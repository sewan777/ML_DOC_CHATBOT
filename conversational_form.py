import re
import json
import dateparser
from datetime import datetime, timedelta
from email_validator import validate_email, EmailNotValidError
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum

class FormState(Enum):
    IDLE = "idle"
    COLLECTING_NAME = "collecting_name"
    COLLECTING_PHONE = "collecting_phone"
    COLLECTING_EMAIL = "collecting_email"
    COLLECTING_DATE = "collecting_date"
    COLLECTING_TIME = "collecting_time"
    COLLECTING_REASON = "collecting_reason"
    CONFIRMING = "confirming"
    COMPLETED = "completed"

@dataclass
class UserInfo:
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    appointment_date: Optional[str] = None
    appointment_time: Optional[str] = None
    reason: Optional[str] = None

class ConversationalForm:
    def __init__(self):
        self.state = FormState.IDLE
        self.user_info = UserInfo()
        self.conversation_history = []
        self.retry_count = 0
        self.max_retries = 3
        
    def reset(self):
        """Reset the form to initial state"""
        self.state = FormState.IDLE
        self.user_info = UserInfo()
        self.conversation_history = []
        self.retry_count = 0
    
    def is_requesting_callback(self, message: str) -> bool:
        """Check if user is requesting a callback or appointment"""
        callback_keywords = [
            'call me', 'call back', 'callback', 'phone me', 'ring me',
            'book appointment', 'schedule appointment', 'make appointment',
            'meet', 'consultation', 'discuss', 'talk to someone'
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in callback_keywords)
    
    def extract_info_from_message(self, message: str) -> Dict[str, Any]:
        """Extract any user information that might be present in the message"""
        extracted = {}
        
        # Extract email using regex
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, message)
        if emails:
            extracted['email'] = emails[0]
        
        # Extract phone number
        phone_pattern = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phones = re.findall(phone_pattern, message)
        if phones:
            # Clean phone number
            phone = re.sub(r'[^\d+]', '', phones[0])
            extracted['phone'] = phone
        
        # Extract name (if message starts with "I'm" or "My name is")
        name_patterns = [
            r"(?:i'm|i am|my name is|call me)\s+([a-zA-Z\s]+)",
            r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
        ]
        for pattern in name_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if self.is_valid_name(name):
                    extracted['name'] = name
                break
        
        # Extract date/time information
        date_info = self.parse_date_from_message(message)
        if date_info:
            extracted.update(date_info)
        
        return extracted
    
    def parse_date_from_message(self, message: str) -> Dict[str, str]:
        """Parse date and time information from natural language"""
        result = {}
        
        # Common relative date expressions
        relative_dates = {
            'today': 0,
            'tomorrow': 1,
            'day after tomorrow': 2,
            'next monday': self._days_until_weekday(0),
            'next tuesday': self._days_until_weekday(1),
            'next wednesday': self._days_until_weekday(2),
            'next thursday': self._days_until_weekday(3),
            'next friday': self._days_until_weekday(4),
            'next saturday': self._days_until_weekday(5),
            'next sunday': self._days_until_weekday(6),
        }
        
        message_lower = message.lower()
        
        # Check for relative dates
        for phrase, days_ahead in relative_dates.items():
            if phrase in message_lower:
                target_date = datetime.now() + timedelta(days=days_ahead)
                result['appointment_date'] = target_date.strftime('%Y-%m-%d')
                break
        
        # Try dateparser for more complex expressions
        if not result.get('appointment_date'):
            parsed_date = dateparser.parse(message, settings={'PREFER_DATES_FROM': 'future'})
            if parsed_date and parsed_date.date() >= datetime.now().date():
                result['appointment_date'] = parsed_date.strftime('%Y-%m-%d')
        
        # Extract time information
        time_patterns = [
            r'(\d{1,2}):(\d{2})\s*(am|pm)',
            r'(\d{1,2})\s*(am|pm)',
            r'(\d{1,2}):(\d{2})',
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, message_lower)
            if match:
                if len(match.groups()) == 3:  # HH:MM AM/PM
                    hour, minute, period = match.groups()
                    hour = int(hour)
                    if period == 'pm' and hour != 12:
                        hour += 12
                    elif period == 'am' and hour == 12:
                        hour = 0
                    result['appointment_time'] = f"{hour:02d}:{minute}"
                elif len(match.groups()) == 2 and match.groups()[1] in ['am', 'pm']:  # H AM/PM
                    hour, period = match.groups()
                    hour = int(hour)
                    if period == 'pm' and hour != 12:
                        hour += 12
                    elif period == 'am' and hour == 12:
                        hour = 0
                    result['appointment_time'] = f"{hour:02d}:00"
                elif len(match.groups()) == 2:  # HH:MM
                    hour, minute = match.groups()
                    result['appointment_time'] = f"{int(hour):02d}:{minute}"
                break
        
        return result
    
    def _days_until_weekday(self, target_weekday: int) -> int:
        """Calculate days until next occurrence of target weekday (0=Monday, 6=Sunday)"""
        today = datetime.now()
        days_ahead = target_weekday - today.weekday()
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        return days_ahead
    
    def is_valid_name(self, name: str) -> bool:
        """Validate name format"""
        if not name or len(name.strip()) < 2:
            return False
        return bool(re.match(r"^[A-Za-z\s'-]+$", name.strip()))
    
    def is_valid_phone(self, phone: str) -> bool:
        """Validate phone number format"""
        if not phone:
            return False
        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', phone)
        # Check if it's a valid length and format
        return bool(re.match(r'^\+?\d{7,15}$', cleaned))
    
    def is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        try:
            validate_email(email)
            return True
        except EmailNotValidError:
            return False
    
    def is_valid_date(self, date_str: str) -> bool:
        """Validate date format and ensure it's not in the past"""
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            return date_obj >= datetime.now().date()
        except ValueError:
            return False
    
    def is_valid_time(self, time_str: str) -> bool:
        """Validate time format"""
        try:
            datetime.strptime(time_str, '%H:%M')
            return True
        except ValueError:
            return False
    
    def process_message(self, message: str) -> Dict[str, Any]:
        """Process a user message and return response with next state"""
        self.conversation_history.append({"user": message, "timestamp": datetime.now().isoformat()})
        
        # Extract any information from the message
        extracted_info = self.extract_info_from_message(message)
        
        # Update user info with extracted information
        for key, value in extracted_info.items():
            if hasattr(self.user_info, key) and getattr(self.user_info, key) is None:
                setattr(self.user_info, key, value)
        
        # Handle state transitions
        if self.state == FormState.IDLE:
            if self.is_requesting_callback(message):
                self.state = FormState.COLLECTING_NAME
                return self._get_next_question()
            else:
                return {"response": "I understand you have a question. Would you like me to call you back to discuss this further?", "state": "idle"}
        
        elif self.state == FormState.COLLECTING_NAME:
            return self._handle_name_collection(message, extracted_info)
        
        elif self.state == FormState.COLLECTING_PHONE:
            return self._handle_phone_collection(message, extracted_info)
        
        elif self.state == FormState.COLLECTING_EMAIL:
            return self._handle_email_collection(message, extracted_info)
        
        elif self.state == FormState.COLLECTING_DATE:
            return self._handle_date_collection(message, extracted_info)
        
        elif self.state == FormState.COLLECTING_TIME:
            return self._handle_time_collection(message, extracted_info)
        
        elif self.state == FormState.COLLECTING_REASON:
            return self._handle_reason_collection(message)
        
        elif self.state == FormState.CONFIRMING:
            return self._handle_confirmation(message)
        
        return {"response": "I'm not sure how to help with that. Could you please clarify?", "state": self.state.value}
    
    def _handle_name_collection(self, message: str, extracted_info: Dict) -> Dict[str, Any]:
        """Handle name collection state"""
        if self.user_info.name and self.is_valid_name(self.user_info.name):
            self.state = FormState.COLLECTING_PHONE
            self.retry_count = 0
            return self._get_next_question()
        
        # Try to extract name from current message if not already extracted
        if not extracted_info.get('name'):
            # If the message looks like a name
            if self.is_valid_name(message.strip()):
                self.user_info.name = message.strip()
                self.state = FormState.COLLECTING_PHONE
                self.retry_count = 0
                return self._get_next_question()
        
        self.retry_count += 1
        if self.retry_count >= self.max_retries:
            return {"response": "I'm having trouble getting your name. Let's try again from the beginning.", "state": "error", "action": "reset"}
        
        return {"response": "Could you please tell me your full name?", "state": self.state.value}
    
    def _handle_phone_collection(self, message: str, extracted_info: Dict) -> Dict[str, Any]:
        """Handle phone number collection state"""
        phone = extracted_info.get('phone') or message.strip()
        
        if self.is_valid_phone(phone):
            self.user_info.phone = phone
            self.state = FormState.COLLECTING_EMAIL
            self.retry_count = 0
            return self._get_next_question()
        
        self.retry_count += 1
        if self.retry_count >= self.max_retries:
            return {"response": "I'm having trouble getting your phone number. Let's try again from the beginning.", "state": "error", "action": "reset"}
        
        return {"response": "Please provide a valid phone number (e.g., +1234567890 or 123-456-7890):", "state": self.state.value}
    
    def _handle_email_collection(self, message: str, extracted_info: Dict) -> Dict[str, Any]:
        """Handle email collection state"""
        email = extracted_info.get('email') or message.strip()
        
        if self.is_valid_email(email):
            self.user_info.email = email
            self.state = FormState.COLLECTING_DATE
            self.retry_count = 0
            return self._get_next_question()
        
        self.retry_count += 1
        if self.retry_count >= self.max_retries:
            return {"response": "I'm having trouble getting your email. Let's try again from the beginning.", "state": "error", "action": "reset"}
        
        return {"response": "Please provide a valid email address (e.g., your.email@example.com):", "state": self.state.value}
    
    def _handle_date_collection(self, message: str, extracted_info: Dict) -> Dict[str, Any]:
        """Handle date collection state"""
        if extracted_info.get('appointment_date'):
            if self.is_valid_date(extracted_info['appointment_date']):
                self.user_info.appointment_date = extracted_info['appointment_date']
                self.state = FormState.COLLECTING_TIME
                self.retry_count = 0
                return self._get_next_question()
        
        self.retry_count += 1
        if self.retry_count >= self.max_retries:
            return {"response": "I'm having trouble understanding the date. Let's try again from the beginning.", "state": "error", "action": "reset"}
        
        return {"response": "When would you like to schedule the appointment? You can say things like 'tomorrow', 'next Monday', or a specific date:", "state": self.state.value}
    
    def _handle_time_collection(self, message: str, extracted_info: Dict) -> Dict[str, Any]:
        """Handle time collection state"""
        time_str = extracted_info.get('appointment_time')
        
        if not time_str:
            # Try to parse time from message
            time_patterns = [
                r'(\d{1,2}):(\d{2})\s*(am|pm)',
                r'(\d{1,2})\s*(am|pm)',
            ]
            
            for pattern in time_patterns:
                match = re.search(pattern, message.lower())
                if match:
                    if len(match.groups()) == 3:
                        hour, minute, period = match.groups()
                        hour = int(hour)
                        if period == 'pm' and hour != 12:
                            hour += 12
                        elif period == 'am' and hour == 12:
                            hour = 0
                        time_str = f"{hour:02d}:{minute}"
                    elif len(match.groups()) == 2:
                        hour, period = match.groups()
                        hour = int(hour)
                        if period == 'pm' and hour != 12:
                            hour += 12
                        elif period == 'am' and hour == 12:
                            hour = 0
                        time_str = f"{hour:02d}:00"
                    break
        
        if time_str and self.is_valid_time(time_str):
            self.user_info.appointment_time = time_str
            self.state = FormState.COLLECTING_REASON
            self.retry_count = 0
            return self._get_next_question()
        
        self.retry_count += 1
        if self.retry_count >= self.max_retries:
            return {"response": "I'm having trouble understanding the time. Let's try again from the beginning.", "state": "error", "action": "reset"}
        
        return {"response": "What time would you prefer? Please specify in format like '2:30 PM' or '14:30':", "state": self.state.value}
    
    def _handle_reason_collection(self, message: str) -> Dict[str, Any]:
        """Handle reason collection state"""
        if message.strip():
            self.user_info.reason = message.strip()
            self.state = FormState.CONFIRMING
            self.retry_count = 0
            return self._get_confirmation_message()
        
        return {"response": "Could you please tell me briefly what you'd like to discuss during the call?", "state": self.state.value}
    
    def _handle_confirmation(self, message: str) -> Dict[str, Any]:
        """Handle confirmation state"""
        message_lower = message.lower().strip()
        
        if message_lower in ['yes', 'y', 'confirm', 'correct', 'ok', 'okay']:
            # Save the appointment
            appointment_data = asdict(self.user_info)
            appointment_data['created_at'] = datetime.now().isoformat()
            appointment_data['status'] = 'confirmed'
            
            self._save_appointment(appointment_data)
            self.state = FormState.COMPLETED
            
            return {
                "response": f"Perfect! Your appointment has been scheduled for {self.user_info.appointment_date} at {self.user_info.appointment_time}. We'll call you at {self.user_info.phone}. You should also receive a confirmation email at {self.user_info.email}.",
                "state": "completed",
                "appointment_data": appointment_data
            }
        
        elif message_lower in ['no', 'n', 'incorrect', 'wrong']:
            return {"response": "What would you like to change? Please let me know which information needs to be updated.", "state": "editing"}
        
        else:
            return {"response": "Please confirm if the information is correct by saying 'yes' or 'no':", "state": self.state.value}
    
    def _get_next_question(self) -> Dict[str, Any]:
        """Get the next question based on current state"""
        questions = {
            FormState.COLLECTING_NAME: "I'd be happy to arrange a callback for you! Could you please tell me your full name?",
            FormState.COLLECTING_PHONE: f"Thank you, {self.user_info.name}! What's the best phone number to reach you?",
            FormState.COLLECTING_EMAIL: "Great! Could you also provide your email address?",
            FormState.COLLECTING_DATE: "When would you like us to call you? You can say things like 'tomorrow', 'next Monday', or a specific date:",
            FormState.COLLECTING_TIME: "What time would be convenient for you?",
            FormState.COLLECTING_REASON: "Finally, could you briefly tell me what you'd like to discuss during the call?"
        }
        
        return {"response": questions.get(self.state, ""), "state": self.state.value}
    
    def _get_confirmation_message(self) -> Dict[str, Any]:
        """Generate confirmation message with all collected information"""
        formatted_date = datetime.strptime(self.user_info.appointment_date, '%Y-%m-%d').strftime('%A, %B %d, %Y')
        formatted_time = datetime.strptime(self.user_info.appointment_time, '%H:%M').strftime('%I:%M %p')
        
        confirmation_text = f"""
Let me confirm your appointment details:

📅 **Name:** {self.user_info.name}
📞 **Phone:** {self.user_info.phone}
📧 **Email:** {self.user_info.email}
📅 **Date:** {formatted_date}
🕐 **Time:** {formatted_time}
💭 **Discussion Topic:** {self.user_info.reason}

Is this information correct?
        """.strip()
        
        return {"response": confirmation_text, "state": self.state.value}
    
    def _save_appointment(self, appointment_data: Dict[str, Any]):
        """Save appointment data to file"""
        try:
            with open("appointments.json", "a") as f:
                f.write(json.dumps(appointment_data) + "\n")
        except Exception as e:
            print(f"Error saving appointment: {e}")
    
    def get_state(self) -> str:
        """Get current form state"""
        return self.state.value
    
    def get_collected_info(self) -> Dict[str, Any]:
        """Get currently collected information"""
        return asdict(self.user_info)