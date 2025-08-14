# ML Document Chatbot with Conversational Appointment Booking

A sophisticated Streamlit-based chatbot that combines document Q&A capabilities with intelligent appointment scheduling through conversational forms. Built with LangChain, Google Gemini, and advanced tool-agents architecture.

## 🌟 Features

### 📄 Document Q&A
- Upload and process PDF/text documents
- Ask questions about document content
- Get AI-powered answers with source citations
- Vector-based retrieval using FAISS
- Powered by Google Gemini LLM

### 📅 Conversational Appointment Booking
- **Natural Language Processing**: Request appointments using phrases like "call me back", "schedule a meeting"
- **Smart Information Extraction**: Automatically extract names, emails, phone numbers from user messages
- **Intelligent Date Parsing**: Understand natural language dates like "next Monday", "tomorrow at 2 PM"
- **Multi-step Form Validation**: Validate emails, phone numbers, and dates with retry logic
- **Conversational Flow Management**: Seamless conversation flow with state management

### 🤖 Tool-Agents Integration
- **Appointment Scheduler Tool**: Guides users through booking process
- **Date Parser Tool**: Converts natural language to YYYY-MM-DD format
- **Validation Tool**: Validates user inputs (email, phone, date)
- **Availability Checker**: Checks for scheduling conflicts
- **Appointment Lookup**: Search existing appointments

### 🔄 Hybrid Mode
- Intelligently routes between document Q&A and appointment booking
- Seamless switching based on user intent
- Context-aware responses with suggestions

## 🚀 Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd ml-chatbot-appointment
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
Create a `.env` file in the project root:
```env
GOOGLE_API_KEY=your_google_api_key_here
```

To get a Google API key:
- Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
- Create a new API key
- Copy it to your `.env` file

4. **Run the application**
```bash
streamlit run main.py
```

## 📁 Project Structure

```
├── main.py                 # Main Streamlit application
├── conversational_form.py  # Conversational form system
├── tool_agents.py         # Tool-agents integration
├── chatbot.py            # Document Q&A functionality
├── form_handler.py       # Basic form utilities
├── demo_test.py          # Demo and testing script
├── requirements.txt      # Python dependencies
├── appointments.json     # Appointment storage
├── sample_docs/          # Sample documents
│   ├── sample1.pdf
│   └── sample2.pdf
└── README.md            # This file
```

## 🎯 Usage Examples

### Document Q&A Mode
```
User: "What is machine learning?"
Bot: Based on the uploaded documents, machine learning is...
```

### Appointment Booking
```
User: "I'd like to schedule a call"
Bot: "I'd be happy to arrange a callback for you! Could you please tell me your full name?"
User: "My name is John Smith"
Bot: "Thank you, John Smith! What's the best phone number to reach you?"
User: "+1234567890"
Bot: "Great! Could you also provide your email address?"
User: "john@example.com"
Bot: "When would you like us to call you? You can say things like 'tomorrow', 'next Monday', or a specific date:"
User: "next Tuesday at 3 PM"
Bot: "Finally, could you briefly tell me what you'd like to discuss during the call?"
User: "I want to learn about your AI services"
Bot: [Shows confirmation with all details]
```

### Natural Language Date Examples
- "tomorrow" → 2024-01-16
- "next Monday" → 2024-01-22
- "December 25th" → 2024-12-25
- "in 3 days" → 2024-01-18
- "next Friday at 2 PM" → 2024-01-19 14:00

## 🏗️ Architecture

### Conversational Form System
- **State Management**: Uses enum-based states for form progression
- **Information Extraction**: Regex and NLP-based extraction from user messages
- **Validation Pipeline**: Multi-layer validation with retry mechanisms
- **Error Handling**: Graceful error handling with user-friendly messages

### Tool-Agents Integration
- **BaseTool Implementation**: Custom LangChain tools for specific functions
- **Agent Executor**: ReAct agent pattern for intelligent tool selection
- **Context Awareness**: Maintains conversation context across tool usage

### Smart Routing
```python
# Hybrid mode logic
if is_appointment_request or in_appointment_flow:
    route_to_appointment_system()
else:
    route_to_document_qa()
```

## 🛠️ Key Components

### ConversationalForm Class
```python
class ConversationalForm:
    - FormState enum for state management
    - UserInfo dataclass for data storage
    - Intelligent information extraction
    - Natural language date parsing
    - Comprehensive input validation
```

### ToolAgentsManager Class
```python
class ToolAgentsManager:
    - Integration with Google Gemini LLM
    - Multiple specialized tools
    - Agent-based decision making
    - Error handling and recovery
```

### Validation Features
- **Email**: RFC-compliant email validation
- **Phone**: International phone number formats
- **Date**: Future date validation with natural language support
- **Name**: Character validation with special character support

## 🔧 Configuration

### Chat Modes
1. **Document Q&A**: Pure document question-answering
2. **Appointment Booking**: Dedicated appointment scheduling
3. **Hybrid Mode**: Intelligent routing (recommended)

### Appointment Settings
- Maximum retry attempts: 3
- Supported date formats: Natural language + standard formats
- Time formats: 12-hour (AM/PM) and 24-hour
- Phone formats: International and domestic

## 📊 Data Storage

Appointments are stored in JSON format in `appointments.json`:
```json
{
  "name": "John Smith",
  "phone": "+1234567890",
  "email": "john@example.com",
  "appointment_date": "2024-01-22",
  "appointment_time": "15:00",
  "reason": "Discuss AI services",
  "created_at": "2024-01-15T10:30:00",
  "status": "confirmed"
}
```

## 🧪 Testing

Run the demo script to test functionality:
```bash
python demo_test.py
```

This will test:
- Conversational form flow
- Natural language date parsing
- Input validation
- Tool-agents integration

## 🚀 Deployment

For production deployment:

1. **Environment Setup**
```bash
export GOOGLE_API_KEY=your_api_key
```

2. **Streamlit Cloud**
- Push to GitHub
- Connect to Streamlit Cloud
- Add secrets in dashboard

3. **Docker Deployment**
```dockerfile
FROM python:3.9-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["streamlit", "run", "main.py"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests for new functionality
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

For issues or questions:
1. Check the demo script output for debugging
2. Verify your Google API key is valid
3. Ensure all dependencies are installed
4. Check the Streamlit logs for errors

## 🔮 Future Enhancements

- [ ] Calendar integration (Google Calendar, Outlook)
- [ ] SMS/Email notifications
- [ ] Multi-language support
- [ ] Voice input/output
- [ ] Advanced scheduling logic (business hours, time zones)
- [ ] Integration with CRM systems
- [ ] Analytics dashboard
- [ ] Custom form templates