"""
Unit tests for the get_user_accounts Lambda function.

This module tests the Lambda function that retrieves user account IDs from DynamoDB.
It mocks all AWS dependencies to isolate the function's business logic.
"""

import json
import pytest
import os
import sys
from unittest.mock import patch, MagicMock


def test_get_user_accounts_success():
    """Test the Lambda function's ability to retrieve user accounts successfully."""
    # Set up the path to the Lambda function
    lambda_path = os.path.join(
        os.path.dirname(__file__), "../../lambda/get_user_accounts"
    )

    # Mock the boto3 module
    mock_boto3 = MagicMock()

    # Mock DynamoDB resource and table
    mock_table = MagicMock()
    mock_table.get_item.return_value = {
        "Item": {
            "email": "test@example.com",
            "payer_account_ids": ["123456789012", "210987654321"],
        }
    }

    mock_dynamodb = MagicMock()
    mock_dynamodb.Table.return_value = mock_table

    # Set up boto3 resource mock
    mock_boto3.resource.return_value = mock_dynamodb

    # Add the lambda directory to the path
    sys.path.insert(0, lambda_path)

    try:
        # Apply the mocks to sys.modules
        with patch.dict("sys.modules", {"boto3": mock_boto3}):
            # Now import the app module
            import app

            # Replace the table with our mock
            app.table = mock_table

            # Create a simple mock for generate_trace_id
            app.generate_trace_id = MagicMock(return_value="test-trace-id")

            # Create a simple mock for log_with_context
            app.log_with_context = MagicMock()

            # Create an API Gateway event
            event = {
                "httpMethod": "GET",
                "queryStringParameters": {"email": "test@example.com"},
            }

            # Call the Lambda handler
            response = app.lambda_handler(event, MagicMock())

            # Verify DynamoDB interactions
            mock_table.get_item.assert_called_once_with(
                Key={"email": "test@example.com"}
            )

            # Verify response
            assert response["statusCode"] == 200
            body = json.loads(response["body"])
            assert body["email"] == "test@example.com"
            assert len(body["payer_account_ids"]) == 2
            assert "123456789012" in body["payer_account_ids"]
            assert "210987654321" in body["payer_account_ids"]

    finally:
        # Clean up
        if lambda_path in sys.path:
            sys.path.remove(lambda_path)
        if "app" in sys.modules:
            del sys.modules["app"]


def test_get_user_accounts_missing_email():
    """Test the Lambda function's handling of missing email parameter."""
    # Set up the path to the Lambda function
    lambda_path = os.path.join(
        os.path.dirname(__file__), "../../lambda/get_user_accounts"
    )

    # Mock the boto3 module
    mock_boto3 = MagicMock()

    # Mock DynamoDB resource and table
    mock_table = MagicMock()
    mock_dynamodb = MagicMock()
    mock_dynamodb.Table.return_value = mock_table

    # Set up boto3 resource mock
    mock_boto3.resource.return_value = mock_dynamodb

    # Add the lambda directory to the path
    sys.path.insert(0, lambda_path)

    try:
        # Apply the mocks to sys.modules
        with patch.dict("sys.modules", {"boto3": mock_boto3}):
            # Now import the app module
            import app

            # Replace the table with our mock
            app.table = mock_table

            # Create a simple mock for generate_trace_id
            app.generate_trace_id = MagicMock(return_value="test-trace-id")

            # Create a simple mock for log_with_context
            app.log_with_context = MagicMock()

            # Create an API Gateway event with missing email
            event = {"httpMethod": "GET", "queryStringParameters": {}}

            # Call the Lambda handler
            response = app.lambda_handler(event, MagicMock())

            # Verify DynamoDB interactions - should not be called
            mock_table.get_item.assert_not_called()

            # Verify response
            assert response["statusCode"] == 400
            body = json.loads(response["body"])
            assert "Missing 'email' parameter" in body["message"]

    finally:
        # Clean up
        if lambda_path in sys.path:
            sys.path.remove(lambda_path)
        if "app" in sys.modules:
            del sys.modules["app"]


def test_get_user_accounts_not_found():
    """Test the Lambda function's handling of non-existent email."""
    # Set up the path to the Lambda function
    lambda_path = os.path.join(
        os.path.dirname(__file__), "../../lambda/get_user_accounts"
    )

    # Mock the boto3 module
    mock_boto3 = MagicMock()

    # Mock DynamoDB resource and table - no item found
    mock_table = MagicMock()
    mock_table.get_item.return_value = {}  # No Item in response

    mock_dynamodb = MagicMock()
    mock_dynamodb.Table.return_value = mock_table

    # Set up boto3 resource mock
    mock_boto3.resource.return_value = mock_dynamodb

    # Add the lambda directory to the path
    sys.path.insert(0, lambda_path)

    try:
        # Apply the mocks to sys.modules
        with patch.dict("sys.modules", {"boto3": mock_boto3}):
            # Now import the app module
            import app

            # Replace the table with our mock
            app.table = mock_table

            # Create a simple mock for generate_trace_id
            app.generate_trace_id = MagicMock(return_value="test-trace-id")

            # Create a simple mock for log_with_context
            app.log_with_context = MagicMock()

            # Create an API Gateway event
            event = {
                "httpMethod": "GET",
                "queryStringParameters": {"email": "nonexistent@example.com"},
            }

            # Call the Lambda handler
            response = app.lambda_handler(event, MagicMock())

            # Verify DynamoDB interactions
            mock_table.get_item.assert_called_once_with(
                Key={"email": "nonexistent@example.com"}
            )

            # Verify response
            assert response["statusCode"] == 404
            body = json.loads(response["body"])
            assert "No accounts found for email" in body["message"]

    finally:
        # Clean up
        if lambda_path in sys.path:
            sys.path.remove(lambda_path)
        if "app" in sys.modules:
            del sys.modules["app"]
