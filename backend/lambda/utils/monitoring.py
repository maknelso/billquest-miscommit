import logging
import os
import time

import boto3

# Configure logging
logger = logging.getLogger()

# Check if we're running in AWS Lambda
IN_LAMBDA = os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is not None

# Initialize CloudWatch client if in Lambda
if IN_LAMBDA:
    try:
        cloudwatch = boto3.client("cloudwatch")
    except Exception as e:
        logger.warning(f"Failed to initialize CloudWatch client: {str(e)}")
        cloudwatch = None
else:
    cloudwatch = None


def put_metric(
    namespace: str,
    metric_name: str,
    value: int | float,
    unit: str = "Count",
    dimensions: list[dict[str, str]] | None = None,
) -> bool:
    """Put a metric to CloudWatch

    Args:
        namespace: CloudWatch namespace
        metric_name: Metric name
        value: Metric value
        unit: Metric unit
        dimensions: Metric dimensions

    Returns:
        True if successful, False otherwise

    """
    if not cloudwatch:
        logger.debug(
            f"CloudWatch client not available, logging metric: {namespace}.{metric_name}={value}{unit}"
        )
        return False

    try:
        # Format dimensions for CloudWatch
        formatted_dimensions = []
        if dimensions:
            for dim in dimensions:
                for name, value in dim.items():
                    formatted_dimensions.append({"Name": name, "Value": value})

        # Put metric data
        response = cloudwatch.put_metric_data(
            Namespace=namespace,
            MetricData=[
                {
                    "MetricName": metric_name,
                    "Value": value,
                    "Unit": unit,
                    "Dimensions": formatted_dimensions,
                }
            ],
        )
        return True
    except Exception as e:
        logger.warning(f"Failed to put metric {namespace}.{metric_name}: {str(e)}")
        return False


def track_latency(func_name: str, duration_ms: float, success: bool = True) -> None:
    """Track function latency

    Args:
        func_name: Function name
        duration_ms: Duration in milliseconds
        success: Whether the function executed successfully

    """
    # Get function name from environment if not provided
    if not func_name and IN_LAMBDA:
        func_name = os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "unknown")

    # Put metrics
    namespace = "BillQuest/Lambda"

    # Track overall latency
    put_metric(
        namespace=namespace,
        metric_name="Latency",
        value=duration_ms,
        unit="Milliseconds",
        dimensions=[
            {"FunctionName": func_name},
            {"Success": "True" if success else "False"},
        ],
    )

    # Track success/failure count
    put_metric(
        namespace=namespace,
        metric_name="Invocations",
        value=1,
        unit="Count",
        dimensions=[
            {"FunctionName": func_name},
            {"Success": "True" if success else "False"},
        ],
    )


def track_business_metric(
    category: str,
    metric_name: str,
    value: int | float = 1,
    unit: str = "Count",
    dimensions: dict[str, str] | None = None,
) -> None:
    """Track a business metric

    Args:
        category: Metric category
        metric_name: Metric name
        value: Metric value
        unit: Metric unit
        dimensions: Additional dimensions

    """
    # Format dimensions
    formatted_dimensions = []
    if dimensions:
        formatted_dimensions = [{"Name": k, "Value": v} for k, v in dimensions.items()]

    # Add category dimension
    formatted_dimensions.append({"Name": "Category", "Value": category})

    # Put metric
    put_metric(
        namespace="BillQuest/Business",
        metric_name=metric_name,
        value=value,
        unit=unit,
        dimensions=formatted_dimensions,
    )


def track_error(
    error_type: str, function_name: str | None = None, count: int = 1
) -> None:
    """Track an error

    Args:
        error_type: Error type
        function_name: Function name
        count: Error count

    """
    # Get function name from environment if not provided
    if not function_name and IN_LAMBDA:
        function_name = os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "unknown")

    # Put metric
    put_metric(
        namespace="BillQuest/Errors",
        metric_name="ErrorCount",
        value=count,
        unit="Count",
        dimensions=[
            {"ErrorType": error_type},
            {"FunctionName": function_name or "unknown"},
        ],
    )


class LatencyTracker:
    """Context manager for tracking function latency"""

    def __init__(self, name: str):
        self.name = name
        self.start_time = None
        self.success = True

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000
            self.success = exc_type is None
            track_latency(self.name, duration_ms, self.success)

            # If there was an exception, track it as an error
            if exc_type:
                track_error(exc_type.__name__, self.name)

        # Don't suppress exceptions
        return False
