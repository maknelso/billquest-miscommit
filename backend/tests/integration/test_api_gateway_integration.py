"""
Integration tests for BillQuest API Gateway endpoints.

This module contains integration tests that verify the deployed API Gateway endpoints
are functioning correctly. These tests make actual HTTP requests to the deployed APIs
and verify the responses, testing the integration between API Gateway, Lambda functions,
and DynamoDB.

Tests are skipped unless the ENVIRONMENT variable is set to "test" to prevent
accidental execution against production endpoints.
"""

import os
import pytest
import requests

# Skip tests if not in a test environment to prevent accidental execution
# against production endpoints during regular test runs
pytestmark = pytest.mark.skipif(
    os.environ.get("ENVIRONMENT") != "test",
    reason="Integration tests should only run in test environment",
)

# Get API endpoints from environment variables or use defaults for testing
# In a CI/CD pipeline, these would be set to the actual deployed endpoints
QUERY_API_ENDPOINT = os.environ.get(
    "QUERY_API_ENDPOINT",
    "https://6f3ntv3qq8.execute-api.us-east-1.amazonaws.com/prod/query",
)
USER_ACCOUNTS_API_ENDPOINT = os.environ.get(
    "USER_ACCOUNTS_API_ENDPOINT",
    "https://saplj0po57.execute-api.us-east-1.amazonaws.com/prod/user-accounts",
)

# Test data - in a real test environment, these would be valid test accounts
# that exist in the test database
TEST_ACCOUNT_ID = "EUINFR25-266134"
TEST_EMAIL = "test@example.com"


@pytest.fixture
def auth_token():
    """
    Provide an authentication token for API requests.

    In a real test environment, this would authenticate with Cognito and
    return a valid JWT token. For now, it returns a placeholder value.

    Returns:
        str: Authentication token to use in request headers
    """
    # This is a placeholder - in a real test, you would get a token from Cognito
    return "test-token"


def test_query_endpoint_returns_200(auth_token):
    """
    Test that the query endpoint returns billing data successfully.

    This test verifies that:
    1. The query endpoint is accessible
    2. It accepts account ID queries
    3. It returns a 200 status code
    4. The response contains billing data items

    Args:
        auth_token: Fixture providing the authentication token
    """
    # Set up authentication header as would be required in production
    headers = {"Authorization": f"Bearer {auth_token}"}

    # Query parameters for the request - using a test account ID
    params = {"queryType": "account", "accountId": TEST_ACCOUNT_ID}

    # Make an actual HTTP request to the deployed API endpoint
    # This test is just a placeholder and would be skipped in actual runs
    # unless ENVIRONMENT=test is set
    response = requests.get(QUERY_API_ENDPOINT, headers=headers, params=params)

    # Verify the response meets our expectations
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


def test_user_accounts_endpoint_returns_user_data(auth_token):
    """
    Test that the user accounts endpoint returns user account mappings.

    This test verifies that:
    1. The user-accounts endpoint is accessible
    2. It accepts email queries
    3. It returns a 200 status code
    4. The response contains the expected user data structure

    Args:
        auth_token: Fixture providing the authentication token
    """
    # Set up authentication header as would be required in production
    headers = {"Authorization": f"Bearer {auth_token}"}

    # Query parameters for the request - using a test email
    params = {"email": TEST_EMAIL}

    # Make an actual HTTP request to the deployed API endpoint
    # This test is just a placeholder and would be skipped in actual runs
    # unless ENVIRONMENT=test is set
    response = requests.get(USER_ACCOUNTS_API_ENDPOINT, headers=headers, params=params)

    # Verify the response meets our expectations
    assert response.status_code == 200
    data = response.json()
    assert "email" in data
    assert "payer_account_ids" in data
