import re
import json
from email_validator import validate_email, EmailNotValidError
import dateparser
from datetime import datetime

def is_valid_name(name):
    return bool(re.match(r"^[A-Za-z\s]+$", name))

def is_valid_phone(phone):
    return bool(re.match(r"^\+?\d{7,15}$", phone))

def is_valid_email(email):
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False

def parse_date(date_str):
    parsed = dateparser.parse(date_str)
    if parsed:
        return parsed.strftime("%Y-%m-%d")
    return None

def save_appointment(data):
    with open("appointments.json", "a") as f:
        f.write(json.dumps(data) + "\n")
