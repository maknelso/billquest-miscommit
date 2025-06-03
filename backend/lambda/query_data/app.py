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
    
    # Print environment variables and table name for debugging
    logger.info(f"Environment variables: {os.environ}")
    logger.info(f"Using table name: {table_name}")
    
    # Check if table exists and is accessible
    try:
        table_info = dynamodb_client.meta.client.describe_table(TableName=table_name)
        logger.info(f"Table exists with {table_info['Table']['ItemCount']} items")
    except Exception as e:
        logger.error(f"Error accessing table: {str(e)}")

    # Define common headers for CORS
    cors_headers = {
        "Access-Control-Allow-Origin": "*",  # Allow any origin for testing
        "Access-Control-Allow-Methods": "GET,OPTIONS",  # Allow GET and OPTIONS methods
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",  # Allow specified headers
    }

    try:
        query_params = event.get("queryStringParameters", {}) or {}
        query_type = query_params.get("queryType", "account")
        format_type = query_params.get(
            "format", "json"
        )  # Default to JSON if not specified
        
        # Add a special scan endpoint for debugging
        if query_type == "scan":
            try:
                limit = int(query_params.get("limit", 10))
                scan_response = table.scan(Limit=limit)
                items = scan_response.get("Items", [])
                logger.info(f"Scan found {len(items)} items")
                
                # Log the first few items for debugging
                if items:
                    logger.info(f"Sample item: {items[0]}")
                    
                    # Extract and log unique payer_account_id values
                    payer_ids = set()
                    for item in items:
                        if "payer_account_id" in item:
                            payer_ids.add(item["payer_account_id"])
                    logger.info(f"Found payer_account_id values: {list(payer_ids)}")
                
                return {
                    "statusCode": 200,
                    "headers": {**{"Content-Type": "application/json"}, **cors_headers},
                    "body": json.dumps({
                        "message": "Scan successful",
                        "count": len(items),
                        "sample": items[:3] if items else [],
                        "payer_account_ids": list(payer_ids) if 'payer_ids' in locals() else []
                    }, cls=DecimalEncoder),
                }
            except Exception as e:
                logger.error(f"Error during scan: {str(e)}")
                return {
                    "statusCode": 500,
                    "headers": {**{"Content-Type": "application/json"}, **cors_headers},
                    "body": json.dumps({"message": f"Error during scan: {str(e)}"}),
                }

        # Different query types
        if query_type == "account":
            items = query_by_account_items(query_params)
        elif query_type == "date":
            items = query_by_date_items(query_params)
        elif query_type == "invoice":
            items = query_by_invoice_items(query_params)
        elif query_type == "getInvoiceIds":
            invoice_ids = get_invoice_ids_for_account(query_params)
            return {
                "statusCode": 200,
                "headers": {**{"Content-Type": "application/json"}, **cors_headers},
                "body": json.dumps({"invoiceIds": invoice_ids}),
            }
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
    
    logger.info(f"Querying for account_id: {account_id}")
    
    # Try direct query first
    response = table.query(
        KeyConditionExpression=Key("payer_account_id").eq(account_id)
    )
    items = response.get("Items", [])
    logger.info(f"Direct query found {len(items)} items")
    
    # If no results, try alternative formats
    if not items:
        logger.info("No items found with direct query, trying alternative formats")
        alt_formats = [account_id.lower(), account_id.upper(), account_id.strip()]
        
        for alt_id in alt_formats:
            if alt_id != account_id:
                logger.info(f"Trying alternative format: {alt_id}")
                alt_response = table.query(
                    KeyConditionExpression=Key("payer_account_id").eq(alt_id)
                )
                alt_items = alt_response.get("Items", [])
                if alt_items:
                    logger.info(f"Found {len(alt_items)} items using alternative format: {alt_id}")
                    items = alt_items
                    break
    
    # If still no results, try a scan with filter
    if not items:
        logger.info("No items found with any format, trying a scan with filter")
        scan_response = table.scan(
            FilterExpression="contains(payer_account_id, :account_fragment)",
            ExpressionAttributeValues={
                ":account_fragment": account_id[-6:] if len(account_id) > 6 else account_id
            },
            Limit=20
        )
        scan_items = scan_response.get("Items", [])
        if scan_items:
            logger.info(f"Scan found {len(scan_items)} items with account fragment")
            items = scan_items
    
    return items


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


def get_invoice_ids_for_account(params):
    account_id = params.get("accountId")
    if not account_id:
        raise ValueError("Missing 'accountId' parameter")
    
    logger.info(f"Fetching invoice IDs for account: {account_id}")
    
    try:
        # First, try to query using the account ID directly
        response = table.query(
            KeyConditionExpression=Key("payer_account_id").eq(account_id)
        )
        
        # Extract unique invoice IDs
        items = response.get("Items", [])
        logger.info(f"Found {len(items)} items for account {account_id}")
        
        # If no results, try with a scan to see if data exists at all
        if not items:
            logger.info(f"No items found with direct query. Performing scan to check if table has data.")
            scan_response = table.scan(Limit=10)
            scan_items = scan_response.get("Items", [])
            logger.info(f"Scan found {len(scan_items)} items. Sample item keys: {[list(item.keys()) for item in scan_items[:3]]}")
            
            # If we found items in the scan, let's check what payer_account_id values exist
            if scan_items:
                payer_ids = set()
                for item in scan_items:
                    if "payer_account_id" in item:
                        payer_ids.add(item["payer_account_id"])
                logger.info(f"Found these payer_account_id values in the table: {list(payer_ids)}")
                
                # Try with different case or formatting
                logger.info("Trying alternative formats of account ID")
                alt_formats = [account_id.lower(), account_id.upper(), account_id.strip()]
                for alt_id in alt_formats:
                    if alt_id != account_id:
                        alt_response = table.query(
                            KeyConditionExpression=Key("payer_account_id").eq(alt_id)
                        )
                        alt_items = alt_response.get("Items", [])
                        if alt_items:
                            logger.info(f"Found items using alternative format: {alt_id}")
                            items = alt_items
                            break
        
        invoice_ids = set()
        
        for item in items:
            # Log item keys to debug
            logger.info(f"Item keys: {list(item.keys())}")
            
            # Extract invoice_id from the invoice_id field
            if "invoice_id" in item:
                invoice_ids.add(item["invoice_id"])
                logger.info(f"Found invoice_id: {item['invoice_id']}")
            # Also check composite key if present
            elif "invoice_id#product_code" in item:
                composite_key = item.get("invoice_id#product_code", "")
                if "#" in composite_key:
                    invoice_id = composite_key.split("#")[0]
                    invoice_ids.add(invoice_id)
                    logger.info(f"Extracted invoice_id {invoice_id} from composite key {composite_key}")
        
        # If no invoice IDs found, return empty list
        if not invoice_ids:
            logger.info("No invoice IDs found for account")
            return []
            
        result = sorted(list(invoice_ids))
        logger.info(f"Returning {len(result)} unique invoice IDs: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in get_invoice_ids_for_account: {str(e)}")
        # Return empty list in case of error
        return []


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