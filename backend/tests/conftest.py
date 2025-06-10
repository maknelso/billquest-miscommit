"""
Test configuration and fixtures for BillQuest application.

This module provides pytest fixtures for mocking AWS services used in the BillQuest application.
It uses the moto library to create mock AWS resources that can be used in unit tests
without making actual AWS API calls.

Fixtures:
- aws_credentials: Sets up mock AWS credentials for testing
- dynamodb: Provides a mock DynamoDB service
- s3: Provides a mock S3 service
- billing_table: Creates a mock billing data table with GSIs for testing
- user_info_table: Creates a mock user info table for testing
- s3_buckets: Creates mock S3 buckets used by the application
"""

import os
import pytest
import boto3
from moto import mock_dynamodb, mock_s3


@pytest.fixture(scope="function")
def aws_credentials():
    """
    Mocked AWS Credentials for boto3.

    Sets environment variables with fake credentials that will be used by boto3
    when creating AWS service clients and resources.
    """
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture(scope="function")
def dynamodb(aws_credentials):
    """
    DynamoDB mock fixture.

    Creates a mock DynamoDB service using moto that intercepts boto3 calls.
    This fixture depends on aws_credentials.
    """
    with mock_dynamodb():
        yield boto3.resource("dynamodb", region_name="us-east-1")


@pytest.fixture(scope="function")
def s3(aws_credentials):
    """
    S3 mock fixture.

    Creates a mock S3 service using moto that intercepts boto3 calls.
    This fixture depends on aws_credentials.
    """
    with mock_s3():
        yield boto3.resource("s3", region_name="us-east-1")


@pytest.fixture(scope="function")
def billing_table(dynamodb):
    """
    Create a mock billing data table.

    Creates a DynamoDB table with the same schema as the production billing data table,
    including the primary key (payer_account_id, invoice_id#product_code) and
    two GSIs (InvoiceIndex and DateProductIndex).
    """
    table = dynamodb.create_table(
        TableName="edp_miscommit",
        KeySchema=[
            {"AttributeName": "payer_account_id", "KeyType": "HASH"},
            {"AttributeName": "invoice_id#product_code", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "payer_account_id", "AttributeType": "S"},
            {"AttributeName": "invoice_id#product_code", "AttributeType": "S"},
            {"AttributeName": "invoice_id", "AttributeType": "S"},
            {"AttributeName": "bill_period_start_date", "AttributeType": "S"},
            {"AttributeName": "product_code", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "InvoiceIndex",
                "KeySchema": [
                    {"AttributeName": "invoice_id", "KeyType": "HASH"},
                    {"AttributeName": "product_code", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "DateProductIndex",
                "KeySchema": [
                    {"AttributeName": "bill_period_start_date", "KeyType": "HASH"},
                    {"AttributeName": "product_code", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    return table


@pytest.fixture(scope="function")
def user_info_table(dynamodb):
    """
    Create a mock user info table.

    Creates a DynamoDB table with the same schema as the production user info table,
    with email as the primary key.
    """
    table = dynamodb.create_table(
        TableName="edp_miscommit_user_info_table",
        KeySchema=[
            {"AttributeName": "email", "KeyType": "HASH"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "email", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    return table


@pytest.fixture(scope="function")
def s3_buckets(s3):
    """
    Create mock S3 buckets.

    Creates the three S3 buckets used by the application:
    - Raw files bucket: For uploading billing data CSV files
    - User info bucket: For uploading user-account mapping CSV files
    - Website bucket: For hosting the frontend static files
    """
    # Create raw files bucket
    s3.create_bucket(Bucket="billquestmiscommitstack-rawfilesbucket-nelmak")

    # Create user info bucket
    s3.create_bucket(Bucket="billquestmiscommitstack-user-access-bucket-nelmak")

    # Create website bucket
    s3.create_bucket(Bucket="billquestmiscommitstack-websitebucket-nelmak")

    return s3
