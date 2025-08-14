import re
import json
from email_validator import validate_email, EmailNotValidError
import dateparser
from datetime import datetime, timedelta

def is_valid_name(name):
    """Validate name with enhanced regex patterns."""
    if not name or len(name.strip()) < 2 or len(name.strip()) > 50:
        return False
    return bool(re.match(r"^[A-Za-z\s]+$", name.strip()))

def is_valid_phone(phone):
    """Validate phone number with international format support."""
    # Remove spaces and dashes for validation
    clean_phone = re.sub(r'[\s-]', '', phone)
    # Allow + prefix and 7-15 digits
    return bool(re.match(r"^\+?\d{7,15}$", clean_phone))

def is_valid_email(email):
    """Validate email using email-validator library."""
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False

def parse_date(date_str):
    """Parse date with natural language support and validation."""
    try:
        # Use dateparser to handle natural language dates
        parsed = dateparser.parse(
            date_str, 
            settings={
                'PREFER_DATES_FROM': 'future',
                'RETURN_AS_TIMEZONE_AWARE': False
            }
        )
        
        if parsed:
            # Ensure the date is in the future
            if parsed.date() <= datetime.now().date():
                # If parsed date is today or past, try to get next occurrence
                if 'next' not in date_str.lower() and 'tomorrow' not in date_str.lower():
                    # Add a week for weekday names without "next"
                    parsed = parsed + timedelta(days=7)
            
            return parsed.strftime("%Y-%m-%d")
        return None
    except Exception:
        return None

def validate_date_format(date_str):
    """Validate if date string can be parsed correctly."""
    return parse_date(date_str) is not None

def save_appointment(data):
    """Save appointment data to JSON file with enhanced error handling."""
    try:
        # Ensure the data has a timestamp
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now().isoformat()
        
        # Validate required fields
        required_fields = ['name', 'phone', 'email', 'appointment_date', 'purpose']
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValueError(f"Missing required field: {field}")
        
        # Save to file
        with open("appointments.json", "a", encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
        
        return True, "Appointment saved successfully!"
        
    except Exception as e:
        return False, f"Error saving appointment: {str(e)}"

def load_appointments():
    """Load all appointments from JSON file."""
    appointments = []
    try:
        with open("appointments.json", "r", encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    appointments.append(json.loads(line.strip()))
    except FileNotFoundError:
        # File doesn't exist yet, return empty list
        pass
    except Exception as e:
        print(f"Error loading appointments: {e}")
    
    return appointments

def get_appointments_by_date(target_date):
    """Get appointments for a specific date."""
    appointments = load_appointments()
    target_appointments = []
    
    for appointment in appointments:
        if appointment.get('appointment_date') == target_date:
            target_appointments.append(appointment)
    
    return target_appointments

def format_appointment_summary(appointment_data):
    """Format appointment data for display."""
    summary = f"""
**Appointment Details:**
📅 **Date:** {appointment_data.get('appointment_date', 'Not specified')}
👤 **Name:** {appointment_data.get('name', 'Not specified')}
📞 **Phone:** {appointment_data.get('phone', 'Not specified')}
📧 **Email:** {appointment_data.get('email', 'Not specified')}
📝 **Purpose:** {appointment_data.get('purpose', 'Not specified')}
🕒 **Booked:** {appointment_data.get('timestamp', 'Not specified')}
"""
    return summary

def validate_appointment_data(data):
    """Comprehensive validation of appointment data."""
    errors = []
    
    # Validate name
    if not data.get('name') or not is_valid_name(data['name']):
        errors.append("Invalid name (2-50 characters, letters and spaces only)")
    
    # Validate phone
    if not data.get('phone') or not is_valid_phone(data['phone']):
        errors.append("Invalid phone number (7-15 digits, optional + prefix)")
    
    # Validate email
    if not data.get('email') or not is_valid_email(data['email']):
        errors.append("Invalid email address")
    
    # Validate date
    if not data.get('appointment_date') or not validate_date_format(data['appointment_date']):
        errors.append("Invalid appointment date")
    
    # Validate purpose
    if not data.get('purpose') or len(data['purpose'].strip()) < 2:
        errors.append("Purpose must be at least 2 characters")
    
    return len(errors) == 0, errors

class AppointmentManager:
    """Class to manage appointment booking process."""
    
    def __init__(self):
        self.current_appointment = {}
        self.step = 'start'
    
    def reset(self):
        """Reset the appointment manager."""
        self.current_appointment = {}
        self.step = 'start'
    
    def process_step(self, user_input, current_step):
        """Process user input for a specific step."""
        user_input = user_input.strip()
        
        if current_step == 'name':
            if is_valid_name(user_input):
                return True, user_input, "Valid name provided"
            else:
                return False, None, "Invalid name. Please provide 2-50 characters, letters and spaces only."
        
        elif current_step == 'phone':
            if is_valid_phone(user_input):
                return True, user_input, "Valid phone number provided"
            else:
                return False, None, "Invalid phone number. Please provide 7-15 digits with optional + prefix."
        
        elif current_step == 'email':
            if is_valid_email(user_input):
                return True, user_input, "Valid email address provided"
            else:
                return False, None, "Invalid email address. Please provide a valid email."
        
        elif current_step == 'date':
            parsed_date = parse_date(user_input)
            if parsed_date:
                return True, parsed_date, f"Date parsed as: {parsed_date}"
            else:
                return False, None, "Invalid date. Try formats like 'next Monday', 'tomorrow', or '2024-12-25'."
        
        elif current_step == 'purpose':
            if len(user_input) >= 2:
                return True, user_input, "Purpose recorded"
            else:
                return False, None, "Please provide a purpose (at least 2 characters)."
        
        return False, None, "Unknown step"
    
    def book_appointment(self, appointment_data):
        """Book an appointment with validation."""
        is_valid, errors = validate_appointment_data(appointment_data)
        
        if not is_valid:
            return False, f"Validation errors: {'; '.join(errors)}"
        
        success, message = save_appointment(appointment_data)
        return success, message

# Example usage and testing
if __name__ == "__main__":
    # Test validation functions
    print("Testing validation functions:")
    
    # Test names
    test_names = ["John Doe", "A", "John123", "Very Long Name That Exceeds Fifty Characters Limit"]
    for name in test_names:
        print(f"Name '{name}': {is_valid_name(name)}")
    
    # Test phones
    test_phones = ["+1234567890", "1234567890", "+91 98765 43210", "123", "abcd123"]
    for phone in test_phones:
        print(f"Phone '{phone}': {is_valid_phone(phone)}")
    
    # Test emails
    test_emails = ["test@example.com", "invalid.email", "user@domain.co.uk"]
    for email in test_emails:
        print(f"Email '{email}': {is_valid_email(email)}")
    
    # Test dates
    test_dates = ["next Monday", "tomorrow", "2024-12-25", "invalid date", "next Friday"]
    for date in test_dates:
        parsed = parse_date(date)
        print(f"Date '{date}': {parsed}")
    
    # Test appointment manager
    manager = AppointmentManager()
    
    sample_appointment = {
        'name': 'John Doe',
        'phone': '+1234567890',
        'email': 'john@example.com',
        'appointment_date': '2024-12-25',
        'purpose': 'Business consultation'
    }
    
    success, message = manager.book_appointment(sample_appointment)
    print(f"Appointment booking: {success}, Message: {message}")
    
    if success:
        print(format_appointment_summary(sample_appointment))