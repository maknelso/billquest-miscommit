# End-to-End Tests

This directory contains end-to-end (E2E) tests for the BillQuest application.

## Purpose

E2E tests verify that the entire application works correctly from the user's perspective. These tests simulate real user interactions and validate complete workflows.

## Test Structure

Each test file should focus on a specific user workflow:

- `test_user_authentication.py`: Tests for user signup, login, and logout
- `test_data_query.py`: Tests for querying billing data
- `test_user_access.py`: Tests for user access to account IDs

## Running Tests

To run the E2E tests:

```bash
# From the project root
cd backend
pytest tests/e2e
```

## Writing E2E Tests

When writing E2E tests:

1. Use a browser automation tool like Selenium or Playwright
2. Test complete user workflows from start to finish
3. Validate both UI elements and backend state
4. Clean up test data after tests complete
5. Use test accounts and data that won't affect production