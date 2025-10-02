
import re
from django.core.validators import URLValidator

from django.core.exceptions import ValidationError


def validate_no_special_symbols(value):
    """
    Validator to ensure the value contains no special signs or symbols.
    Allows only letters, numbers, spaces, hyphens, and dots.
    """
    if not re.match(r'^[\w\s.-]+$', str(value)):
        raise ValidationError(
            "Value must not contain special signs or symbols.")


def validate_array_of_urls(value):
    """
    Validator to ensure the value is a list of valid URLs.
    """
    if not isinstance(value, list):
        raise ValidationError("Value must be a list of URLs.")
    url_validator = URLValidator()
    for url in value:
        try:
            url_validator(url)
        except ValidationError:
            raise ValidationError(f"'{url}' is not a valid URL.")
