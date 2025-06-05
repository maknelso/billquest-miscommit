import json
import logging
import os
import boto3
from botocore.exceptions import ClientError

# Import shared utilities
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.error_handler import handle_error, ValidationError, ResourceNotFoundError
from utils.response_formatter import format_success_response
from utils.logging_utils import log_event, log_lambda_execution
from utils.cors_config import get_cors_headers

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Initialize DynamoDB client
dynamodb_client = boto3.resource("dynamodb")
table_name = os.environ.get("TABLE_NAME")
table = dynamodb_client.Table(table_name)


@log_lambda_execution
def lambda_handler(event, context):
    """
    Lambda function that retrieves payer_account_ids associated with an email
    from the DynamoDB table.
    """
    # Log the incoming event
    log_event(event, context)

    # Handle OPTIONS request (preflight)
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": get_cors_headers(), "body": ""}

    try:
        # Get email from query parameters
        query_params = event.get("queryStringParameters", {}) or {}
        email = query_params.get("email")

        if not email:
            raise ValidationError("Missing 'email' parameter")

        logger.info(f"Querying for email: {email}")

        # Query DynamoDB for the email
        response = table.get_item(Key={"email": email})

        # Check if the item exists
        if "Item" not in response:
            raise ResourceNotFoundError(
                f"No accounts found for email: {email}", {"email": email}
            )

        # Extract payer_account_ids from the item
        item = response["Item"]
        payer_account_ids = item.get("payer_account_ids", [])

        logger.info(f"Found account IDs for {email}: {payer_account_ids}")

        # Return successful response
        return format_success_response(
            {"email": email, "payer_account_ids": payer_account_ids}
        )

    except (ValidationError, ResourceNotFoundError) as e:
        # Handle known error types
        return handle_error(
            e,
            {
                "aws_request_id": context.aws_request_id,
                "email": email if "email" in locals() else None,
                "function_name": context.function_name,
            },
        )
    except ClientError as e:
        # Handle AWS service errors
        logger.error(f"DynamoDB error: {str(e)}")
        return handle_error(
            e,
            {
                "aws_request_id": context.aws_request_id,
                "service": "DynamoDB",
                "email": email if "email" in locals() else None,
            },
        )
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Error processing request: {str(e)}")
        return handle_error(
            e, {"aws_request_id": context.aws_request_id, "event": event}
        )
