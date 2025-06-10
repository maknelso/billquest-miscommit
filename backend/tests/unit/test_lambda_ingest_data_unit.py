"""Unit tests for the ingest_data Lambda function.

This module tests the Lambda function that processes CSV files from S3 and writes data to DynamoDB.
It mocks all AWS dependencies to isolate the function's business logic.
"""

import json
import os
import sys
from unittest.mock import MagicMock, patch


def test_process_csv_file():
    """Test the Lambda function's ability to process a CSV file from S3.

    This test verifies that:
    1. The function correctly checks if a file was already processed
    2. It properly reads and parses CSV data from S3
    3. It writes the processed data to DynamoDB
    4. It marks the file as processed after successful processing
    5. It returns a proper success response with statistics
    """
    # Set up the path to the Lambda function
    lambda_path = os.path.join(os.path.dirname(__file__), "../../lambda/ingest_data")

    # Mock the boto3 module
    mock_boto3 = MagicMock()

    # Mock S3 client
    mock_s3_client = MagicMock()
    mock_s3_client.head_object.return_value = {"Metadata": {}}  # File not processed

    # Create mock CSV content
    csv_content = """payer_account_id,invoice_id,product_code,bill_period_start_date,cost_before_tax
123456789012,INV123,EC2,2023-01-01,100.50
123456789012,INV123,S3,2023-01-01,50.25"""

    # Mock S3 get_object response
    mock_s3_client.get_object.return_value = {
        "Body": MagicMock(read=MagicMock(return_value=csv_content.encode()))
    }

    # Mock DynamoDB resource and table
    mock_table = MagicMock()
    mock_batch_writer = MagicMock()
    mock_table.batch_writer.return_value.__enter__.return_value = mock_batch_writer

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
                    {"message": "Success", "statistics": {"processed": 2}}
                ),
            }

            sys.modules["utils.error_handler"] = mock_error_handler
            sys.modules["utils.response_formatter"] = mock_response_formatter
            sys.modules["utils.logging_utils"] = MagicMock()

            # Now import the app module
            import app

            # Replace the clients with our mocks
            app.s3_client = mock_s3_client
            app.table = mock_table

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
            mock_s3_client.head_object.assert_called_once_with(
                Bucket="test-bucket", Key="test-file.csv"
            )
            mock_s3_client.get_object.assert_called_once_with(
                Bucket="test-bucket", Key="test-file.csv"
            )

            # Verify the file was marked as processed
            mock_s3_client.copy_object.assert_called_once()

            # Verify DynamoDB batch write was used
            assert mock_table.batch_writer.called

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


def test_already_processed_file():
    """Test the Lambda function's handling of already processed files."""
    # Set up the path to the Lambda function
    lambda_path = os.path.join(os.path.dirname(__file__), "../../lambda/ingest_data")

    # Mock the boto3 module
    mock_boto3 = MagicMock()

    # Mock S3 client - file already processed
    mock_s3_client = MagicMock()
    mock_s3_client.head_object.return_value = {"Metadata": {"processed": "true"}}

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
            sys.modules["utils.error_handler"] = MagicMock()
            sys.modules["utils.response_formatter"] = MagicMock()
            sys.modules["utils.logging_utils"] = MagicMock()

            # Now import the app module
            import app

            # Replace the clients with our mocks
            app.s3_client = mock_s3_client
            app.table = mock_table

            # Create a simple mock for format_success_response
            def mock_format_success(message, **kwargs):
                return {
                    "statusCode": 200,
                    "body": "File test-file.csv was already processed. Skipping.",
                }

            # Replace the format_success_response function
            app.format_success_response = mock_format_success

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

            # Call the Lambda handler
            response = app.lambda_handler(event, context=MagicMock())

            # Verify S3 interactions
            mock_s3_client.head_object.assert_called_once_with(
                Bucket="test-bucket", Key="test-file.csv"
            )

            # Verify get_object was NOT called (file skipped)
            mock_s3_client.get_object.assert_not_called()

            # Verify success response was returned
            assert response["statusCode"] == 200
            assert "processed" in response["body"]

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
