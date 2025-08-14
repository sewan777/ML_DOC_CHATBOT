# 🤖 AI Document Chatbot with Appointment Booking

An intelligent Streamlit application that combines document-based question answering with conversational appointment booking capabilities. Upload documents to get AI-powered insights or seamlessly book appointments through natural conversation.

## ✨ Features

### 📄 Document Intelligence
- **PDF Upload & Processing**: Upload multiple PDF documents for analysis
- **Smart Q&A**: Ask questions about your uploaded documents using advanced AI
- **Vector Search**: Efficient document retrieval using FAISS vector storage
- **Context-Aware Responses**: Get accurate answers based on document content

### 📅 Appointment Booking
- **Conversational Interface**: Book appointments through natural language
- **Smart Form Handling**: AI extracts appointment details from conversation
- **Validation**: Automatic validation of names, emails, phone numbers, and dates
- **Flexible Scheduling**: Support for various date formats and natural language ("next Monday", "tomorrow", etc.)
- **Appointment Management**: View and manage scheduled appointments

### 🧠 AI-Powered Features
- **Google Gemini Integration**: Powered by Google's Generative AI
- **Contextual Memory**: Maintains conversation context for better interactions
- **Multi-Modal Responses**: Handles both document queries and appointment requests
- **Error Handling**: Graceful handling of invalid inputs and edge cases

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Google AI API key (for Gemini)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-document-chatbot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   GOOGLE_API_KEY=your_google_api_key_here
   ```

4. **Run the application**
   ```bash
   streamlit run main.py
   ```

5. **Access the application**
   Open your browser and navigate to `http://localhost:8501`

## 🔧 Configuration

### Environment Variables
- `GOOGLE_API_KEY`: Your Google AI API key (required)

### Getting Google AI API Key
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file

## 📁 Project Structure

```
.
├── main.py                 # Main Streamlit application
├── chatbot.py             # Document processing and Q&A logic
├── conversational_form.py # Form handling and validation
├── form_handler.py        # Appointment management
├── requirements.txt       # Python dependencies
├── appointments.json      # Stored appointments (auto-created)
├── sample_docs/          # Example PDF documents
│   ├── sample1.pdf
│   └── sample2.pdf
└── README.md             # This file
```

## 🎯 Usage

### Document Q&A
1. **Upload Documents**: Use the sidebar to upload one or more PDF files
2. **Ask Questions**: Type questions about your documents in the chat
3. **Get Insights**: Receive AI-powered answers based on document content

Example questions:
- "What are the main topics covered in this document?"
- "Can you summarize the key findings?"
- "What does it say about [specific topic]?"

### Appointment Booking
1. **Start Conversation**: Simply ask to book an appointment
2. **Provide Details**: The AI will guide you through providing necessary information
3. **Confirm**: Review and confirm your appointment details

Example phrases:
- "I'd like to book an appointment"
- "Can you schedule a meeting for me?"
- "I need to set up a call for next Monday at 2 PM"

### Managing Appointments
- View all scheduled appointments in the sidebar
- Appointments are automatically saved to `appointments.json`
- Each appointment includes name, email, phone, date, time, and any additional notes

## 🛠️ Technical Details

### Dependencies
- **Streamlit**: Web application framework
- **LangChain**: AI application development framework
- **Google Generative AI**: Large language model integration
- **FAISS**: Vector similarity search
- **PyPDF2**: PDF processing
- **email-validator**: Email validation
- **dateparser**: Natural language date parsing

### AI Models
- **Embeddings**: `models/embedding-001` (Google)
- **Chat Model**: `gemini-pro` (Google)

### Data Storage
- **Vector Store**: FAISS (in-memory)
- **Appointments**: JSON file storage
- **Session State**: Streamlit session management

## 🔒 Privacy & Security

- Documents are processed in-memory and not permanently stored
- Appointment data is stored locally in JSON format
- API keys should be kept secure and not committed to version control
- Consider implementing additional security measures for production use

## 🚨 Troubleshooting

### Common Issues

**"API key not found"**
- Ensure your `.env` file contains a valid `GOOGLE_API_KEY`
- Restart the application after adding the API key

**"No documents uploaded"**
- Upload at least one PDF document before asking questions
- Check that your PDF files are not corrupted

**"Invalid appointment details"**
- Ensure dates are in the future
- Use valid email format (e.g., user@example.com)
- Phone numbers should be 7-15 digits

### Error Messages
The application provides helpful error messages for:
- Invalid email addresses
- Malformed phone numbers
- Past dates for appointments
- Missing required information



## 🔮 Future Enhancements

- [ ] Support for more document formats (DOCX, TXT)
- [ ] Calendar integration
- [ ] Email notifications for appointments
- [ ] User authentication
- [ ] Database storage for appointments
- [ ] Advanced appointment management features
- [ ] Multi-language support

