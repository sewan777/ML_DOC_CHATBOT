import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Callable
from langchain.tools import BaseTool
from langchain.agents import Tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from conversational_form import ConversationalForm
import dateparser

class AppointmentTool(BaseTool):
    name = "appointment_scheduler"
    description = "Use this tool to schedule appointments when users request callbacks or meetings. It will guide them through a conversational form."
    
    def __init__(self):
        super().__init__()
        self.form = ConversationalForm()
    
    def _run(self, user_message: str) -> str:
        """Run the appointment scheduling tool"""
        result = self.form.process_message(user_message)
        
        if result.get("action") == "reset":
            self.form.reset()
            return "Let's start over. " + result["response"]
        
        return result["response"]
    
    def reset_form(self):
        """Reset the conversational form"""
        self.form.reset()
    
    def get_form_state(self):
        """Get current form state"""
        return self.form.get_state()
    
    def get_collected_info(self):
        """Get collected user information"""
        return self.form.get_collected_info()

class DateParserTool(BaseTool):
    name = "date_parser"
    description = "Parse natural language date expressions like 'next Monday', 'tomorrow', etc. into YYYY-MM-DD format"
    
    def _run(self, date_text: str) -> str:
        """Parse date from natural language"""
        try:
            parsed_date = dateparser.parse(date_text, settings={'PREFER_DATES_FROM': 'future'})
            if parsed_date:
                return parsed_date.strftime('%Y-%m-%d')
            else:
                return f"Could not parse date from: {date_text}"
        except Exception as e:
            return f"Error parsing date: {str(e)}"

class AppointmentLookupTool(BaseTool):
    name = "appointment_lookup"
    description = "Look up existing appointments by name, phone, or email"
    
    def _run(self, search_term: str) -> str:
        """Look up appointments"""
        try:
            appointments = []
            with open("appointments.json", "r") as f:
                for line in f:
                    if line.strip():
                        appointment = json.loads(line)
                        # Search in name, phone, or email
                        if (search_term.lower() in appointment.get('name', '').lower() or
                            search_term in appointment.get('phone', '') or
                            search_term.lower() in appointment.get('email', '').lower()):
                            appointments.append(appointment)
            
            if appointments:
                result = "Found appointments:\n"
                for i, apt in enumerate(appointments, 1):
                    result += f"{i}. {apt.get('name')} - {apt.get('appointment_date')} at {apt.get('appointment_time')}\n"
                return result
            else:
                return f"No appointments found for: {search_term}"
        except FileNotFoundError:
            return "No appointments file found"
        except Exception as e:
            return f"Error looking up appointments: {str(e)}"

class ValidatorTool(BaseTool):
    name = "input_validator"
    description = "Validate user inputs like email addresses, phone numbers, dates, etc."
    
    def _run(self, input_data: str) -> str:
        """Validate input data"""
        try:
            data = json.loads(input_data)
            validation_type = data.get('type')
            value = data.get('value')
            
            if validation_type == 'email':
                from email_validator import validate_email, EmailNotValidError
                try:
                    validate_email(value)
                    return "Valid email address"
                except EmailNotValidError:
                    return "Invalid email address"
            
            elif validation_type == 'phone':
                import re
                cleaned = re.sub(r'[^\d+]', '', value)
                if re.match(r'^\+?\d{7,15}$', cleaned):
                    return "Valid phone number"
                else:
                    return "Invalid phone number"
            
            elif validation_type == 'date':
                try:
                    date_obj = datetime.strptime(value, '%Y-%m-%d').date()
                    if date_obj >= datetime.now().date():
                        return "Valid date"
                    else:
                        return "Date is in the past"
                except ValueError:
                    return "Invalid date format"
            
            else:
                return f"Unknown validation type: {validation_type}"
        
        except json.JSONDecodeError:
            return "Invalid input format. Expected JSON with 'type' and 'value' fields"
        except Exception as e:
            return f"Validation error: {str(e)}"

class AvailabilityTool(BaseTool):
    name = "availability_checker"
    description = "Check availability for appointment scheduling based on date and time"
    
    def _run(self, datetime_str: str) -> str:
        """Check availability for given date and time"""
        try:
            # Parse the input
            data = json.loads(datetime_str)
            date = data.get('date')
            time = data.get('time')
            
            # Load existing appointments
            existing_appointments = []
            try:
                with open("appointments.json", "r") as f:
                    for line in f:
                        if line.strip():
                            appointment = json.loads(line)
                            existing_appointments.append(appointment)
            except FileNotFoundError:
                pass
            
            # Check for conflicts
            conflicts = [
                apt for apt in existing_appointments 
                if apt.get('appointment_date') == date and apt.get('appointment_time') == time
            ]
            
            if conflicts:
                return f"Time slot {date} at {time} is not available. Conflicting appointments: {len(conflicts)}"
            else:
                return f"Time slot {date} at {time} is available"
                
        except json.JSONDecodeError:
            return "Invalid input format. Expected JSON with 'date' and 'time' fields"
        except Exception as e:
            return f"Error checking availability: {str(e)}"

class ToolAgentsManager:
    def __init__(self, google_api_key: str):
        self.google_api_key = google_api_key
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.1,
            google_api_key=google_api_key,
            convert_system_message_to_human=True
        )
        
        # Initialize tools
        self.appointment_tool = AppointmentTool()
        self.tools = [
            self.appointment_tool,
            DateParserTool(),
            AppointmentLookupTool(),
            ValidatorTool(),
            AvailabilityTool()
        ]
        
        # Create agent
        self.agent = self._create_agent()
    
    def _create_agent(self):
        """Create the agent with tools"""
        prompt = PromptTemplate(
            input_variables=["tools", "tool_names", "input", "agent_scratchpad"],
            template="""
You are a helpful assistant that specializes in appointment scheduling and customer service.
You have access to the following tools:

{tools}

Tool names: {tool_names}

When a user asks to be called back or wants to schedule an appointment, use the appointment_scheduler tool.
When you need to parse dates from natural language, use the date_parser tool.
When you need to validate user inputs, use the input_validator tool.
When you need to check appointment availability, use the availability_checker tool.
When you need to look up existing appointments, use the appointment_lookup tool.

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Question: {input}
{agent_scratchpad}
"""
        )
        
        agent = create_react_agent(self.llm, self.tools, prompt)
        return AgentExecutor(agent=agent, tools=self.tools, verbose=True, handle_parsing_errors=True)
    
    def process_message(self, user_message: str) -> Dict[str, Any]:
        """Process user message through the agent"""
        try:
            # Check if we're in the middle of a form conversation
            if self.appointment_tool.get_form_state() != "idle":
                # Continue with the conversational form
                form_result = self.appointment_tool._run(user_message)
                return {
                    "response": form_result,
                    "state": self.appointment_tool.get_form_state(),
                    "collected_info": self.appointment_tool.get_collected_info()
                }
            
            # Use agent for general processing
            result = self.agent.invoke({"input": user_message})
            
            return {
                "response": result.get("output", "I'm sorry, I couldn't process that request."),
                "state": self.appointment_tool.get_form_state(),
                "collected_info": self.appointment_tool.get_collected_info()
            }
            
        except Exception as e:
            return {
                "response": f"I encountered an error: {str(e)}",
                "state": "error",
                "collected_info": {}
            }
    
    def reset_appointment_form(self):
        """Reset the appointment form"""
        self.appointment_tool.reset_form()
    
    def get_appointments_summary(self) -> str:
        """Get summary of all appointments"""
        try:
            appointments = []
            with open("appointments.json", "r") as f:
                for line in f:
                    if line.strip():
                        appointments.append(json.loads(line))
            
            if not appointments:
                return "No appointments scheduled."
            
            summary = f"Total appointments: {len(appointments)}\n\n"
            for i, apt in enumerate(appointments, 1):
                summary += f"{i}. {apt.get('name')} - {apt.get('appointment_date')} at {apt.get('appointment_time')}\n"
                summary += f"   Phone: {apt.get('phone')}, Email: {apt.get('email')}\n"
                summary += f"   Reason: {apt.get('reason', 'Not specified')}\n\n"
            
            return summary
            
        except FileNotFoundError:
            return "No appointments file found."
        except Exception as e:
            return f"Error retrieving appointments: {str(e)}"

# Helper functions for integration
def create_tool_agents_manager(google_api_key: str) -> ToolAgentsManager:
    """Factory function to create ToolAgentsManager"""
    return ToolAgentsManager(google_api_key)

def validate_user_input(input_type: str, value: str) -> Dict[str, Any]:
    """Standalone validation function"""
    validator = ValidatorTool()
    input_data = json.dumps({"type": input_type, "value": value})
    result = validator._run(input_data)
    return {"valid": "Valid" in result, "message": result}

def parse_natural_date(date_text: str) -> str:
    """Standalone date parsing function"""
    parser = DateParserTool()
    return parser._run(date_text)

def check_appointment_availability(date: str, time: str) -> Dict[str, Any]:
    """Standalone availability check function"""
    checker = AvailabilityTool()
    input_data = json.dumps({"date": date, "time": time})
    result = checker._run(input_data)
    return {"available": "available" in result.lower(), "message": result}