"""
Unit tests for the update_user_info Lambda function.

This module tests the Lambda function that processes CSV files from S3 and updates user info in DynamoDB.
It mocks all AWS dependencies to isolate the function's business logic.
"""

import json
import pytest
import os
import sys
from unittest.mock import patch, MagicMock


def test_process_csv_file():
    """Test the Lambda function's ability to process a CSV file with user info."""
    # Set up the path to the Lambda function
    lambda_path = os.path.join(
        os.path.dirname(__file__), "../../lambda/update_user_info"
    )

    # Mock the boto3 module
    mock_boto3 = MagicMock()

    # Mock S3 client
    mock_s3_client = MagicMock()

    # Create mock CSV content
    csv_content = """email,payer_account_id
test@example.com,123456789012;210987654321
another@example.com,987654321098"""

    # Mock S3 get_object response
    mock_s3_client.get_object.return_value = {
        "Body": MagicMock(read=MagicMock(return_value=csv_content.encode()))
    }

    # Mock DynamoDB resource and table
    mock_table = MagicMock()

    mock_dynamodb = MagicMock()
    mock_dynamodb.Table.return_value = mock_table

    # Set up boto3 resource and client mocks
    mock_boto3.resource.return_value = mock_dynamodb
    mock_boto3.client.return_value = mock_s3_client

    # Add the lambda directory to the path
    sys.path.insert(0, lambda_path)

    try:
        # Apply the mocks to sys.modules
        with patch.dict("sys.modules", {"boto3": mock_boto3}):
            # Mock the utils modules
            mock_error_handler = MagicMock()
            mock_response_formatter = MagicMock()
            mock_response_formatter.format_success_response.return_value = {
                "statusCode": 200,
                "body": json.dumps(
                    {
                        "message": "Successfully processed file test-file.csv",
                        "statistics": {
                            "processed": 2,
                            "skipped": 0,
                            "errors": 0,
                            "total": 2,
                        },
                    }
                ),
            }

            sys.modules["utils.error_handler"] = mock_error_handler
            sys.modules["utils.response_formatter"] = mock_response_formatter
            sys.modules["utils.logging_utils"] = MagicMock()
            sys.modules["utils.cors_config"] = MagicMock()

            # Now import the app module
            import app

            # Replace the clients with our mocks
            app.s3_client = mock_s3_client
            app.table = mock_table
            app.format_success_response = (
                mock_response_formatter.format_success_response
            )

            # Create an S3 event
            event = {
                "Records": [
                    {
                        "s3": {
                            "bucket": {"name": "test-bucket"},
                            "object": {"key": "test-file.csv"},
                        }
                    }
                ]
            }

            # Create a mock context
            context = MagicMock()
            context.aws_request_id = "test-request-id"
            context.function_name = "test-function"

            # Call the Lambda handler
            response = app.lambda_handler(event, context)

            # Verify S3 interactions
            mock_s3_client.get_object.assert_called_once_with(
                Bucket="test-bucket", Key="test-file.csv"
            )

            # Verify DynamoDB interactions - should be called twice (once for each row)
            assert mock_table.put_item.call_count == 2

            # Verify the first put_item call (test@example.com)
            first_call_args = mock_table.put_item.call_args_list[0][1]
            assert first_call_args["Item"]["email"] == "test@example.com"
            assert len(first_call_args["Item"]["payer_account_ids"]) == 2
            assert "123456789012" in first_call_args["Item"]["payer_account_ids"]
            assert "210987654321" in first_call_args["Item"]["payer_account_ids"]

            # Verify the second put_item call (another@example.com)
            second_call_args = mock_table.put_item.call_args_list[1][1]
            assert second_call_args["Item"]["email"] == "another@example.com"
            assert len(second_call_args["Item"]["payer_account_ids"]) == 1
            assert "987654321098" in second_call_args["Item"]["payer_account_ids"]

            # Verify success response was returned
            assert response["statusCode"] == 200

    finally:
        # Clean up
        if lambda_path in sys.path:
            sys.path.remove(lambda_path)
        if "app" in sys.modules:
            del sys.modules["app"]
        if "utils.error_handler" in sys.modules:
            del sys.modules["utils.error_handler"]
        if "utils.response_formatter" in sys.modules:
            del sys.modules["utils.response_formatter"]
        if "utils.logging_utils" in sys.modules:
            del sys.modules["utils.logging_utils"]
        if "utils.cors_config" in sys.modules:
            del sys.modules["utils.cors_config"]


def test_invalid_csv_format():
    """Test the Lambda function's handling of invalid CSV format."""
    # Set up the path to the Lambda function
    lambda_path = os.path.join(
        os.path.dirname(__file__), "../../lambda/update_user_info"
    )

    # Mock the boto3 module
    mock_boto3 = MagicMock()

    # Mock S3 client
    mock_s3_client = MagicMock()

    # Create mock CSV content with missing required columns
    csv_content = """name,company
John Doe,ACME Inc
Jane Smith,XYZ Corp"""

    # Mock S3 get_object response
    mock_s3_client.get_object.return_value = {
        "Body": MagicMock(read=MagicMock(return_value=csv_content.encode()))
    }

    # Mock DynamoDB resource and table
    mock_table = MagicMock()

    mock_dynamodb = MagicMock()
    mock_dynamodb.Table.return_value = mock_table

    # Set up boto3 resource and client mocks
    mock_boto3.resource.return_value = mock_dynamodb
    mock_boto3.client.return_value = mock_s3_client

    # Add the lambda directory to the path
    sys.path.insert(0, lambda_path)

    try:
        # Apply the mocks to sys.modules
        with patch.dict("sys.modules", {"boto3": mock_boto3}):
            # Mock the utils modules
            mock_error_handler = MagicMock()
            mock_response_formatter = MagicMock()
            mock_response_formatter.format_success_response.return_value = {
                "statusCode": 200,
                "body": json.dumps(
                    {
                        "message": "Successfully processed file test-file.csv",
                        "statistics": {
                            "processed": 0,
                            "skipped": 2,  # Both rows should be skipped
                            "errors": 0,
                            "total": 2,
                        },
                    }
                ),
            }

            sys.modules["utils.error_handler"] = mock_error_handler
            sys.modules["utils.response_formatter"] = mock_response_formatter
            sys.modules["utils.logging_utils"] = MagicMock()
            sys.modules["utils.cors_config"] = MagicMock()

            # Now import the app module
            import app

            # Replace the clients with our mocks
            app.s3_client = mock_s3_client
            app.table = mock_table
            app.format_success_response = (
                mock_response_formatter.format_success_response
            )

            # Create an S3 event
            event = {
                "Records": [
                    {
                        "s3": {
                            "bucket": {"name": "test-bucket"},
                            "object": {"key": "test-file.csv"},
                        }
                    }
                ]
            }

            # Create a mock context
            context = MagicMock()
            context.aws_request_id = "test-request-id"
            context.function_name = "test-function"

            # Call the Lambda handler
            response = app.lambda_handler(event, context)

            # Verify S3 interactions
            mock_s3_client.get_object.assert_called_once_with(
                Bucket="test-bucket", Key="test-file.csv"
            )

            # Verify DynamoDB interactions - should not be called
            mock_table.put_item.assert_not_called()

            # Verify success response was returned with skipped rows
            assert response["statusCode"] == 200
            response_body = json.loads(response["body"])
            assert response_body["statistics"]["skipped"] == 2
            assert response_body["statistics"]["processed"] == 0

    finally:
        # Clean up
        if lambda_path in sys.path:
            sys.path.remove(lambda_path)
        if "app" in sys.modules:
            del sys.modules["app"]
        if "utils.error_handler" in sys.modules:
            del sys.modules["utils.error_handler"]
        if "utils.response_formatter" in sys.modules:
            del sys.modules["utils.response_formatter"]
        if "utils.logging_utils" in sys.modules:
            del sys.modules["utils.logging_utils"]
        if "utils.cors_config" in sys.modules:
            del sys.modules["utils.cors_config"]
