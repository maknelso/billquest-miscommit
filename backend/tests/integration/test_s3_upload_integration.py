"""Integration tests for S3 upload functionality.

This module contains integration tests that verify the S3 upload triggers Lambda functions
and updates DynamoDB correctly. These tests upload actual files to S3 buckets and verify
that the data processing pipeline works end-to-end.

Tests are skipped unless the ENVIRONMENT variable is set to "test" to prevent
accidental execution against production resources.
"""

import io
import os
import time
import uuid

import boto3
import pandas as pd
import pytest

# Skip tests if not in a test environment
pytestmark = pytest.mark.skipif(
    os.environ.get("ENVIRONMENT") != "test",
    reason="Integration tests should only run in test environment",
)

# Get bucket names from environment variables or use defaults for testing
RAW_FILES_BUCKET = os.environ.get(
    "RAW_FILES_BUCKET",
    "billquestmiscommitstack-rawfilesbucket-nelmak",
)
USER_ACCESS_BUCKET = os.environ.get(
    "USER_ACCESS_BUCKET",
    "billquestmiscommitstack-user-access-bucket-nelmak",
)

# Get table names from environment variables or use defaults for testing
BILLING_TABLE = os.environ.get("BILLING_TABLE", "edp_miscommit")
USER_INFO_TABLE = os.environ.get("USER_INFO_TABLE", "edp_miscommit_user_info_table")

# Test data
TEST_ACCOUNT_ID = "123456789012"
TEST_EMAIL = f"test-{uuid.uuid4()}@example.com"


@pytest.fixture
def s3_client():
    """Create an S3 client for test operations."""
    return boto3.client("s3", region_name="us-east-1")


@pytest.fixture
def dynamodb_client():
    """Create a DynamoDB client for test operations."""
    return boto3.resource("dynamodb", region_name="us-east-1")


def test_billing_data_upload_to_dynamodb(s3_client, dynamodb_client):
    """Test that uploading a billing data Excel file to S3 triggers the Lambda function
    and updates the DynamoDB table.
    """
    # Generate a unique test file name
    test_file_key = f"test-billing-data-{uuid.uuid4()}.xlsx"

    # Create test Excel content using pandas
    test_data = pd.DataFrame(
        {
            "payer_account_id": [TEST_ACCOUNT_ID],
            "invoice_id": ["INV123"],
            "product_code": ["EC2"],
            "bill_period_start_date": ["2023-01-01"],
            "cost_before_tax": [100.50],
        }
    )
    excel_bytes = io.BytesIO()
    test_data.to_excel(excel_bytes, index=False, engine="openpyxl")
    excel_bytes.seek(0)
    excel_content = excel_bytes.getvalue()

    # Upload the file to S3
    s3_client.put_object(Bucket=RAW_FILES_BUCKET, Key=test_file_key, Body=excel_content)

    try:
        # Wait for Lambda to process the file (up to 30 seconds)
        table = dynamodb_client.Table(BILLING_TABLE)
        max_retries = 15
        for i in range(max_retries):
            # Check if the file was processed (metadata updated)
            response = s3_client.head_object(Bucket=RAW_FILES_BUCKET, Key=test_file_key)
            metadata = response.get("Metadata", {})
            if metadata.get("processed") == "true":
                break

            # Check if data was written to DynamoDB
            response = table.query(
                KeyConditionExpression="payer_account_id = :pid",
                ExpressionAttributeValues={":pid": TEST_ACCOUNT_ID},
            )
            if response["Items"]:
                break

            # Wait before retrying
            time.sleep(2)

        # Verify the file was marked as processed
        response = s3_client.head_object(Bucket=RAW_FILES_BUCKET, Key=test_file_key)
        metadata = response.get("Metadata", {})
        assert metadata.get("processed") == "true", "File was not marked as processed"

        # Verify data was written to DynamoDB
        response = table.query(
            KeyConditionExpression="payer_account_id = :pid",
            ExpressionAttributeValues={":pid": TEST_ACCOUNT_ID},
        )
        assert len(response["Items"]) > 0, "No items found in DynamoDB"

        # Verify the data is correct
        item = response["Items"][0]
        assert item["payer_account_id"] == TEST_ACCOUNT_ID
        assert item["invoice_id"] == "INV123"
        assert item["product_code"] == "EC2"
        assert item["bill_period_start_date"] == "2023-01-01"
        assert float(item["cost_before_tax"]) == 100.50

    finally:
        # Clean up - delete the test file
        s3_client.delete_object(Bucket=RAW_FILES_BUCKET, Key=test_file_key)

        # Clean up - delete the DynamoDB item
        table.delete_item(
            Key={
                "payer_account_id": TEST_ACCOUNT_ID,
                "invoice_id#product_code": "INV123#EC2",
            }
        )
