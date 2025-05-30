# lambda/query_data/app.py
import json
import logging
import os
import csv
import base64
from decimal import Decimal
import io

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
            return float(obj)
        return json.JSONEncoder.default(self, obj)


def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event, indent=2)}")

    # Define common headers for CORS
    cors_headers = {
        "Access-Control-Allow-Origin": "http://localhost:5173",  # Allow your frontend origin
        "Access-Control-Allow-Methods": "GET,OPTIONS",  # Allow GET and OPTIONS methods
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",  # Allow specified headers
    }

    try:
        query_params = event.get("queryStringParameters", {}) or {}
        query_type = query_params.get("queryType", "account")
        format_type = query_params.get(
            "format", "json"
        )  # Default to JSON if not specified

        # Different query types
        if query_type == "account":
            items = query_by_account_items(query_params)
        elif query_type == "date":
            items = query_by_date_items(query_params)
        elif query_type == "invoice":
            items = query_by_invoice_items(query_params)
        else:
            return {
                "statusCode": 400,
                "headers": {**{"Content-Type": "application/json"}, **cors_headers},
                "body": json.dumps({"message": f"Invalid query type: {query_type}"}),
            }

        # Format response based on requested format
        if format_type.lower() == "csv":
            return format_csv_response(items, cors_headers)
        else:
            return format_json_response(items, cors_headers)

    except Exception as e:
        logger.error(f"Error querying data: {str(e)}")
        # For error responses, also include CORS headers
        return {
            "statusCode": 500,
            "headers": {**{"Content-Type": "application/json"}, **cors_headers},
            "body": json.dumps({"message": f"Error: {str(e)}"}),
        }


def query_by_account_items(params):
    account_id = params.get("accountId")
    if not account_id:
        raise ValueError("Missing 'accountId' parameter")

    response = table.query(
        KeyConditionExpression=Key("payer_account_id").eq(account_id)
    )
    return response.get("Items", [])


def query_by_date_items(params):
    date = params.get("date")
    product = params.get("product")

    if not date:
        raise ValueError("Missing 'date' parameter")

    key_condition = Key("bill_period_start_date").eq(date)
    if product:
        key_condition = key_condition & Key("product_code").eq(product)

    response = table.query(
        IndexName="DateProductIndex", KeyConditionExpression=key_condition
    )
    return response.get("Items", [])


def query_by_invoice_items(params):
    invoice_id = params.get("invoiceId")

    if not invoice_id:
        raise ValueError("Missing 'invoiceId' parameter")

    response = table.query(
        IndexName="InvoiceIndex",
        KeyConditionExpression=Key("invoice_id").eq(invoice_id),
    )
    return response.get("Items", [])


def format_json_response(items, cors_headers):
    return {
        "statusCode": 200,
        "headers": {**{"Content-Type": "application/json"}, **cors_headers},
        "body": json.dumps({"items": items}, cls=DecimalEncoder),
    }


def format_csv_response(items, cors_headers):
    if not items:
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "text/csv",
                "Content-Disposition": "attachment; filename=billing_data.csv",
                **cors_headers,
            },
            "body": "",
        }

    # Create CSV in memory
    output = io.StringIO()

    # Get all unique keys from all items to ensure we include all possible columns
    all_keys = set()
    for item in items:
        all_keys.update(item.keys())

    # Sort keys for consistent column order
    fieldnames = sorted(list(all_keys))

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    # Convert Decimal to float for CSV compatibility
    for item in items:
        row = {}
        for key in fieldnames:
            value = item.get(key, "")
            if isinstance(value, Decimal):
                row[key] = float(value)
            else:
                row[key] = value
        writer.writerow(row)

    csv_content = output.getvalue()

    # API Gateway binary content handling
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/csv",
            "Content-Disposition": "attachment; filename=billing_data.csv",
            **cors_headers,
        },
        "body": csv_content,
        "isBase64Encoded": False,  # Changed to False since we're returning plain text
    }
