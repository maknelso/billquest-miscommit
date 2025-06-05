import json
import logging
import time
from typing import Dict, Any, Optional, Callable
from functools import wraps

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def log_event(event: Dict[str, Any], context: Any = None, level: str = "INFO") -> None:
    """
    Log an API Gateway event with relevant information

    Args:
        event: API Gateway event
        context: Lambda context
        level: Logging level (INFO, WARNING, ERROR)
    """
    # Extract useful information from the event
    log_data = {
        "timestamp": time.time(),
        "path": event.get("path", ""),
        "httpMethod": event.get("httpMethod", ""),
        "queryStringParameters": event.get("queryStringParameters", {}),
        "requestContext": {
            "requestId": event.get("requestContext", {}).get("requestId", ""),
            "stage": event.get("requestContext", {}).get("stage", ""),
            "identity": {
                "sourceIp": event.get("requestContext", {})
                .get("identity", {})
                .get("sourceIp", "")
            },
        },
    }

    # Add context information if available
    if context:
        log_data["context"] = {
            "functionName": getattr(context, "function_name", ""),
            "functionVersion": getattr(context, "function_version", ""),
            "awsRequestId": getattr(context, "aws_request_id", ""),
            "remainingTimeMs": getattr(
                context, "get_remaining_time_in_millis", lambda: 0
            )(),
        }

    # Log at the appropriate level
    log_message = json.dumps(log_data)
    if level == "ERROR":
        logger.error(log_message)
    elif level == "WARNING":
        logger.warning(log_message)
    else:
        logger.info(log_message)


def log_lambda_execution(func: Callable) -> Callable:
    """
    Decorator to log Lambda execution details

    Args:
        func: Lambda handler function

    Returns:
        Wrapped function with logging
    """

    @wraps(func)
    def wrapper(event, context):
        start_time = time.time()
        request_id = getattr(context, "aws_request_id", "unknown")

        # Log the incoming request
        logger.info(
            json.dumps(
                {
                    "message": "Lambda execution started",
                    "requestId": request_id,
                    "functionName": getattr(context, "function_name", ""),
                    "event": {
                        "path": event.get("path", ""),
                        "httpMethod": event.get("httpMethod", ""),
                        "queryStringParameters": event.get("queryStringParameters", {}),
                    },
                }
            )
        )

        try:
            # Execute the handler
            response = func(event, context)

            # Log the successful completion
            execution_time = time.time() - start_time
            logger.info(
                json.dumps(
                    {
                        "message": "Lambda execution completed",
                        "requestId": request_id,
                        "executionTimeMs": int(execution_time * 1000),
                        "statusCode": response.get("statusCode", 200),
                    }
                )
            )

            return response

        except Exception as e:
            # Log the error
            execution_time = time.time() - start_time
            logger.error(
                json.dumps(
                    {
                        "message": "Lambda execution failed",
                        "requestId": request_id,
                        "executionTimeMs": int(execution_time * 1000),
                        "error": str(e),
                        "errorType": e.__class__.__name__,
                    }
                )
            )

            # Re-raise the exception
            raise

    return wrapper
