# lambda/query_data/app.py
import json
import logging
import os
import csv
import io
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key, Attr

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Initialize DynamoDB client
dynamodb_client = boto3.resource("dynamodb")
table_name = os.environ.get("TABLE_NAME")
table = dynamodb_client.Table(table_name)


# Define CORS headers directly
def get_cors_headers():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Credentials": "true",
    }


def format_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": get_cors_headers(),
        "body": json.dumps(body, cls=DecimalEncoder),
    }


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)


def lambda_handler(event, context):
    # Log the incoming event
    logger.info(f"Received event: {json.dumps(event)}")

    # Handle OPTIONS request (preflight)
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": get_cors_headers(), "body": ""}

    try:
        query_params = event.get("queryStringParameters", {}) or {}
        query_type = query_params.get("queryType", "account")
        format_type = query_params.get(
            "format", "json"
        )  # Default to JSON if not specified

        # Validate query type
        if query_type not in ["account", "date", "invoice"]:
            return format_response(
                400,
                {
                    "message": f"Invalid query type: {query_type}",
                    "valid_types": ["account", "date", "invoice"],
                },
            )

        # Different query types
        if query_type == "account":
            items = query_by_account_items(query_params)
        elif query_type == "date":
            items = query_by_date_items(query_params)
        elif query_type == "invoice":
            items = query_by_invoice_items(query_params)

        # Format response based on requested format
        if format_type.lower() == "csv":
            return format_csv_response(items)
        else:
            return format_response(
                200,
                {"items": items, "count": len(items), "summary": summarize_data(items)},
            )

    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Error querying data: {str(e)}")
        return format_response(500, {"message": f"Error: {str(e)}"})


def query_by_account_items(params):
    account_id = params.get("accountId")
    invoice_id = params.get("invoiceId")
    bill_period_start_date = params.get("billPeriodStartDate")

    if not account_id:
        raise ValueError("Missing 'accountId' parameter")

    # Handle multiple account IDs (comma-separated)
    account_ids = [aid.strip() for aid in account_id.split(",")]
    logger.info(f"Processing {len(account_ids)} account IDs: {account_ids}")

    all_items = []

    # Process each account ID
    for aid in account_ids:
        # If invoice ID is provided, use that for more specific filtering
        if invoice_id:
            logger.info(f"Querying by account ID {aid} and invoice ID {invoice_id}")
            response = table.query(
                IndexName="InvoiceIndex",
                KeyConditionExpression=Key("invoice_id").eq(invoice_id),
                FilterExpression=Attr("payer_account_id").eq(aid),
            )
        # If bill period start date is provided, use DateProductIndex
        elif bill_period_start_date:
            logger.info(
                f"Querying by account ID {aid} and bill period {bill_period_start_date}"
            )
            response = table.query(
                IndexName="DateProductIndex",
                KeyConditionExpression=Key("bill_period_start_date").eq(
                    bill_period_start_date
                ),
                FilterExpression=Attr("payer_account_id").eq(aid),
            )
        # Otherwise just query by account ID
        else:
            logger.info(f"Querying by account ID {aid} only")
            response = table.query(
                KeyConditionExpression=Key("payer_account_id").eq(aid)
            )

        # Add items from this account ID to the result
        all_items.extend(response.get("Items", []))

    return all_items


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


def generate_filename(items):
    """Generate a descriptive filename for the CSV download based on the data"""
    if not items:
        return "billing_data.csv"

    # Get unique account IDs
    account_ids = set()
    invoice_ids = set()
    dates = set()

    for item in items:
        if "payer_account_id" in item:
            account_ids.add(item["payer_account_id"])
        if "invoice_id" in item:
            invoice_ids.add(item["invoice_id"])
        if "bill_period_start_date" in item:
            dates.add(item["bill_period_start_date"])

    # Create filename based on available data
    if len(account_ids) == 1:
        account_id = list(account_ids)[0]
        if len(dates) == 1:
            date = list(dates)[0]
            return f"billing_{account_id}_{date}.csv"
        elif len(invoice_ids) == 1:
            invoice_id = list(invoice_ids)[0]
            return f"billing_{account_id}_{invoice_id}.csv"
        else:
            return f"billing_{account_id}.csv"
    else:
        return f"billing_data_multiple_accounts.csv"


def summarize_data(items):
    """Generate a summary of the data for the JSON response"""
    if not items:
        return {}

    # Count unique values
    account_ids = set()
    invoice_ids = set()
    dates = set()
    products = set()

    # Track totals
    total_cost = 0

    for item in items:
        if "payer_account_id" in item:
            account_ids.add(item["payer_account_id"])
        if "invoice_id" in item:
            invoice_ids.add(item["invoice_id"])
        if "bill_period_start_date" in item:
            dates.add(item["bill_period_start_date"])
        if "product_code" in item:
            products.add(item["product_code"])
        if "cost_before_tax" in item and isinstance(
            item["cost_before_tax"], (int, float, Decimal)
        ):
            total_cost += float(item["cost_before_tax"])

    return {
        "unique_accounts": len(account_ids),
        "unique_invoices": len(invoice_ids),
        "unique_dates": len(dates),
        "unique_products": len(products),
        "total_cost": round(total_cost, 2),
    }


def format_csv_response(items):
    if not items:
        # Return empty CSV with CORS headers
        return {
            "statusCode": 200,
            "headers": {
                **get_cors_headers(),
                "Content-Type": "text/csv",
                "Content-Disposition": "attachment; filename=billing_data.csv",
            },
            "body": "",
            "isBase64Encoded": False,
        }

    # Create CSV in memory
    output = io.StringIO()

    # Get all unique keys from all items to ensure we include all possible columns
    all_keys = set()
    for item in items:
        all_keys.update(item.keys())

    # Define important columns to appear first in the CSV
    priority_columns = [
        "payer_account_id",
        "invoice_id",
        "product_code",
        "bill_period_start_date",
        "cost_before_tax",
    ]

    # Sort keys with priority columns first, then alphabetically for the rest
    fieldnames = []
    for col in priority_columns:
        if col in all_keys:
            fieldnames.append(col)
            all_keys.remove(col)

    # Add remaining columns in alphabetical order
    fieldnames.extend(sorted(list(all_keys)))

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

    # Generate a more descriptive filename based on query parameters
    filename = generate_filename(items)

    # Return CSV with CORS headers
    return {
        "statusCode": 200,
        "headers": {
            **get_cors_headers(),
            "Content-Type": "text/csv",
            "Content-Disposition": f"attachment; filename={filename}",
        },
        "body": csv_content,
        "isBase64Encoded": False,
    }
