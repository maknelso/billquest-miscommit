"""End-to-End test for the complete data processing flow.

This test verifies the entire data processing pipeline from file upload to data retrieval.
It uploads a test Excel file to S3, waits for Lambda to process it, and then queries the API
to verify the data was correctly processed and stored.

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
import requests

# Skip tests if not in a test environment
pytestmark = pytest.mark.skipif(
    os.environ.get("ENVIRONMENT") != "test",
    reason="E2E tests should only run in test environment",
)

# Get S3 bucket name from environment or use default for testing
RAW_FILES_BUCKET = os.environ.get(
    "RAW_FILES_BUCKET",
    "billquestmiscommitstack-rawfilesbucket-nelmak",
)

# Get API endpoint from environment or use default for testing
QUERY_API_ENDPOINT = os.environ.get(
    "QUERY_API_ENDPOINT",
    "https://6f3ntv3qq8.execute-api.us-east-1.amazonaws.com/prod/query",
)

# Test data with unique values to avoid conflicts
TEST_ACCOUNT_ID = f"test-{uuid.uuid4()}"[:8]
TEST_INVOICE_ID = f"INV-{uuid.uuid4()}"[:10]
TEST_PRODUCT_CODE = "EC2"
TEST_DATE = "2023-01-01"
TEST_COST = "123.45"


@pytest.fixture
def s3_client():
    """Create an S3 client for test operations."""
    return boto3.client("s3", region_name="us-east-1")


@pytest.fixture
def dynamodb_client():
    """Create a DynamoDB client for test operations."""
    return boto3.resource("dynamodb", region_name="us-east-1")


def test_end_to_end_data_flow(s3_client, dynamodb_client):
    """Test the complete data flow from file upload to data retrieval.

    This test:
    1. Creates a test Excel file with billing data
    2. Uploads it to the S3 bucket
    3. Waits for the Lambda function to process it
    4. Queries the API to retrieve the processed data
    5. Verifies the data matches what was uploaded
    """
    # Generate a unique test file name
    test_file_key = f"test-billing-data-{uuid.uuid4()}.xlsx"

    # Create test Excel content using pandas
    test_data = pd.DataFrame(
        {
            "payer_account_id": [TEST_ACCOUNT_ID],
            "invoice_id": [TEST_INVOICE_ID],
            "product_code": [TEST_PRODUCT_CODE],
            "bill_period_start_date": [TEST_DATE],
            "cost_before_tax": [float(TEST_COST)],
        }
    )

    # Convert to Excel bytes
    excel_bytes = io.BytesIO()
    test_data.to_excel(excel_bytes, index=False, engine="openpyxl")
    excel_bytes.seek(0)
    excel_content = excel_bytes.getvalue()

    try:
        # Step 1: Upload the file to S3
        print(f"Uploading test file {test_file_key} to S3...")
        s3_client.put_object(
            Bucket=RAW_FILES_BUCKET, Key=test_file_key, Body=excel_content
        )

        # Step 2: Wait for Lambda to process the file (up to 60 seconds)
        print("Waiting for Lambda to process the file...")
        max_retries = 30
        processed = False

        for i in range(max_retries):
            # Check if the file was processed (metadata updated)
            try:
                response = s3_client.head_object(
                    Bucket=RAW_FILES_BUCKET, Key=test_file_key
                )
                metadata = response.get("Metadata", {})
                if metadata.get("processed") == "true":
                    processed = True
                    print("File was processed successfully!")
                    break
            except Exception as e:
                print(f"Error checking file metadata: {e}")

            # Wait before retrying
            time.sleep(2)
            print(f"Waiting... ({i + 1}/{max_retries})")

        assert processed, f"File was not processed after {max_retries * 2} seconds"

        # Step 3: Query the API to retrieve the data
        print("Querying API for processed data...")
        params = {"queryType": "account", "accountId": TEST_ACCOUNT_ID}
        response = requests.get(QUERY_API_ENDPOINT, params=params)

        # Verify API response
        assert (
            response.status_code == 200
        ), f"API returned status code {response.status_code}"

        # Step 4: Verify the data matches what was uploaded
        data = response.json()
        assert "items" in data, "API response missing 'items' field"
        assert data["count"] > 0, "API returned no items"

        # Find our test item in the results
        found = False
        for item in data["items"]:
            if (
                item["payer_account_id"] == TEST_ACCOUNT_ID
                and item["invoice_id"] == TEST_INVOICE_ID
                and item["product_code"] == TEST_PRODUCT_CODE
            ):
                found = True
                assert item["bill_period_start_date"] == TEST_DATE
                assert float(item["cost_before_tax"]) == float(TEST_COST)
                break

        assert found, f"Test data not found in API response: {data}"
        print("End-to-end test successful!")

    finally:
        # Clean up - delete the test file
        try:
            s3_client.delete_object(Bucket=RAW_FILES_BUCKET, Key=test_file_key)
            print(f"Cleaned up test file {test_file_key}")
        except Exception as e:
            print(f"Error cleaning up test file: {e}")

        # Clean up - delete the DynamoDB item
        try:
            table = dynamodb_client.Table("edp_miscommit")
            table.delete_item(
                Key={
                    "payer_account_id": TEST_ACCOUNT_ID,
                    "invoice_id#product_code": f"{TEST_INVOICE_ID}#{TEST_PRODUCT_CODE}",
                }
            )
            print("Cleaned up DynamoDB item")
        except Exception as e:
            print(f"Error cleaning up DynamoDB item: {e}")
