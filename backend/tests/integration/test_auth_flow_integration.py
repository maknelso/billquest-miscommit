"""
Integration tests for authentication flow.

This module contains integration tests that verify the Cognito authentication flow
works correctly. These tests create actual users, authenticate them, and verify
that the tokens can be used to access protected API endpoints.

Tests are skipped unless the ENVIRONMENT variable is set to "test" to prevent
accidental execution against production resources.
"""

import os
import time
import uuid
import pytest
import boto3
import requests
import json
from botocore.exceptions import ClientError

# Skip tests if not in a test environment
pytestmark = pytest.mark.skipif(
    os.environ.get("ENVIRONMENT") != "test",
    reason="Integration tests should only run in test environment",
)

# Get Cognito configuration from environment variables or use defaults for testing
USER_POOL_ID = os.environ.get("USER_POOL_ID", "us-east-1_0TZqMTtTP")
CLIENT_ID = os.environ.get("CLIENT_ID", "3ak8em99qdsivhg2qka1b3p62f")

# Get API endpoints from environment or use defaults for testing
PROTECTED_API_ENDPOINT = os.environ.get(
    "PROTECTED_API_ENDPOINT",
    "https://6f3ntv3qq8.execute-api.us-east-1.amazonaws.com/prod/protected",
)

# Test data with unique values to avoid conflicts
TEST_USERNAME = f"testuser-{uuid.uuid4()}"
TEST_EMAIL = f"test-{uuid.uuid4()}@example.com"
TEST_PASSWORD = "Test@password123"  # Must meet Cognito complexity requirements


@pytest.fixture
def cognito_idp_client():
    """
    Create a Cognito Identity Provider client for test operations.

    Returns:
        boto3.client: Configured Cognito IDP client
    """
    return boto3.client("cognito-idp", region_name="us-east-1")


@pytest.fixture
def test_user(cognito_idp_client):
    """
    Create a test user in Cognito and clean up after the test.

    This fixture:
    1. Creates a test user in Cognito
    2. Yields the username and password
    3. Deletes the user after the test

    Args:
        cognito_idp_client: Fixture providing the Cognito IDP client

    Returns:
        dict: User credentials (username, email, password)
    """
    # Create the user
    try:
        cognito_idp_client.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username=TEST_USERNAME,
            TemporaryPassword=TEST_PASSWORD,
            UserAttributes=[
                {"Name": "email", "Value": TEST_EMAIL},
                {"Name": "email_verified", "Value": "true"},
            ],
            MessageAction="SUPPRESS",  # Don't send emails
        )

        # Set the permanent password
        cognito_idp_client.admin_set_user_password(
            UserPoolId=USER_POOL_ID,
            Username=TEST_USERNAME,
            Password=TEST_PASSWORD,
            Permanent=True,
        )

        # Yield the user credentials
        yield {
            "username": TEST_USERNAME,
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
        }
    finally:
        # Clean up - delete the user
        try:
            cognito_idp_client.admin_delete_user(
                UserPoolId=USER_POOL_ID,
                Username=TEST_USERNAME,
            )
        except ClientError:
            pass  # User might already be deleted or not exist


def test_user_authentication_flow(cognito_idp_client, test_user):
    """
    Test the complete user authentication flow.

    This test:
    1. Authenticates a user with Cognito
    2. Gets ID and access tokens
    3. Uses the tokens to access a protected API endpoint
    4. Verifies successful access

    Args:
        cognito_idp_client: Fixture providing the Cognito IDP client
        test_user: Fixture providing test user credentials
    """
    # Authenticate the user and get tokens
    auth_response = cognito_idp_client.admin_initiate_auth(
        UserPoolId=USER_POOL_ID,
        ClientId=CLIENT_ID,
        AuthFlow="ADMIN_NO_SRP_AUTH",
        AuthParameters={
            "USERNAME": test_user["username"],
            "PASSWORD": test_user["password"],
        },
    )

    # Verify authentication response contains tokens
    assert "AuthenticationResult" in auth_response
    assert "IdToken" in auth_response["AuthenticationResult"]
    assert "AccessToken" in auth_response["AuthenticationResult"]

    # Extract tokens
    id_token = auth_response["AuthenticationResult"]["IdToken"]
    access_token = auth_response["AuthenticationResult"]["AccessToken"]

    # Use the token to access a protected API endpoint
    headers = {"Authorization": f"Bearer {id_token}"}
    response = requests.get(PROTECTED_API_ENDPOINT, headers=headers)

    # Verify successful access
    assert response.status_code == 200

    # Verify token information
    user_info = cognito_idp_client.get_user(AccessToken=access_token)

    # Verify user attributes
    user_attributes = {
        attr["Name"]: attr["Value"] for attr in user_info["UserAttributes"]
    }
    assert user_attributes["email"] == test_user["email"]


def test_unauthorized_access():
    """
    Test that protected endpoints reject unauthorized access.

    This test:
    1. Attempts to access a protected API endpoint without authentication
    2. Verifies that access is denied
    """
    # Attempt to access protected endpoint without auth
    response = requests.get(PROTECTED_API_ENDPOINT)

    # Verify access is denied
    assert response.status_code in [401, 403]

    # Attempt to access with invalid token
    headers = {"Authorization": "Bearer invalid_token"}
    response = requests.get(PROTECTED_API_ENDPOINT, headers=headers)

    # Verify access is denied
    assert response.status_code in [401, 403]
