import os

# Determine environment
ENV = os.environ.get("ENVIRONMENT", "dev")

# Common configuration across environments
REGION = os.environ.get("AWS_REGION", "us-east-1")
USERNAME_SUFFIX = "nelmak"

# Stack configuration
STACK_PREFIX = "BillQuestMiscommitStack"

# DynamoDB Tables
DYNAMODB_TABLES = {
    "billing_data": "edp_miscommit",
    "user_info": "edp_miscommit_user_info_table",
}

# S3 Buckets
S3_BUCKETS = {
    "raw_files": f"billquestmiscommitstack-rawfilesbucket-{USERNAME_SUFFIX}",
    "website": f"billquestmiscommitstack-websitebucket-{USERNAME_SUFFIX}",
    "user_access": f"billquestmiscommitstack-user-access-bucket-{USERNAME_SUFFIX}",
}

# API Gateway configuration
API_GATEWAY = {
    "main_api_name": f"BillQuestAPIGateway{USERNAME_SUFFIX}",
    "user_access_api_name": f"BillQuestAPIGatewayUserAccess{USERNAME_SUFFIX}",
    "cors_origins": ["http://localhost:5173"]
    if ENV == "dev"
    else ["https://your-production-domain.com"],
    "cors_methods": ["GET", "OPTIONS"],
    "cors_headers": [
        "Content-Type",
        "X-Amz-Date",
        "Authorization",
        "X-Api-Key",
        "X-Amz-Security-Token",
    ],
}

# Lambda configuration
LAMBDA_CONFIG = {
    "runtime": "python3.10",
    "timeout_seconds": 60,
    "user_accounts_timeout": 30,
}

# Cognito configuration
COGNITO_CONFIG = {
    "refresh_token_validity_days": 30,
    "access_token_validity_minutes": 60,
    "id_token_validity_minutes": 60,
}

# Environment-specific overrides
if ENV == "prod":
    # Production-specific settings
    REMOVAL_POLICY = "RETAIN"
    CORS_ALLOW_ALL_ORIGINS = False
else:
    # Development-specific settings
    REMOVAL_POLICY = "DESTROY"
    CORS_ALLOW_ALL_ORIGINS = True
