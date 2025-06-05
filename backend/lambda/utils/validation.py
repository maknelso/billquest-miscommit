from typing import Dict, Any, List, Optional, Union, Callable
from .error_handler import ValidationError


def validate_required_params(
    params: Dict[str, Any], required_fields: List[str]
) -> None:
    """
    Validate that all required parameters are present

    Args:
        params: Dictionary of parameters to validate
        required_fields: List of required field names

    Raises:
        ValidationError: If any required field is missing
    """
    missing_fields = [field for field in required_fields if field not in params]

    if missing_fields:
        if len(missing_fields) == 1:
            raise ValidationError(f"Missing required parameter: {missing_fields[0]}")
        else:
            raise ValidationError(
                f"Missing required parameters: {', '.join(missing_fields)}"
            )


def validate_field_type(
    params: Dict[str, Any],
    field: str,
    expected_type: Union[type, tuple],
    allow_none: bool = False,
) -> None:
    """
    Validate that a field is of the expected type

    Args:
        params: Dictionary of parameters to validate
        field: Field name to validate
        expected_type: Expected type or tuple of types
        allow_none: Whether None is allowed

    Raises:
        ValidationError: If the field is not of the expected type
    """
    if field not in params:
        return

    value = params[field]

    if value is None and allow_none:
        return

    if not isinstance(value, expected_type):
        type_name = getattr(expected_type, "__name__", str(expected_type))
        raise ValidationError(
            f"Invalid type for {field}. Expected {type_name}, got {type(value).__name__}",
            {"field": field, "value": str(value)},
        )


def validate_field_format(
    params: Dict[str, Any],
    field: str,
    validator: Callable[[Any], bool],
    error_message: str,
    allow_none: bool = False,
) -> None:
    """
    Validate that a field matches a specific format using a validator function

    Args:
        params: Dictionary of parameters to validate
        field: Field name to validate
        validator: Function that returns True if the value is valid
        error_message: Error message to use if validation fails
        allow_none: Whether None is allowed

    Raises:
        ValidationError: If the field doesn't match the expected format
    """
    if field not in params:
        return

    value = params[field]

    if value is None and allow_none:
        return

    if not validator(value):
        raise ValidationError(error_message, {"field": field, "value": str(value)})
