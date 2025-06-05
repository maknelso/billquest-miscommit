# Update User Info Lambda

This Lambda function processes CSV files containing user information and updates the user info DynamoDB table.

## Function Details

- **Handler**: `app.lambda_handler`
- **Runtime**: Python 3.10
- **Timeout**: 60 seconds
- **Memory**: Default (128 MB)

## Trigger

This function is triggered by S3 object creation events in the user info bucket.

## Input

The function expects a CSV file with the following columns:

- `email`: The user's email address
- `payer_account_id`: Semicolon-separated list of AWS account IDs

Example CSV content:
```
email,payer_account_id
user@example.com,ACCOUNT-123;ACCOUNT-456;ACCOUNT-789
```

## Processing

The function:

1. Downloads the CSV file from S3
2. Parses the CSV data
3. For each row:
   - Extracts the email and payer_account_ids
   - Splits the payer_account_ids by semicolon
   - Writes the data to DynamoDB

## DynamoDB Schema

The function writes to a DynamoDB table with the following structure:

- Partition Key: `email`
- Attribute: `payer_account_ids` (List of strings)

## Error Handling

The function handles various error cases including:

- Invalid CSV format
- Missing required columns
- Empty values
- S3 access issues
- DynamoDB write failures

## Notes

- The function handles UTF-8 BOM characters in CSV files
- Each new file upload will overwrite existing entries with the same email