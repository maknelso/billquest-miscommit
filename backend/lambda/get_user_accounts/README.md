# Get User Accounts Lambda

This Lambda function retrieves the payer account IDs associated with a user's email address from DynamoDB.

## Function Details

- **Handler**: `app.lambda_handler`
- **Runtime**: Python 3.10
- **Timeout**: 30 seconds
- **Memory**: Default (128 MB)

## Input

The function expects an API Gateway event with the following query parameter:

- `email`: The email address to look up

Example:
```
GET /user-accounts?email=user@example.com
```

## Output

The function returns a JSON response with the following structure:

```json
{
  "email": "user@example.com",
  "payer_account_ids": ["ACCOUNT-123", "ACCOUNT-456"]
}
```

## Error Handling

The function handles the following error cases:

- Missing email parameter (400 Bad Request)
- Email not found in the database (404 Not Found)
- Database errors (500 Internal Server Error)

## CORS Support

The function includes CORS headers to allow cross-origin requests from the frontend application.

## Authentication

This function is protected by a Cognito authorizer in API Gateway. The caller must include a valid JWT token in the Authorization header.