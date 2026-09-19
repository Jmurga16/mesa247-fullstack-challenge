import phonenumbers
from fastapi.exceptions import RequestValidationError


def field_error(field: str, message: str):
    raise RequestValidationError([
        {"type": "value_error", "loc": ("body", field), "msg": message}
    ])


def normalize_phone(value: str, region: str) -> str:
    try:
        number = phonenumbers.parse(value, region)
        if not phonenumbers.is_valid_number(number) or number.extension:
            raise ValueError()
        return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)
    except (phonenumbers.NumberParseException, ValueError):
        field_error("phone", "Introduce un teléfono válido con su código de país.")
