import json
from decimal import Decimal
from typing import Any

from .cors_config import get_cors_headers


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal objects."""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)


def format_response(
    status_code: int = 200, body: Any = None, headers: dict[str, str] | None = None
) -> dict[str, Any]:
    """Format a standard API Gateway response

    Args:
        status_code: HTTP status code
        body: Response body (will be JSON serialized)
        headers: Additional headers to include

    Returns:
        API Gateway response object

    """
    # Get environment-specific CORS headers
    cors_headers = get_cors_headers()

    # Merge CORS headers with any provided headers
    response_headers = {**cors_headers, **(headers or {})}

    # Add content type if not specified
    if "Content-Type" not in response_headers:
        response_headers["Content-Type"] = "application/json"

    # Create the response
    response = {"statusCode": status_code, "headers": response_headers}

    # Add the body if provided
    if body is not None:
        response["body"] = json.dumps(body, cls=DecimalEncoder)

    return response


def format_success_response(
    data: Any,
    metadata: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Format a successful response with data and optional metadata

    Args:
        data: The main response data
        metadata: Optional metadata about the response
        headers: Additional headers to include

    Returns:
        API Gateway response object

    """
    response_body = {"data": data}

    if metadata:
        response_body["metadata"] = metadata

    return format_response(200, response_body, headers)


def format_csv_response(
    csv_content: str,
    filename: str = "data.csv",
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Format a response containing CSV data

    Args:
        csv_content: The CSV content as a string
        filename: The suggested filename for the download
        headers: Additional headers to include

    Returns:
        API Gateway response object

    """
    # CSV-specific headers
    csv_headers = {
        "Content-Type": "text/csv",
        "Content-Disposition": f"attachment; filename={filename}",
    }

    # Get environment-specific CORS headers
    cors_headers = get_cors_headers()

    # Merge all headers
    response_headers = {**cors_headers, **csv_headers, **(headers or {})}

    return {
        "statusCode": 200,
        "headers": response_headers,
        "body": csv_content,
        "isBase64Encoded": False,
    }
