# Ingest Data Lambda

This Lambda function processes CSV files uploaded to the raw files S3 bucket and stores the data in DynamoDB.

## Function Details

- **Handler**: `app.lambda_handler`
- **Runtime**: Python 3.10
- **Timeout**: 60 seconds
- **Memory**: Default (128 MB)

## Trigger

This function is triggered by S3 object creation events in the raw files bucket.

## Input

The function expects a CSV file with billing data. The CSV should contain columns including:

- `payer_account_id`: The AWS account ID
- `invoice_id`: The invoice ID
- `product_code`: The AWS product code
- `bill_period_start_date`: The billing period start date
- Additional billing data columns

## Processing

The function:

1. Downloads the CSV file from S3
2. Parses the CSV data
3. Transforms the data as needed
4. Writes the data to DynamoDB

## DynamoDB Schema

The function writes to a DynamoDB table with the following key structure:

- Partition Key: `payer_account_id`
- Sort Key: `invoice_id#product_code`

## Error Handling

The function handles various error cases including:

- Invalid CSV format
- Missing required columns
- S3 access issues
- DynamoDB write failures