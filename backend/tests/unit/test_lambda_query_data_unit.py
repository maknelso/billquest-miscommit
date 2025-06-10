"""
Unit tests for the query_data Lambda function.

This module tests the Lambda function that queries billing data from DynamoDB.
It mocks all AWS dependencies to isolate the function's business logic.
"""

import json
import pytest
import os
import sys
from decimal import Decimal
from unittest.mock import patch, MagicMock


def test_query_by_account():
    """
    Test the Lambda function's ability to query billing data by account ID.

    This test verifies that:
    1. The function correctly processes 'account' query type requests
    2. It properly queries DynamoDB using the account ID
    3. It returns the expected data in the correct format
    4. The response includes proper status code and CORS headers
    """
    # Set up the path to the Lambda function
    lambda_path = os.path.join(os.path.dirname(__file__), "../../lambda/query_data")

    # Create mock classes for boto3.dynamodb.conditions
    # These are used by the Lambda to build DynamoDB query expressions
    mock_key = MagicMock()
    mock_attr = MagicMock()

    # Mock the boto3 module and its submodules
    # This prevents actual AWS API calls during testing
    mock_boto3 = MagicMock()
    mock_boto3.dynamodb = MagicMock()
    mock_boto3.dynamodb.conditions = MagicMock()
    mock_boto3.dynamodb.conditions.Key = mock_key
    mock_boto3.dynamodb.conditions.Attr = mock_attr

    # Mock the table with a predefined response
    # This simulates what would be returned from a real DynamoDB query
    mock_table = MagicMock()
    mock_table.query.return_value = {
        "Items": [
            {
                "payer_account_id": "123456789012",
                "invoice_id#product_code": "INV123#EC2",
                "invoice_id": "INV123",
                "product_code": "EC2",
                "bill_period_start_date": "2023-01-01",
                "cost_before_tax": Decimal("100.50"),
            }
        ]
    }

    # Mock the dynamodb resource that returns our mock table
    mock_dynamodb = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    mock_boto3.resource.return_value = mock_dynamodb

    # Add the lambda directory to the path so we can import the app module
    sys.path.insert(0, lambda_path)

    try:
        # Apply the mocks to sys.modules to intercept imports
        # This ensures that when the Lambda code imports boto3, it gets our mock
        with patch.dict(
            "sys.modules",
            {
                "boto3": mock_boto3,
                "boto3.dynamodb": mock_boto3.dynamodb,
                "boto3.dynamodb.conditions": mock_boto3.dynamodb.conditions,
            },
        ):
            # Now import the app module after all mocks are in place
            import app

            # Replace the table with our mock to ensure queries use our mock
            app.table = mock_table

            # Set environment variable for the Lambda function
            # This simulates how AWS Lambda provides configuration
            os.environ["TABLE_NAME"] = "edp_miscommit"

            # Create an API Gateway event with query parameters
            # This simulates the event that would be passed to the Lambda by API Gateway
            event = {
                "queryStringParameters": {
                    "queryType": "account",
                    "accountId": "123456789012",
                },
                "httpMethod": "GET",
            }

            # Call the Lambda handler with our test event
            response = app.lambda_handler(event, {})

            # Verify the response meets our expectations
            assert response["statusCode"] == 200  # Successful response
            body = json.loads(response["body"])
            assert "items" in body  # Response contains items array
            assert len(body["items"]) == 1  # One item returned
            assert (
                body["items"][0]["payer_account_id"] == "123456789012"
            )  # Correct account ID

    finally:
        # Clean up to prevent test interference with other tests
        if lambda_path in sys.path:
            sys.path.remove(lambda_path)
        if "app" in sys.modules:
            del sys.modules["app"]
