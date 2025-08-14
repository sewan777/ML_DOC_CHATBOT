import streamlit as st
import os
from dotenv import load_dotenv
from chatbot import load_docs, build_qa_chain, build_agent_with_tools
from conversational_form import ConversationalForm
from form_handler import AppointmentManager, load_appointments, format_appointment_summary
from langchain.docstore.document import Document

# Load environment variables
load_dotenv()

st.set_page_config(page_title="AI Document Chatbot with Appointment Booking", page_icon="🤖", layout="wide")

st.title("🤖 AI Document Chatbot with Appointment Booking")
st.markdown("Upload documents to chat about them, or book an appointment by asking me to call you!")

# Initialize session state
if 'form_handler' not in st.session_state:
    st.session_state.form_handler = ConversationalForm()

if 'appointment_manager' not in st.session_state:
    st.session_state.appointment_manager = AppointmentManager()

if 'messages' not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant", 
        "content": """Hello! I'm your AI assistant. I can help you with:

📄 **Document Questions** - Upload documents and ask me anything about them
📅 **Appointment Booking** - Just say "book an appointment" or "call me"

What can I help you with today?"""
    })

if 'agent' not in st.session_state:
    st.session_state.agent = None

if 'docs_loaded' not in st.session_state:
    st.session_state.docs_loaded = False

# Sidebar for file upload and appointment management
with st.sidebar:
    st.header("📁 Document Upload")
    uploaded_files = st.file_uploader(
        "Upload your documents", 
        type=["pdf", "txt"], 
        accept_multiple_files=True,
        help="Upload PDF or text files to chat about their content"
    )
    
    # Process uploaded files
    docs = []
    if uploaded_files:
        with st.spinner("Processing documents..."):
            try:
                docs = load_docs(uploaded_files)
                st.success(f"✅ Loaded {len(docs)} document chunks!")
                
                # Build agent with tools
                agent = build_agent_with_tools(docs, st.session_state.form_handler)
                st.session_state.agent = agent
                st.session_state.docs_loaded = True
                
                st.info("🤖 Agent ready! You can now ask questions or book appointments.")
                
            except Exception as e:
                st.error(f"❌ Error processing documents: {str(e)}")
                st.session_state.docs_loaded = False
    else:
        if not st.session_state.docs_loaded:
            st.info("📤 Upload documents to enable document-based Q&A")
    
    # Appointment Status
    st.header("📅 Appointment Status")
    
    if st.session_state.form_handler.form_active:
        st.info(f"**Current Step:** {st.session_state.form_handler.current_step}")
        
        # Show progress
        progress_steps = ['name', 'phone', 'email', 'date', 'purpose']
        current_index = progress_steps.index(st.session_state.form_handler.current_step) if st.session_state.form_handler.current_step in progress_steps else 0
        progress = (current_index + 1) / len(progress_steps)
        st.progress(progress)
        
        # Show collected info
        user_info = st.session_state.form_handler.user_info
        if user_info['name']:
            st.write(f"✅ **Name:** {user_info['name']}")
        if user_info['phone']:
            st.write(f"✅ **Phone:** {user_info['phone']}")
        if user_info['email']:
            st.write(f"✅ **Email:** {user_info['email']}")
        if user_info['appointment_date']:
            st.write(f"✅ **Date:** {user_info['appointment_date']}")
    else:
        st.write("No active appointment booking")
    
    # Show recent appointments
    st.header("📋 Recent Appointments")
    try:
        recent_appointments = load_appointments()[-3:]  # Show last 3
        if recent_appointments:
            for i, appointment in enumerate(reversed(recent_appointments)):
                with st.expander(f"Appointment {len(recent_appointments)-i}"):
                    st.write(f"**Name:** {appointment.get('name', 'N/A')}")
                    st.write(f"**Date:** {appointment.get('appointment_date', 'N/A')}")
                    st.write(f"**Purpose:** {appointment.get('purpose', 'N/A')}")
        else:
            st.write("No appointments yet")
    except Exception as e:
        st.write(f"Error loading appointments: {e}")

# Main chat interface
st.header("💬 Chat Interface")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Helper function to check if query is appointment related
def is_appointment_related(query):
    appointment_keywords = [
        'book appointment', 'schedule', 'call me', 'contact me', 
        'appointment', 'meeting', 'book', 'schedule meeting',
        'call', 'phone', 'contact', 'reach out'
    ]
    return any(keyword in query.lower() for keyword in appointment_keywords)

# Chat input
if prompt := st.chat_input("Ask me anything about your documents or say 'book an appointment'"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = ""
                
                # Check if we're in the middle of form filling
                if st.session_state.form_handler.form_active and st.session_state.form_handler.current_step != 'start':
                    response = st.session_state.form_handler.process_form_input(prompt)
                
                # Check if user wants to book appointment
                elif is_appointment_related(prompt):
                    response = st.session_state.form_handler.start_booking()
                
                # Use agent for document queries (if available and documents loaded)
                elif st.session_state.agent and st.session_state.docs_loaded:
                    try:
                        response = st.session_state.agent.run(prompt)
                    except Exception as agent_error:
                        st.error(f"Agent error: {str(agent_error)}")
                        # Fallback to basic QA if agent fails
                        if "qa_chain" in st.session_state:
                            try:
                                if hasattr(st.session_state.qa_chain, 'invoke'):
                                    result = st.session_state.qa_chain.invoke({"query": prompt})
                                else:
                                    result = st.session_state.qa_chain({"query": prompt})
                                
                                answer = result.get('result', 'No answer found')
                                sources = result.get('source_documents', [])
                                
                                response = f"**Answer:** {answer}"
                                
                                if sources:
                                    response += "\n\n**Sources:**"
                                    for i, doc in enumerate(sources[:2]):
                                        response += f"\n- **Source {i+1}:** {doc.page_content[:150]}..."
                            except Exception as qa_error:
                                response = f"I encountered an error processing your question: {str(qa_error)}"
                        else:
                            response = "I don't have access to any documents right now. Please upload documents first, or ask me to book an appointment."
                
                # Handle case when no documents are loaded
                else:
                    if is_appointment_related(prompt):
                        response = st.session_state.form_handler.start_booking()
                    else:
                        response = """I can help you in two ways:

1. **📄 Upload documents** using the sidebar to ask questions about them
2. **📅 Book an appointment** by saying "book an appointment" or "call me"

What would you like to do?"""
                
                # Display response
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
            except Exception as e:
                error_msg = f"I encountered an error: {str(e)}. Please try again."
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

st.header("💡 Example Prompts")
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **📄 Document Questions:**
    - "What is this document about?"
    - "Summarize the main points"
    - "Find information about [topic]"
    - "What are the key conclusions?"
    """)
    
    if st.button("📄 Ask about documents", key="doc_example"):
        if st.session_state.docs_loaded:
            example_prompt = "What is this document about?"
            st.session_state.messages.append({"role": "user", "content": example_prompt})
            st.rerun()

with col2:
    st.markdown("""
    **📅 Appointment Booking:**
    - "Book an appointment"
    - "I need to schedule a meeting"
    - "Please call me"
    - "Schedule a consultation"
    """)
    
    if st.button("📅 Book appointment", key="appointment_example"):
        example_prompt = "I'd like to book an appointment"
        st.session_state.messages.append({"role": "user", "content": example_prompt})
        st.rerun()


# Debug information (only show in development)
if st.checkbox("🔧 Show Debug Info", key="debug"):
    st.subheader("Debug Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Form Handler State:**")
        st.write(f"Form Active: {st.session_state.form_handler.form_active}")
        st.write(f"Current Step: {st.session_state.form_handler.current_step}")
        st.write(f"User Info: {st.session_state.form_handler.user_info}")
    
    with col2:
        st.write("**System State:**")
        st.write(f"Docs Loaded: {st.session_state.docs_loaded}")
        st.write(f"Agent Available: {st.session_state.agent is not None}")
        st.write(f"Messages Count: {len(st.session_state.messages)}")
        
        # Environment check
        google_api_key = os.getenv('GOOGLE_API_KEY')
        if google_api_key:
            st.write(f"Google API Key: {'*' * 10}...{google_api_key[-4:]}")
        else:
            st.error("Google API Key not found in environment!")

# Clear conversation button
if st.button("🗑️ Clear Conversation", key="clear_chat"):
    st.session_state.messages = []
    st.session_state.form_handler.reset_form()
    st.session_state.messages.append({
        "role": "assistant", 
        "content": """Hello! I'm your AI assistant. I can help you with:

📄 **Document Questions** - Upload documents and ask me anything about them
📅 **Appointment Booking** - Just say "book an appointment" or "call me"

What can I help you with today?"""
    })
    st.rerun()