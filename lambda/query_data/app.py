# lambda/query_data/app.py
import json
import os
import boto3
import logging
from boto3.dynamodb.conditions import Key, Attr

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Initialize DynamoDB client
dynamodb_client = boto3.resource('dynamodb')
table_name = os.environ.get('TABLE_NAME')
table = dynamodb_client.Table(table_name)

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event, indent=2)}")

    try:
        query_params = event.get('queryStringParameters', {}) or {}
        query_type = query_params.get('queryType', 'account')
        
        # Different query types
        if query_type == 'account':
            return query_by_account(query_params)
        elif query_type == 'date':
            return query_by_date(query_params)
        elif query_type == 'invoice':
            return query_by_invoice(query_params)
        else:
            return {
                'statusCode': 400,
                'headers': {"Content-Type": "application/json"},
                'body': json.dumps({"message": f"Invalid query type: {query_type}"})
            }

    except Exception as e:
        logger.error(f"Error querying data: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {"Content-Type": "application/json"},
            'body': json.dumps({"message": f"Error: {str(e)}"})
        }

def query_by_account(params):
    account_id = params.get('accountId')
    if not account_id:
        return {
            'statusCode': 400,
            'headers': {"Content-Type": "application/json"},
            'body': json.dumps({"message": "Missing 'accountId' parameter"})
        }
    
    response = table.query(
        KeyConditionExpression=Key('payer_account_id').eq(account_id)
    )
    
    return {
        'statusCode': 200,
        'headers': {"Content-Type": "application/json"},
        'body': json.dumps({"items": response.get('Items', [])})
    }

def query_by_date(params):
    date = params.get('date')
    product = params.get('product')
    
    if not date:
        return {
            'statusCode': 400,
            'headers': {"Content-Type": "application/json"},
            'body': json.dumps({"message": "Missing 'date' parameter"})
        }
    
    key_condition = Key('bill_period_start_date').eq(date)
    if product:
        key_condition = key_condition & Key('product_code').eq(product)
    
    response = table.query(
        IndexName='DateProductIndex',
        KeyConditionExpression=key_condition
    )
    
    return {
        'statusCode': 200,
        'headers': {"Content-Type": "application/json"},
        'body': json.dumps({"items": response.get('Items', [])})
    }

def query_by_invoice(params):
    invoice_id = params.get('invoiceId')
    
    if not invoice_id:
        return {
            'statusCode': 400,
            'headers': {"Content-Type": "application/json"},
            'body': json.dumps({"message": "Missing 'invoiceId' parameter"})
        }
    
    response = table.query(
        IndexName='InvoiceIndex',
        KeyConditionExpression=Key('invoice_id').eq(invoice_id)
    )
    
    return {
        'statusCode': 200,
        'headers': {"Content-Type": "application/json"},
        'body': json.dumps({"items": response.get('Items', [])})
    }
