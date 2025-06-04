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


def lambda_handler(event, context):
    """
    Lambda function that retrieves payer_account_ids associated with an email
    from the DynamoDB table.
    """
    logger.info(f"Received event: {json.dumps(event)}")

    # Define common headers for CORS
    cors_headers = {
        "Access-Control-Allow-Origin": "http://localhost:5173",  # Allow your frontend origin
        "Access-Control-Allow-Methods": "GET,OPTIONS",  # Allow GET and OPTIONS methods
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
    }

    # Handle OPTIONS request (preflight)
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": cors_headers, "body": ""}

    try:
        # Get email from query parameters
        query_params = event.get("queryStringParameters", {}) or {}
        email = query_params.get("email")

        if not email:
            return {
                "statusCode": 400,
                "headers": {**{"Content-Type": "application/json"}, **cors_headers},
                "body": json.dumps({"message": "Missing 'email' parameter"}),
            }

        logger.info(f"Querying for email: {email}")

        # Query DynamoDB for the email
        response = table.get_item(Key={"email": email})

        # Check if the item exists
        if "Item" not in response:
            return {
                "statusCode": 404,
                "headers": {**{"Content-Type": "application/json"}, **cors_headers},
                "body": json.dumps(
                    {"message": f"No accounts found for email: {email}"}
                ),
            }

        # Extract payer_account_ids from the item
        item = response["Item"]
        payer_account_ids = item.get("payer_account_ids", [])

        logger.info(f"Found account IDs for {email}: {payer_account_ids}")

        return {
            "statusCode": 200,
            "headers": {**{"Content-Type": "application/json"}, **cors_headers},
            "body": json.dumps(
                {"email": email, "payer_account_ids": payer_account_ids}
            ),
        }

    except ClientError as e:
        logger.error(f"DynamoDB error: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {**{"Content-Type": "application/json"}, **cors_headers},
            "body": json.dumps({"message": f"Database error: {str(e)}"}),
        }
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {**{"Content-Type": "application/json"}, **cors_headers},
            "body": json.dumps({"message": f"Error: {str(e)}"}),
        }
