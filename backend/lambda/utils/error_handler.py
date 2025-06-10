"""Error handling utilities for Lambda functions.

This module provides a standardized way to handle errors in Lambda functions,
including custom exception types and a unified error response format for API Gateway.
It ensures consistent error handling, logging, and CORS headers across all Lambda functions.
"""

import json
import logging
import traceback
from typing import Any

from .cors_config import get_cors_headers

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class LambdaError(Exception):
    """Base exception class for Lambda errors.

    All custom error types should inherit from this class.
    It provides common attributes like status_code and error_type
    that are used to generate appropriate API responses.

    Attributes:
        status_code (int): HTTP status code to return (defaults to 500)
        error_type (str): Error type identifier for API responses
        message (str): Human-readable error message
        details (dict): Additional error context information

    """

    status_code = 500
    error_type = "InternalServerError"

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        """Initialize a new LambdaError.

        Args:
            message: Human-readable error message
            details: Additional context about the error (optional)

        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(LambdaError):
    """Exception for input validation errors.

    Raised when user input fails validation checks.
    Returns HTTP 400 Bad Request.
    """

    status_code = 400
    error_type = "ValidationError"


class ResourceNotFoundError(LambdaError):
    """Exception for resource not found errors.

    Raised when a requested resource doesn't exist.
    Returns HTTP 404 Not Found.
    """

    status_code = 404
    error_type = "ResourceNotFoundError"


class AuthorizationError(LambdaError):
    """Exception for authorization errors.

    Raised when a user doesn't have permission to access a resource.
    Returns HTTP 403 Forbidden.
    """

    status_code = 403
    error_type = "AuthorizationError"


def handle_error(e: Exception, context: dict[str, Any] = None) -> dict[str, Any]:
    """Handle exceptions and return appropriate API Gateway response.

    This function processes exceptions, logs error details, and formats
    a standardized API Gateway response with proper status code and CORS headers.

    Args:
        e: The exception to handle
        context: Additional context information like request ID, user info, etc.

    Returns:
        API Gateway response object with appropriate status code, headers, and error details

    """
    # Initialize context if not provided
    context = context or {}

    # Extract error details based on exception type
    if isinstance(e, LambdaError):
        # Use attributes from our custom error classes
        status_code = e.status_code
        error_type = e.error_type
        message = e.message
        details = e.details
    else:
        # Default handling for standard Python exceptions
        status_code = 500
        error_type = "InternalServerError"
        message = str(e) or "An unexpected error occurred"
        details = {}

    # Prepare structured log data
    log_data = {
        "error_type": error_type,
        "message": message,
        "details": details,
        "context": context,
        "traceback": traceback.format_exc(),
    }

    # Log at appropriate level based on severity
    if status_code >= 500:
        # Server errors are logged as errors
        logger.error(json.dumps(log_data))
    else:
        # Client errors are logged as warnings
        logger.warning(json.dumps(log_data))

    # Get environment-specific CORS headers
    cors_headers = get_cors_headers()

    # Prepare API Gateway response with standardized format
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
