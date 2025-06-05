# Integration Tests

This directory contains integration tests for the BillQuest application.

## Purpose

Integration tests verify that different components of the system work together correctly. These tests focus on the interactions between:

- Lambda functions and DynamoDB tables
- API Gateway and Lambda functions
- S3 event triggers and Lambda functions

## Test Structure

Each test file should focus on a specific integration scenario:

- `test_api_gateway.py`: Tests for API Gateway endpoints
- `test_s3_triggers.py`: Tests for S3 event triggers
- `test_dynamodb_access.py`: Tests for DynamoDB access patterns

## Running Tests

To run the integration tests:

```bash
# From the project root
cd backend
pytest tests/integration
```

## Writing Integration Tests

When writing integration tests:

1. Use the AWS SDK (boto3) to interact with real AWS services in a test environment
2. Create and clean up test resources to avoid affecting production data
3. Use unique identifiers for test resources to prevent conflicts
4. Mock external dependencies when appropriate