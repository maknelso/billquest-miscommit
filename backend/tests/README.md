# Tests

This directory contains tests for the BillQuest application.

## Directory Structure

- `unit/`: Unit tests for individual components
  - `test_bill_quest_miscommit_stack.py`: Tests for the CDK stack

## Running Tests

To run the tests:

```bash
# From the project root
cd backend
pytest
```

## Test Coverage

The current test suite covers:

- Basic CDK stack validation

## Adding Tests

### Unit Tests

Unit tests should be added for:

- Lambda functions
- Utility functions
- CDK constructs

### Integration Tests

Integration tests should be added to test:

- API endpoints
- End-to-end workflows
- Cross-component interactions

## Best Practices

1. Each test file should focus on a single component
2. Use mocks for external dependencies
3. Tests should be independent and not rely on the state from other tests
4. Use descriptive test names that explain what is being tested
5. Include both positive and negative test cases