# Lambda Functions

This directory contains the AWS Lambda functions used in the BillQuest application.

## Functions

### get_user_accounts

Retrieves the payer account IDs associated with a user's email address.

- **Trigger**: API Gateway GET request
- **Input**: Email address as a query parameter
- **Output**: List of payer account IDs associated with the email
- **DynamoDB Table**: `edp_miscommit_user_info_table`

### ingest_data

Processes CSV files uploaded to the raw files S3 bucket and stores the data in DynamoDB.

- **Trigger**: S3 object creation event
- **Input**: CSV file with billing data
- **Output**: Data stored in DynamoDB
- **DynamoDB Table**: `edp_miscommit`

### query_data

Queries the billing data based on various parameters and returns the results.

- **Trigger**: API Gateway GET request
- **Input**: Query parameters (account ID, invoice ID, bill period)
- **Output**: Matching billing data records
- **DynamoDB Table**: `edp_miscommit`
- **Features**: CSV export, data summarization

### update_user_info

Processes CSV files containing user information and updates the user info DynamoDB table.

- **Trigger**: S3 object creation event
- **Input**: CSV file with user email and payer account IDs
- **Output**: User information stored in DynamoDB
- **DynamoDB Table**: `edp_miscommit_user_info_table`
- **Note**: Handles semicolon-separated payer account IDs

## Development

Each Lambda function directory contains:

- `app.py`: The Lambda function code
- `requirements.txt` (if needed): Python dependencies

To update a Lambda function:

1. Modify the code in the appropriate directory
2. Deploy the changes with `cdk deploy`