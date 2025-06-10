"""Integration tests for user info upload functionality.

This module contains integration tests that verify the user info upload process
works correctly. These tests upload actual CSV files to the user access S3 bucket
and verify that the Lambda function processes them and updates the DynamoDB table.

Tests are skipped unless the ENVIRONMENT variable is set to "test" to prevent
accidental execution against production resources.
"""

import csv
import io
import os
import time
import uuid

import boto3
import pytest

# Skip tests if not in a test environment
pytestmark = pytest.mark.skipif(
    os.environ.get("ENVIRONMENT") != "test",
    reason="Integration tests should only run in test environment",
)

# Get bucket name from environment variable or use default for testing
USER_ACCESS_BUCKET = os.environ.get(
    "USER_ACCESS_BUCKET",
    "billquestmiscommitstack-user-access-bucket-nelmak",
)

# Get table name from environment variable or use default for testing
USER_INFO_TABLE = os.environ.get("USER_INFO_TABLE", "edp_miscommit_user_info_table")

# Test data with unique email to avoid conflicts
TEST_EMAIL = f"test-{uuid.uuid4()}@example.com"
TEST_ACCOUNT_IDS = ["123456789012", "210987654321"]


@pytest.fixture
def s3_client():
    """Create an S3 client for test operations.

    Returns:
        boto3.client: Configured S3 client

    """
    return boto3.client("s3", region_name="us-east-1")


@pytest.fixture
def dynamodb_client():
    """Create a DynamoDB client for test operations.

    Returns:
        boto3.resource: Configured DynamoDB resource

    """
    return boto3.resource("dynamodb", region_name="us-east-1")


def test_user_info_upload_to_dynamodb(s3_client, dynamodb_client):
    """Test that uploading a user info CSV file to S3 triggers the Lambda function
    and updates the user_info DynamoDB table.

    This test:
    1. Creates a test CSV file with user info data
    2. Uploads it to the user access S3 bucket
    3. Waits for the Lambda function to process it
    4. Verifies that the data was written to DynamoDB

    Args:
        s3_client: Fixture providing the S3 client
        dynamodb_client: Fixture providing the DynamoDB client

    """
    # Generate a unique test file name
    test_file_key = f"test-user-info-{uuid.uuid4()}.csv"

    # Create test CSV content
    csv_content = io.StringIO()
    writer = csv.writer(csv_content)
    writer.writerow(["email", "payer_account_id"])
    writer.writerow([TEST_EMAIL, ";".join(TEST_ACCOUNT_IDS)])

    # Upload the file to S3
    s3_client.put_object(
        Bucket=USER_ACCESS_BUCKET, Key=test_file_key, Body=csv_content.getvalue()
    )

    try:
        # Wait for Lambda to process the file (up to 30 seconds)
        table = dynamodb_client.Table(USER_INFO_TABLE)
        max_retries = 15
        found = False

        for i in range(max_retries):
            # Check if data was written to DynamoDB
            response = table.get_item(Key={"email": TEST_EMAIL})

            if "Item" in response:
                found = True
                break

            # Wait before retrying
            time.sleep(2)

        # Verify data was written to DynamoDB
        assert found, f"User info for {TEST_EMAIL} was not found in DynamoDB after {max_retries * 2} seconds"

        # Get the item again to verify its contents
        response = table.get_item(Key={"email": TEST_EMAIL})

        # Verify the data is correct
        item = response["Item"]
        assert item["email"] == TEST_EMAIL
        assert len(item["payer_account_ids"]) == len(TEST_ACCOUNT_IDS)
        for account_id in TEST_ACCOUNT_IDS:
            assert account_id in item["payer_account_ids"]

    finally:
        # Clean up - delete the test file
        s3_client.delete_object(Bucket=USER_ACCESS_BUCKET, Key=test_file_key)

        # Clean up - delete the DynamoDB item
        table.delete_item(Key={"email": TEST_EMAIL})


def test_user_info_update_existing_user(s3_client, dynamodb_client):
    """Test that uploading a user info CSV file updates an existing user's account IDs.

    This test:
    1. Creates an initial user record in DynamoDB
    2. Creates a test CSV file with updated account IDs
    3. Uploads it to the user access S3 bucket
    4. Waits for the Lambda function to process it
    5. Verifies that the user's account IDs were updated

    Args:
        s3_client: Fixture providing the S3 client
        dynamodb_client: Fixture providing the DynamoDB client

    """
    # Generate a unique test file name and email
    test_file_key = f"test-user-info-update-{uuid.uuid4()}.csv"
    test_email = f"test-update-{uuid.uuid4()}@example.com"
    initial_account_ids = ["111111111111"]
    updated_account_ids = ["222222222222", "333333333333"]

    # Create initial user record
    table = dynamodb_client.Table(USER_INFO_TABLE)
    table.put_item(Item={"email": test_email, "payer_account_ids": initial_account_ids})

    # Create test CSV content with updated account IDs
    csv_content = io.StringIO()
    writer = csv.writer(csv_content)
    writer.writerow(["email", "payer_account_id"])
    writer.writerow([test_email, ";".join(updated_account_ids)])

    # Upload the file to S3
    s3_client.put_object(
        Bucket=USER_ACCESS_BUCKET, Key=test_file_key, Body=csv_content.getvalue()
    )

    try:
        # Wait for Lambda to process the file (up to 30 seconds)
        max_retries = 15
        updated = False

        for i in range(max_retries):
            # Check if data was updated in DynamoDB
            response = table.get_item(Key={"email": test_email})

            if "Item" in response:
                item = response["Item"]
                # Check if the account IDs have been updated
                if all(
                    account_id in item["payer_account_ids"]
                    for account_id in updated_account_ids
                ):
                    updated = True
                    break

            # Wait before retrying
            time.sleep(2)

        # Verify data was updated in DynamoDB
        assert updated, f"User info for {test_email} was not updated in DynamoDB after {max_retries * 2} seconds"

        # Get the item again to verify its contents
        response = table.get_item(Key={"email": test_email})

        # Verify the data is correct
        item = response["Item"]
        assert item["email"] == test_email

        # Verify that all account IDs are present (both initial and updated)
        for account_id in updated_account_ids:
            assert account_id in item["payer_account_ids"]

    finally:
        # Clean up - delete the test file
        s3_client.delete_object(Bucket=USER_ACCESS_BUCKET, Key=test_file_key)

        # Clean up - delete the DynamoDB item
        table.delete_item(Key={"email": test_email})
