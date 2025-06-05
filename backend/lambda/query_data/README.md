# Query Data Lambda

This Lambda function queries the billing data in DynamoDB based on various parameters and returns the results.

## Function Details

- **Handler**: `app.lambda_handler`
- **Runtime**: Python 3.10
- **Timeout**: 60 seconds
- **Memory**: Default (128 MB)

## Input

The function expects an API Gateway event with the following query parameters:

- `queryType`: The type of query to perform (account, date, or invoice)
- `accountId`: The AWS account ID (for account queries)
- `billPeriodStartDate`: The billing period start date (optional)
- `invoiceId`: The invoice ID (optional)
- `format`: The response format (json or csv)

Example:
```
GET /query?queryType=account&accountId=123456789012&billPeriodStartDate=2023-01
```

## Query Types

### Account Query

Queries by account ID, optionally filtered by invoice ID or bill period start date.

### Date Query

Queries by bill period start date, optionally filtered by product code.

### Invoice Query

Queries by invoice ID.

## Output Formats

### JSON

Returns a JSON response with the following structure:

```json
{
  "items": [...],
  "count": 42,
  "summary": {
    "unique_accounts": 1,
    "unique_invoices": 5,
    "unique_dates": 1,
    "unique_products": 10,
    "total_cost": 1234.56
  }
}
```

### CSV

Returns a CSV file with all the data fields. The filename is dynamically generated based on the query parameters.

## CORS Support

The function includes CORS headers to allow cross-origin requests from the frontend application.