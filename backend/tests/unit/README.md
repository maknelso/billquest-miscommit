# Unit Tests

This directory contains unit tests for individual components of the BillQuest application.

## Purpose

Unit tests verify that individual components work correctly in isolation. These tests focus on:

- Lambda function logic
- Utility functions
- CDK constructs
- Helper classes

## Test Structure

Each test file should focus on a specific component:

- `test_bill_quest_miscommit_stack.py`: Tests for the CDK stack
- `test_query_data_lambda.py`: Tests for the query data Lambda function
- `test_ingest_data_lambda.py`: Tests for the ingest data Lambda function
- `test_get_user_accounts_lambda.py`: Tests for the get user accounts Lambda function
- `test_update_user_info_lambda.py`: Tests for the update user info Lambda function

## Running Tests

To run the unit tests:

```bash
# From the project root
cd backend
pytest tests/unit
```

## Writing Unit Tests

When writing unit tests:

1. Mock external dependencies (AWS services, other components)
2. Test both success and failure cases
3. Validate input validation and error handling
4. Use descriptive test names that explain what is being tested
5. Keep tests small and focused on a single aspect of the component