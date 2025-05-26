from aws_cdk import (
    CfnOutput,  # For printing outputs after deployment
    Duration,  # For lambda timeouts
    RemovalPolicy,  # For making resources easier to clean up in dev
    Stack,
    aws_apigateway as apigw,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_dynamodb as dynamodb,
    aws_lambda as lambda_,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_s3_notifications as s3n,
)
from constructs import Construct


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

        stack_prefix = "BillQuestMiscommitStack"

        billing_data_table = dynamodb.Table(
            self,
            "BillingDataTable",
            table_name="edp_miscommit",  # Set the specific table name
            partition_key=dynamodb.Attribute(
                name="payer_account_id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="invoice_id#product_code", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
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
            bucket_name="billquestmiscommitstack-rawfilesbucket-nelmak",
            # Highly recommended for security
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            auto_delete_objects=False,
        )

        # --- 3. Lambda fx for S3 Ingestion (Reads from S3, writes to DynamoDB) ---
        # This function is triggered when new file is uploaded to rawfilesbucket.
        ingest_lambda = lambda_.Function(
            self,
            "IngestDataLambda",
            function_name=f"{stack_prefix}-IngestDataLambda-nelmak",
            runtime=lambda_.Runtime.PYTHON_3_10,
            # Point to 'app' and 'lambda_handler' function within the lambda directory
            handler="app.lambda_handler",
            code=lambda_.Code.from_asset(
                # Path to your Lambda code directory, relative to your CDK app root
                "./backend/lambda/ingest_data"
            ),
            timeout=Duration.seconds(
                # Max execution time for the Lambda.
                60
            ),
            environment={  # Environment variables for the Lambda function
                "TABLE_NAME": billing_data_table.table_name  # Pass DynamoDB table name
            },
        )

        # Grant the Ingest Lambda necessary permissions
        raw_files_bucket.grant_read_write(
            ingest_lambda
        )  # Allow Lambda to read and write to S3 bucket
        billing_data_table.grant_write_data(
            ingest_lambda
        )  # Allow Lambda to write to the DynamoDB table

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
            function_name=f"{stack_prefix}-QueryDataLambda-nelmak",
            runtime=lambda_.Runtime.PYTHON_3_10,
            handler="app.lambda_handler",
            code=lambda_.Code.from_asset("./backend/lambda/query_data"),
            # Max execution time. Adjust as needed.
            timeout=Duration.seconds(60),
            environment={"TABLE_NAME": billing_data_table.table_name},
        )

        # Grant the Query Lambda necessary permissions
        billing_data_table.grant_read_data(
            query_lambda
        )  # Allow Lambda to read from DynamoDB

        # --- 6. API Gateway for Frontend Access ---
        # Creates a REST API endpoint that your frontend will interact with.
        api = apigw.RestApi(
            self,
            "BillQuestApi",
            rest_api_name="BillQuestAPIGatewaynelmak",
            description="API for BillQuest frontend to query data.",
            # Enable CORS (Cross-Origin Resource Sharing) for your frontend
            # This is crucial for your browser-based frontend to call your API.
            default_cors_preflight_options=apigw.CorsOptions(
                #! CAUTION: ALL_ORIGINS means any website can call your API. Be specific in production!
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=["GET"],
                allow_headers=[
                    "Content-Type",
                    "X-Amz-Date",
                    "Authorization",
                    "X-Api-Key",
                    "X-Amz-Security-Token",
                ],
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
            bucket_name="billquestmiscommitstack-websitebucket-nelmak",
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
