import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Initialize DynamoDB client
dynamodb_client = boto3.resource("dynamodb")
table_name = os.environ.get("TABLE_NAME")
table = dynamodb_client.Table(table_name)


def get_cors_headers():
    """Return CORS headers for API responses.

    Returns:
        dict: Dictionary containing CORS headers allowing cross-origin requests

    """
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Credentials": "true",
    }


def format_response(status_code, body):
    """Format a standardized API Gateway response with CORS headers.

    Args:
        status_code (int): HTTP status code
        body (dict): Response body to be JSON serialized

    Returns:
        dict: Formatted API Gateway response

    """
    return {
        "statusCode": status_code,
        "headers": get_cors_headers(),
        "body": json.dumps(body),
    }


def lambda_handler(event, context):
    """Lambda function that retrieves payer_account_ids associated with an email
    from the DynamoDB table.

    This function:
    1. Extracts the email from query parameters
    2. Queries the DynamoDB table for the email
    3. Returns the associated payer_account_ids if found

    Args:
        event (dict): API Gateway event containing request data
        context (object): Lambda context object

    Returns:
        dict: API Gateway response with status code, headers, and body

    """
    # Log the incoming event
    logger.info(f"Received event: {json.dumps(event)}")

    # Handle OPTIONS request (preflight)
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": get_cors_headers(), "body": ""}

    try:
        # Get email from query parameters
        query_params = event.get("queryStringParameters", {}) or {}
        email = query_params.get("email")

        if not email:
            return format_response(400, {"message": "Missing 'email' parameter"})

        logger.info(f"Querying for email: {email}")

        # Query DynamoDB for the email
        response = table.get_item(Key={"email": email})

        # Check if the item exists
        if "Item" not in response:
            return format_response(
                404, {"message": f"No accounts found for email: {email}"}
            )

        # Extract payer_account_ids from the item
        item = response["Item"]
        payer_account_ids = item.get("payer_account_ids", [])

        logger.info(f"Found account IDs for {email}: {payer_account_ids}")

        # Return successful response
        return format_response(
            200, {"email": email, "payer_account_ids": payer_account_ids}
        )

    except ClientError as e:
        # Handle AWS service errors
        logger.error(f"DynamoDB error: {str(e)}")
        return format_response(500, {"message": f"Database error: {str(e)}"})
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Error processing request: {str(e)}")
        return format_response(500, {"message": f"Error: {str(e)}"})
