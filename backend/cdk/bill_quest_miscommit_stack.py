from aws_cdk import (
    CfnOutput,  # For printing outputs after deployment
    Duration,  # For lambda timeouts
    RemovalPolicy,  # For making resources easier to clean up in dev
    Stack,
    aws_apigateway as apigw,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_cognito as cognito,  # For user authentication
    aws_dynamodb as dynamodb,
    aws_lambda as lambda_,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_s3_notifications as s3n,
)
from constructs import Construct

# Import centralized configuration
from backend.config.config import (
    STACK_PREFIX,
    DYNAMODB_TABLES,
    S3_BUCKETS,
    API_GATEWAY,
    LAMBDA_CONFIG,
    COGNITO_CONFIG,
    REMOVAL_POLICY,
    CORS_ALLOW_ALL_ORIGINS,
)


# <<< NOTE: This class name MUST match your project's stack name
class BillQuestMiscommitStack(Stack):
    """CDK Stack for the BillQuest Miscommit application.

    This stack defines and provisions all the necessary AWS resources
    for the BillQuest application, including backend services (DynamoDB, S3,
    Lambda, API Gateway) and frontend hosting (S3, CloudFront).

    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        """Initialize the BillQuestMiscommitStack.

        Parameters
        ----------
        scope : Construct
            The scope in which to define this construct.
        construct_id : str
            The unique ID for this construct within the scope.
        **kwargs
            Additional keyword arguments passed to the parent `Stack` class.
            Typically includes `env` for defining AWS environment (account, region).

        """
        super().__init__(scope, construct_id, **kwargs)

        stack_prefix = STACK_PREFIX

        billing_data_table = dynamodb.Table(
            self,
            "BillingDataTable",
            table_name=DYNAMODB_TABLES["billing_data"],  # Set the specific table name
            partition_key=dynamodb.Attribute(
                name="payer_account_id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="invoice_id#product_code", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
            if REMOVAL_POLICY == "DESTROY"
            else RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
        )

        # Add GSI for efficient date-based queries
        billing_data_table.add_global_secondary_index(
            index_name="DateProductIndex",
            partition_key=dynamodb.Attribute(
                name="bill_period_start_date", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="product_code", type=dynamodb.AttributeType.STRING
            ),
        )

        # Add GSI for efficient invoice-based queries
        billing_data_table.add_global_secondary_index(
            index_name="InvoiceIndex",
            partition_key=dynamodb.Attribute(
                name="invoice_id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="product_code", type=dynamodb.AttributeType.STRING
            ),
        )

        # --- 2. S3 Bucket for Raw File Uploads ---
        # Users will upload their raw files here.
        raw_files_bucket = s3.Bucket(
            self,
            "RawFilesBucket",
            bucket_name=S3_BUCKETS["raw_files"],
            # Highly recommended for security
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            auto_delete_objects=False,
        )

        # --- 3. Lambda fx for S3 Ingestion (Reads from S3, writes to DynamoDB) ---
        # This function is triggered when new file is uploaded to rawfilesbucket.
        ingest_lambda = lambda_.Function(
            self,
            "IngestDataLambda",
            function_name=f"{stack_prefix}-IngestDataLambda-{S3_BUCKETS['raw_files'].split('-')[-1]}",
            runtime=lambda_.Runtime.PYTHON_3_10,
            # Point to 'app' and 'lambda_handler' function within the lambda directory
            handler="app.lambda_handler",
            code=lambda_.Code.from_asset(
                # Path to your Lambda code directory, relative to your CDK app root
                "./backend/lambda/ingest_data"
            ),
            timeout=Duration.seconds(
                # Max execution time for the Lambda.
                LAMBDA_CONFIG["timeout_seconds"]
            ),
            environment={  # Environment variables for the Lambda function
                "TABLE_NAME": billing_data_table.table_name  # Pass DynamoDB table name
            },
        )

        # Grant the Ingest Lambda necessary permissions with least privilege
        # Only grant specific S3 permissions needed: GetObject for reading files and PutObjectAcl/PutObject for marking as processed
        raw_files_bucket.grant(
            ingest_lambda,
            "s3:GetObject",
            "s3:PutObjectAcl",
            "s3:PutObject",
            "s3:CopyObject",  # Needed for updating object metadata
        )

        # Only grant specific DynamoDB permissions needed: PutItem for writing data
        billing_data_table.grant(
            ingest_lambda,
            "dynamodb:PutItem",
            "dynamodb:BatchWriteItem",  # For batch operations
        )

        # --- 4. S3 Event Notification to trigger Ingest Lambda ---
        # Configures the S3 bucket to invoke the Lambda when new objects are created.
        raw_files_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,  # Trigger on object creation events
            s3n.LambdaDestination(ingest_lambda),  # The Lambda function to invoke
            # Optional: Add filters if you only want to process specific files
            # s3.NotificationKeyFilter(prefix="raw_data/", suffix=".csv")
        )

        # --- 5. Lambda Function for API Gateway (Queries DynamoDB) ---
        # This function will be invoked by API Gateway to serve data to the frontend.
        query_lambda = lambda_.Function(
            self,
            "QueryDataLambda",
            function_name=f"{stack_prefix}-QueryDataLambda-{S3_BUCKETS['raw_files'].split('-')[-1]}",
            runtime=lambda_.Runtime.PYTHON_3_10,
            handler="app.lambda_handler",
            code=lambda_.Code.from_asset("./backend/lambda/query_data"),
            # Max execution time. Adjust as needed.
            timeout=Duration.seconds(LAMBDA_CONFIG["timeout_seconds"]),
            environment={"TABLE_NAME": billing_data_table.table_name},
        )

        # Grant the Query Lambda necessary permissions with least privilege
        # Only grant specific DynamoDB permissions needed: Query for reading data with filters
        billing_data_table.grant(query_lambda, "dynamodb:Query")

        # --- 6. API Gateway for Frontend Access ---
        # Creates a REST API endpoint that your frontend will interact with.
        api = apigw.RestApi(
            self,
            "BillQuestApi",
            rest_api_name=API_GATEWAY["main_api_name"],
            description="API for BillQuest frontend to query data.",
            # Enable CORS (Cross-Origin Resource Sharing) for your frontend
            # This is crucial for your browser-based frontend to call your API.
            default_cors_preflight_options=apigw.CorsOptions(
                #! CAUTION: ALL_ORIGINS means any website can call your API. Be specific in production!
                allow_origins=apigw.Cors.ALL_ORIGINS
                if CORS_ALLOW_ALL_ORIGINS
                else API_GATEWAY["cors_origins"],
                allow_methods=API_GATEWAY["cors_methods"],
                allow_headers=API_GATEWAY["cors_headers"],
            ),
        )

        # Add a '/query' resource and integrate it with the Query Lambda
        query_resource = api.root.add_resource("query")
        query_resource.add_method(
            "GET",  # Frontend will typically send GET requests for querying
            apigw.LambdaIntegration(
                query_lambda
            ),  # Connects the API Gateway method to your Lambda function
            # Set to True for production to control access with API Keys
            api_key_required=False,
        )

        # --- Frontend Hosting Resources (Revised for Secure CloudFront with S3) ---

        # 7. S3 Bucket for Vite Frontend Static Files
        # This bucket will store your built Vite application (HTML, CSS, JS).
        # IMPORTANT: This bucket should NOT be publicly accessible directly.
        # CloudFront will be granted specific access via an Origin Access Identity (OAI).
        website_bucket = s3.Bucket(
            self,
            "WebsiteBucket",
            bucket_name=S3_BUCKETS["website"],
            # Ensure public access is blocked. CloudFront will get specific access.
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        )

        # 8. CloudFront Distribution (Content Delivery Network - CDN)
        # This serves your static frontend files securely from the private S3 bucket.
        distribution = cloudfront.Distribution(
            self,
            "WebsiteDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin(website_bucket),
                # Forces HTTPS
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            ),
            # CloudFront will serve index.html for root requests
            default_root_object="index.html",
        )

        # 9. S3 Deployment for the Vite Frontend
        # This will automatically upload your 'frontend/dist' folder content to the S3 website bucket
        s3deploy.BucketDeployment(
            self,
            "DeployWebsite",
            sources=[
                s3deploy.Source.asset("./frontend/dist")
            ],  # Source directory for your built frontend
            destination_bucket=website_bucket,
            # Triggers CloudFront cache invalidation after deployment
            distribution=distribution,
            # Invalidate all paths to ensure fresh content
            distribution_paths=["/*"],
        )

        # --- 10. AWS Cognito User Pool ---
        # Create a user pool for authentication
        user_pool = cognito.UserPool(
            self,
            "BillQuestUserPoolMiscommit",
            user_pool_name=f"{stack_prefix}-UserPool",
            # Self sign-up allows users to register themselves
            self_sign_up_enabled=True,
            # Configure sign-in options (email is primary)
            sign_in_aliases=cognito.SignInAliases(
                email=True,
                username=True,
            ),
            # Configure password policy
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True,
            ),
            # Configure email verification
            auto_verify={"email": True},
            # Standard attributes required from users
            standard_attributes={
                "email": {"required": True, "mutable": True},
                "fullname": {"required": False, "mutable": True},
            },
            # Removal policy for development (use RETAIN for production)
            removal_policy=RemovalPolicy.DESTROY
            if REMOVAL_POLICY == "DESTROY"
            else RemovalPolicy.RETAIN,
        )

        # --- 11. Cognito User Pool Client ---
        # This client will be used by your frontend application
        user_pool_client = cognito.UserPoolClient(
            self,
            "BillQuestMiscommitWebClient",
            user_pool=user_pool,
            user_pool_client_name=f"{stack_prefix}-WebClient",
            # Generate a client secret (set to False if using a public client like a SPA)
            generate_secret=False,
            # Configure OAuth flows
            auth_flows={
                "user_password": True,
                "user_srp": True,
            },
            # Configure OAuth scopes
            o_auth={
                "flows": {
                    "implicit_code_grant": True,
                },
                "scopes": [
                    cognito.OAuthScope.EMAIL,
                    cognito.OAuthScope.OPENID,
                    cognito.OAuthScope.PROFILE,
                ],
                "callback_urls": [
                    f"https://{distribution.distribution_domain_name}/callback",
                    "http://localhost:5173/callback",  # For local development
                ],
                "logout_urls": [
                    f"https://{distribution.distribution_domain_name}",
                    "http://localhost:5173",  # For local development
                ],
            },
            # Prevent users from being automatically logged out
            refresh_token_validity=Duration.days(
                COGNITO_CONFIG["refresh_token_validity_days"]
            ),
            access_token_validity=Duration.minutes(
                COGNITO_CONFIG["access_token_validity_minutes"]
            ),
            id_token_validity=Duration.minutes(
                COGNITO_CONFIG["id_token_validity_minutes"]
            ),
        )

        # --- 12. Cognito Authorizer for API Gateway ---
        # Create an authorizer that uses the Cognito User Pool
        auth = apigw.CognitoUserPoolsAuthorizer(
            self,
            "BillQuestAuthorizer",
            cognito_user_pools=[user_pool],
        )

        # Add a protected resource that requires authentication
        protected_resource = api.root.add_resource("protected")
        protected_resource.add_method(
            "GET",
            apigw.LambdaIntegration(query_lambda),
            # Require authorization for this endpoint
            authorizer=auth,
            authorization_type=apigw.AuthorizationType.COGNITO,
        )

        # --- Outputs ---
        # These outputs will be displayed in your terminal after 'cdk deploy'
        # You'll use these URLs for your frontend configuration and testing.
        CfnOutput(
            self,
            "ApiGatewayEndpoint",
            value=api.url,
            description="The API Gateway endpoint for querying data.",
        )
        CfnOutput(
            self,
            "WebsiteUrl",
            value=f"https://{distribution.distribution_domain_name}",
            description="The URL for your static website hosted on CloudFront.",
        )

        # Cognito outputs for frontend configuration
        CfnOutput(
            self,
            "UserPoolId",
            value=user_pool.user_pool_id,
            description="The ID of the Cognito User Pool.",
        )
        CfnOutput(
            self,
            "UserPoolClientId",
            value=user_pool_client.user_pool_client_id,
            description="The ID of the Cognito User Pool Client.",
        )
        CfnOutput(
            self,
            "UserPoolDomain",
            value=f"{user_pool.user_pool_id}.auth.{Stack.of(self).region}.amazoncognito.com",
            description="The domain for the Cognito hosted UI.",
        )

        # --- 13. User Info DynamoDB Table ---
        # This table will store user information including email and payer_account_ids (list)
        user_info_table = dynamodb.Table(
            self,
            "UserInfoTable",
            table_name=DYNAMODB_TABLES["user_info"],
            partition_key=dynamodb.Attribute(
                name="email", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
            if REMOVAL_POLICY == "DESTROY"
            else RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
        )

        # --- 14. S3 Bucket for User Info CSV Uploads ---
        # Users will upload their user info CSV files here
        user_info_bucket = s3.Bucket(
            self,
            "UserInfoBucket",
            bucket_name=S3_BUCKETS["user_access"],
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            auto_delete_objects=False,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # --- 15. Lambda Function for Processing User Info CSV ---
        # This function is triggered when a new file is uploaded to the user info bucket
        update_user_info_lambda = lambda_.Function(
            self,
            "UpdateUserInfoLambda",
            function_name=f"{stack_prefix}-UpdateUserInfoLambda-{S3_BUCKETS['raw_files'].split('-')[-1]}",
            runtime=lambda_.Runtime.PYTHON_3_10,
            handler="app.lambda_handler",
            code=lambda_.Code.from_asset("./backend/lambda/update_user_info"),
            timeout=Duration.seconds(LAMBDA_CONFIG["timeout_seconds"]),
            environment={"TABLE_NAME": user_info_table.table_name},
        )

        # Grant the Lambda necessary permissions with least privilege
        # Only grant specific S3 permissions needed: GetObject for reading uploaded files
        user_info_bucket.grant(update_user_info_lambda, "s3:GetObject")

        # Only grant specific DynamoDB permissions needed: PutItem for updating user info
        user_info_table.grant(update_user_info_lambda, "dynamodb:PutItem")

        # --- 16. S3 Event Notification to trigger Update User Info Lambda ---
        # Configures the S3 bucket to invoke the Lambda when new objects are created
        user_info_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(update_user_info_lambda),
        )

        # --- 17. Lambda Function for Getting User Accounts ---
        # This function retrieves payer_account_ids associated with an email
        get_user_accounts_lambda = lambda_.Function(
            self,
            "GetUserAccountsLambda",
            function_name=f"{stack_prefix}-GetUserAccountsLambda-{S3_BUCKETS['raw_files'].split('-')[-1]}",
            runtime=lambda_.Runtime.PYTHON_3_10,
            handler="app.lambda_handler",
            code=lambda_.Code.from_asset("./backend/lambda/get_user_accounts"),
            timeout=Duration.seconds(LAMBDA_CONFIG["user_accounts_timeout"]),
            environment={"TABLE_NAME": user_info_table.table_name},
        )

        # Grant the Lambda necessary permissions with least privilege
        # Only grant specific DynamoDB permissions needed: GetItem for retrieving user accounts
        user_info_table.grant(get_user_accounts_lambda, "dynamodb:GetItem")

        # --- 18. API Gateway for User Access ---
        # Creates a REST API endpoint for user account access
        user_access_api = apigw.RestApi(
            self,
            "BillQuestUserAccessApi",
            rest_api_name=API_GATEWAY["user_access_api_name"],
            description="API for retrieving user account information",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS
                if CORS_ALLOW_ALL_ORIGINS
                else API_GATEWAY["cors_origins"],
                allow_methods=API_GATEWAY["cors_methods"],
                allow_headers=API_GATEWAY["cors_headers"],
            ),
        )

        # Create an authorizer for the user access API using the same Cognito User Pool
        user_access_auth = apigw.CognitoUserPoolsAuthorizer(
            self,
            "UserAccessAuthorizer",
            cognito_user_pools=[user_pool],
        )

        # Add a '/user-accounts' resource and integrate it with the Get User Accounts Lambda
        user_accounts_resource = user_access_api.root.add_resource("user-accounts")
        user_accounts_resource.add_method(
            "GET",
            apigw.LambdaIntegration(get_user_accounts_lambda),
            authorizer=user_access_auth,
            authorization_type=apigw.AuthorizationType.COGNITO,
        )

        # Add outputs for the new resources
        CfnOutput(
            self,
            "UserInfoBucketName",
            value=user_info_bucket.bucket_name,
            description="The S3 bucket for user info CSV uploads.",
        )
        CfnOutput(
            self,
            "UserInfoTableName",
            value=user_info_table.table_name,
            description="The DynamoDB table for user information.",
        )

        # Add output for the User Access API endpoint
        CfnOutput(
            self,
            "UserAccessApiEndpoint",
            value=f"{user_access_api.url}user-accounts",
            description="The API endpoint for retrieving user account information.",
        )
