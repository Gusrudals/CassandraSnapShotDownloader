"""Input validation functions."""

from datetime import date
from config.settings import MAX_DATE_RANGE_DAYS


def validate_date_range(start_date: date, end_date: date) -> tuple[bool, str]:
    """
    Validate date range is logical and reasonable.

    Args:
        start_date: Beginning of date range
        end_date: End of date range

    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    if start_date > end_date:
        return (False, "End date must be after start date")

    if (end_date - start_date).days > MAX_DATE_RANGE_DAYS:
        return (False, f"Date range cannot exceed {MAX_DATE_RANGE_DAYS} days. Please narrow your search.")

    if end_date > date.today():
        return (False, "End date cannot be in the future")

    return (True, "")


def validate_eqpid(eqpid: str) -> tuple[bool, str]:
    """
    Validate equipment ID is not empty.

    Args:
        eqpid: Equipment identifier

    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    if not eqpid or not eqpid.strip():
        return (False, "Equipment ID is required")

    return (True, "")
