import os
import pytest
import boto3
from moto import mock_dynamodb, mock_s3


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for boto3."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture(scope="function")
def dynamodb(aws_credentials):
    """DynamoDB mock fixture."""
    with mock_dynamodb():
        yield boto3.resource("dynamodb", region_name="us-east-1")


@pytest.fixture(scope="function")
def s3(aws_credentials):
    """S3 mock fixture."""
    with mock_s3():
        yield boto3.resource("s3", region_name="us-east-1")


@pytest.fixture(scope="function")
def billing_table(dynamodb):
    """Create a mock billing data table."""
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
    """Create a mock user info table."""
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
    """Create mock S3 buckets."""
    # Create raw files bucket
    s3.create_bucket(Bucket="billquestmiscommitstack-rawfilesbucket-nelmak")

    # Create user info bucket
    s3.create_bucket(Bucket="billquestmiscommitstack-user-access-bucket-nelmak")

    # Create website bucket
    s3.create_bucket(Bucket="billquestmiscommitstack-websitebucket-nelmak")

    return s3
