import os

import pytest
import requests

# Skip tests if not in a test environment
pytestmark = pytest.mark.skipif(
    os.environ.get("ENVIRONMENT") != "test",
    reason="Integration tests should only run in test environment",
)

# Get API endpoints from environment or use defaults for testing
QUERY_API_ENDPOINT = os.environ.get(
    "QUERY_API_ENDPOINT",
    "https://6f3ntv3qq8.execute-api.us-east-1.amazonaws.com/prod/query",
)
USER_ACCOUNTS_API_ENDPOINT = os.environ.get(
    "USER_ACCOUNTS_API_ENDPOINT",
    "https://saplj0po57.execute-api.us-east-1.amazonaws.com/prod/user-accounts",
)

# Test data
TEST_ACCOUNT_ID = "EUINFR25-266134"
TEST_EMAIL = "test@example.com"


@pytest.fixture
def auth_token():
    """Get authentication token for API requests.
    In a real test, this would authenticate with Cognito.
    """
    # This is a placeholder - in a real test, you would get a token from Cognito
    return "test-token"


def test_query_endpoint_returns_200(auth_token):
    """Test that the query endpoint returns a 200 status code."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    params = {"queryType": "account", "accountId": TEST_ACCOUNT_ID}

    # This test is just a placeholder and would be skipped in actual runs
    # unless ENVIRONMENT=test is set
    response = requests.get(QUERY_API_ENDPOINT, headers=headers, params=params)

    assert response.status_code == 200
    data = response.json()
    assert "items" in data


def test_user_accounts_endpoint_returns_user_data(auth_token):
    """Test that the user accounts endpoint returns user data."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    params = {"email": TEST_EMAIL}

    # This test is just a placeholder and would be skipped in actual runs
    # unless ENVIRONMENT=test is set
    response = requests.get(USER_ACCOUNTS_API_ENDPOINT, headers=headers, params=params)

    assert response.status_code == 200
    data = response.json()
    assert "email" in data
    assert "payer_account_ids" in data
