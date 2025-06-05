# Shared Utilities

This directory contains shared utility modules used across Lambda functions.

## Modules

### error_handler.py

Provides standardized error handling and response formatting for Lambda functions.

**Key Components:**
- Custom exception classes for different error types
- Error response formatting with consistent structure
- Detailed error logging with context

**Usage:**
```python
from utils.error_handler import handle_error, ValidationError, ResourceNotFoundError

# Raise a validation error
if not email:
    raise ValidationError("Missing 'email' parameter")

# Handle errors in catch blocks
except Exception as e:
    return handle_error(e, {"context": "additional info"})
```

### response_formatter.py

Provides standardized response formatting for Lambda functions.

**Key Components:**
- JSON response formatting with consistent structure
- CSV response formatting for file downloads
- Decimal handling for DynamoDB values

**Usage:**
```python
from utils.response_formatter import format_success_response, format_csv_response

# Return a successful JSON response
return format_success_response({"data": items})

# Return a CSV file
return format_csv_response(csv_content, "data.csv")
```

### validation.py

Provides input validation utilities for Lambda functions.

**Key Components:**
- Parameter validation
- Type checking
- Format validation

**Usage:**
```python
from utils.validation import validate_required_params

# Validate required parameters
validate_required_params(params, ["email", "accountId"])
```

### logging_utils.py

Provides enhanced logging utilities for Lambda functions.

**Key Components:**
- Structured logging with context
- Lambda execution logging decorator
- Event logging

**Usage:**
```python
from utils.logging_utils import log_event, log_lambda_execution

# Log an event
log_event(event, context)

# Decorate Lambda handler for automatic logging
@log_lambda_execution
def lambda_handler(event, context):
    # ...
```