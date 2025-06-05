import json
import logging
import traceback
from typing import Dict, Any, Optional

from .cors_config import get_cors_headers

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class LambdaError(Exception):
    """Base exception class for Lambda errors"""

    status_code = 500
    error_type = "InternalServerError"

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(LambdaError):
    """Exception for input validation errors"""

    status_code = 400
    error_type = "ValidationError"


class ResourceNotFoundError(LambdaError):
    """Exception for resource not found errors"""

    status_code = 404
    error_type = "ResourceNotFoundError"


class AuthorizationError(LambdaError):
    """Exception for authorization errors"""

    status_code = 403
    error_type = "AuthorizationError"


def handle_error(e: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Handle exceptions and return appropriate API Gateway response

    Args:
        e: The exception to handle
        context: Additional context information

    Returns:
        API Gateway response object
    """
    context = context or {}

    # Get error details based on exception type
    if isinstance(e, LambdaError):
        status_code = e.status_code
        error_type = e.error_type
        message = e.message
        details = e.details
    else:
        status_code = 500
        error_type = "InternalServerError"
        message = str(e) or "An unexpected error occurred"
        details = {}

    # Log the error with context
    log_data = {
        "error_type": error_type,
        "message": message,
        "details": details,
        "context": context,
        "traceback": traceback.format_exc(),
    }

    if status_code >= 500:
        logger.error(json.dumps(log_data))
    else:
        logger.warning(json.dumps(log_data))

    # Get environment-specific CORS headers
    cors_headers = get_cors_headers()

    # Prepare API Gateway response
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json", **cors_headers},
        "body": json.dumps(
            {
                "error": error_type,
                "message": message,
                "requestId": context.get("aws_request_id", ""),
            }
        ),
    }
