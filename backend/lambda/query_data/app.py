# lambda/query_data/app.py
import json
import logging
import os
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Initialize DynamoDB client
dynamodb_client = boto3.resource("dynamodb")
table_name = os.environ.get("TABLE_NAME")
table = dynamodb_client.Table(table_name)


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            # Convert Decimal objects to float for JSON serialization.
            # You could also use str(obj) if you need exact string representation
            # and want to avoid potential floating-point inaccuracies.
            return float(obj)
        return json.JSONEncoder.default(self, obj)


def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event, indent=2)}")

    # Define common headers for CORS
    cors_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "http://localhost:5173",  # Allow your frontend origin
        "Access-Control-Allow-Methods": "GET,OPTIONS",  # Allow GET and OPTIONS methods
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",  # Allow specified headers
    }

    try:
        query_params = event.get("queryStringParameters", {}) or {}
        query_type = query_params.get("queryType", "account")

        # Different query types
        if query_type == "account":
            response = query_by_account(query_params)
        elif query_type == "date":
            response = query_by_date(query_params)
        elif query_type == "invoice":
            response = query_by_invoice(query_params)
        else:
            response = {
                "statusCode": 400,
                "body": json.dumps({"message": f"Invalid query type: {query_type}"}),
            }

        # Merge CORS headers into the response headers for all successful paths
        response["headers"] = {**response.get("headers", {}), **cors_headers}
        return response

    except Exception as e:
        logger.error(f"Error querying data: {str(e)}")
        # For error responses, also include CORS headers
        return {
            "statusCode": 500,
            "headers": cors_headers,  # Apply CORS headers to error response
            "body": json.dumps({"message": f"Error: {str(e)}"}),
        }


def query_by_account(params):
    account_id = params.get("accountId")
    if not account_id:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Missing 'accountId' parameter"}),
        }

    response = table.query(
        KeyConditionExpression=Key("payer_account_id").eq(account_id)
    )

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(
            {"items": response.get("Items", [])}, cls=DecimalEncoder
        ),  # Added DecimalEncoder
    }


def query_by_date(params):
    date = params.get("date")
    product = params.get("product")

    if not date:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Missing 'date' parameter"}),
        }

    key_condition = Key("bill_period_start_date").eq(date)
    if product:
        key_condition = key_condition & Key("product_code").eq(product)

    response = table.query(
        IndexName="DateProductIndex", KeyConditionExpression=key_condition
    )

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(
            {"items": response.get("Items", [])}, cls=DecimalEncoder
        ),  # Added DecimalEncoder
    }


def query_by_invoice(params):
    invoice_id = params.get("invoiceId")

    if not invoice_id:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Missing 'invoiceId' parameter"}),
        }

    response = table.query(
        IndexName="InvoiceIndex",
        KeyConditionExpression=Key("invoice_id").eq(invoice_id),
    )

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(
            {"items": response.get("Items", [])}, cls=DecimalEncoder
        ),  # Added DecimalEncoder
    }
