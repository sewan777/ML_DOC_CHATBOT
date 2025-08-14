import re
import json
from datetime import datetime
from email_validator import validate_email, EmailNotValidError
import dateparser

def validate_email_address(email):
    """Enhanced email validation using email-validator library."""
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False

def validate_phone(phone):
    """Enhanced phone validation with better regex."""
    # Remove spaces and dashes for validation
    clean_phone = re.sub(r'[\s-]', '', phone)
    return re.match(r"^\+?\d{7,15}$", clean_phone)

def validate_name(name):
    """Validate name with improved regex."""
    return bool(re.match(r"^[A-Za-z\s]{2,50}$", name.strip()))

def parse_date(date_str):
    """Parse date with natural language support."""
    try:
        # Handle relative dates like "next Monday", "tomorrow", etc.
        parsed = dateparser.parse(date_str, settings={'PREFER_DATES_FROM': 'future'})
        if parsed:
            return parsed.strftime("%Y-%m-%d")
        return None
    except:
        return None

class ConversationalForm:
    def __init__(self):
        self.reset_form()
    
    def reset_form(self):
        """Reset form to initial state."""
        self.user_info = {
            'name': None,
            'phone': None, 
            'email': None,
            'appointment_date': None,
            'purpose': None
        }
        self.current_step = 'start'
        self.form_active = False
    
    def is_appointment_related(self, query):
        """Check if the query is related to booking appointments."""
        appointment_keywords = [
            'book appointment', 'schedule', 'call me', 'contact me', 
            'appointment', 'meeting', 'book', 'schedule meeting',
            'call', 'phone', 'contact', 'reach out'
        ]
        return any(keyword in query.lower() for keyword in appointment_keywords)
    
    def process_form_input(self, user_input):
        """Process user input based on current form step."""
        user_input = user_input.strip()
        
        if self.current_step == 'name':
            if validate_name(user_input):
                self.user_info['name'] = user_input
                self.current_step = 'phone'
                return "Great! Now, please provide your phone number (with country code if international):"
            else:
                return "Please enter a valid name (only letters and spaces, 2-50 characters):"
        
        elif self.current_step == 'phone':
            if validate_phone(user_input):
                self.user_info['phone'] = user_input
                self.current_step = 'email'
                return "Perfect! Now, please provide your email address:"
            else:
                return "Please enter a valid phone number (7-15 digits, optionally starting with +):"
        
        elif self.current_step == 'email':
            if validate_email_address(user_input):
                self.user_info['email'] = user_input
                self.current_step = 'date'
                return "Excellent! When would you like to schedule the appointment? (e.g., 'next Monday', 'tomorrow', '2024-12-25', etc.):"
            else:
                return "Please enter a valid email address:"
        
        elif self.current_step == 'date':
            parsed_date = parse_date(user_input)
            if parsed_date:
                self.user_info['appointment_date'] = parsed_date
                self.current_step = 'purpose'
                return f"Great! I've scheduled your appointment for {parsed_date}. Finally, what's the purpose of your appointment?"
            else:
                return "Please provide a valid date (e.g., 'next Monday', 'tomorrow', '2024-12-25'):"
        
        elif self.current_step == 'purpose':
            self.user_info['purpose'] = user_input
            self.current_step = 'complete'
            return self.complete_appointment()
        
        return "I didn't understand that. Please try again."
    
    def complete_appointment(self):
        """Complete the appointment booking process."""
        # Save appointment to file
        appointment_data = {
            'timestamp': datetime.now().isoformat(),
            **self.user_info
        }
        
        try:
            with open("appointments.json", "a") as f:
                f.write(json.dumps(appointment_data) + "\n")
        except Exception as e:
            return f"Error saving appointment: {e}"
        
        summary = f"""
**Appointment Booked Successfully! 📅**

**Details:**
- **Name:** {self.user_info['name']}
- **Phone:** {self.user_info['phone']}
- **Email:** {self.user_info['email']}
- **Date:** {self.user_info['appointment_date']}
- **Purpose:** {self.user_info['purpose']}

We'll contact you soon to confirm the appointment details. Is there anything else I can help you with?
"""
        self.form_active = False
        return summary
    
    def start_booking(self):
        """Start the appointment booking process."""
        self.reset_form()
        self.form_active = True
        self.current_step = 'name'
        return "I'd be happy to help you book an appointment! Let's start by collecting some information. What's your full name?"

def collect_user_info():
    """Enhanced user info collection with better validation."""
    user_info = {}
    
    # Collect Name
    while True:
        name = input("Please enter your name: ").strip()
        if validate_name(name):
            user_info['name'] = name
            break
        print("Invalid name. Please enter only letters and spaces (2-50 characters).")
    
    # Collect Phone
    while True:
        phone = input("Please enter your phone number (with country code): ").strip()
        if validate_phone(phone):
            user_info['phone'] = phone
            break
        print("Invalid phone number. Please enter 7-15 digits, optionally starting with +.")
    
    # Collect Email
    while True:
        email = input("Please enter your email: ").strip()
        if validate_email_address(email):
            user_info['email'] = email
            break
        print("Invalid email address. Please try again.")
    
    # Collect Date
    while True:
        date_input = input("Enter appointment date (e.g., 'next Monday', 'tomorrow', '2024-12-25'): ").strip()
        parsed_date = parse_date(date_input)
        if parsed_date:
            user_info['appointment_date'] = parsed_date
            break
        print("Invalid date format. Please try again.")
    
    # Collect Purpose
    user_info['purpose'] = input("What's the purpose of your appointment?: ").strip()
    
    return user_info

# Example usage
if __name__ == "__main__":
    user_info = collect_user_info()
    print("Collected Info:", user_info)
    
    # Save to file
    appointment_data = {
        'timestamp': datetime.now().isoformat(),
        **user_info
    }
    
    with open("appointments.json", "a") as f:
        f.write(json.dumps(appointment_data) + "\n")
    
    print("Appointment saved successfully!")