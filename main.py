import streamlit as st
import os
from dotenv import load_dotenv
from chatbot import load_docs, build_qa_chain
from langchain.docstore.document import Document
from tool_agents import create_tool_agents_manager
from conversational_form import ConversationalForm

# Load environment variables
load_dotenv()

st.set_page_config(page_title="ML Chatbot with Appointment Booking", page_icon="🤖")

st.title("ML_DOC_CHATBOT 🤖 with Appointment Scheduling")

# Initialize session state for appointment system
if "tool_agents_manager" not in st.session_state:
    if os.getenv('GOOGLE_API_KEY'):
        st.session_state.tool_agents_manager = create_tool_agents_manager(os.getenv('GOOGLE_API_KEY'))
    else:
        st.error("GOOGLE_API_KEY not found in environment variables")
        st.stop()

if "conversation_mode" not in st.session_state:
    st.session_state.conversation_mode = "document_qa"  # or "appointment"

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Sidebar for mode selection
with st.sidebar:
    st.header("Chat Mode")
    mode = st.radio(
        "Select chat mode:",
        ["Document Q&A", "Appointment Booking", "Hybrid Mode"],
        index=2 if st.session_state.conversation_mode == "hybrid" else (0 if st.session_state.conversation_mode == "document_qa" else 1)
    )
    
    if mode == "Document Q&A":
        st.session_state.conversation_mode = "document_qa"
    elif mode == "Appointment Booking":
        st.session_state.conversation_mode = "appointment"
    else:
        st.session_state.conversation_mode = "hybrid"
    
    st.header("Appointment System")
    if st.button("View Appointments"):
        appointments_summary = st.session_state.tool_agents_manager.get_appointments_summary()
        st.text_area("Appointments Summary", appointments_summary, height=200)
    
    if st.button("Reset Appointment Form"):
        st.session_state.tool_agents_manager.reset_appointment_form()
        st.success("Appointment form reset!")
    
    # Show current form state
    if hasattr(st.session_state.tool_agents_manager, 'appointment_tool'):
        form_state = st.session_state.tool_agents_manager.appointment_tool.get_form_state()
        if form_state != "idle":
            st.info(f"Form State: {form_state}")
            collected_info = st.session_state.tool_agents_manager.appointment_tool.get_collected_info()
            if any(collected_info.values()):
                st.json(collected_info)

# Main content area
if st.session_state.conversation_mode in ["document_qa", "hybrid"]:
    st.header("📄 Document Upload")
    
    # File upload
    uploaded_files = st.file_uploader(
        "Upload your documents", 
        type=["pdf", "txt"], 
        accept_multiple_files=True
    )

    # Initialize documents
    docs = []
    if uploaded_files:
        with st.spinner("Loading documents..."):
            try:
                docs = load_docs(uploaded_files)
                st.success(f"Loaded {len(docs)} document chunks successfully!")
            except Exception as e:
                st.error(f"Error loading documents: {str(e)}")
                docs = []
    else:
        # Try to load sample documents if no files uploaded
        try:
            sample_files = []
            if os.path.exists("sample_docs/sample1.pdf"):
                with open("sample_docs/sample1.pdf", "rb") as f:
                    sample_files.append(type('obj', (object,), {
                        'read': lambda: f.read(),
                        'name': 'sample1.pdf',
                        'type': 'application/pdf'
                    })())
            
            if sample_files:
                with st.spinner("Loading sample documents..."):
                    docs = load_docs(sample_files)
                    st.info(f"Loaded {len(docs)} sample document chunks. Upload your own documents to replace these.")
        except Exception as e:
            st.warning("No documents available. Please upload some files.")

    # Initialize QA chain safely
    if st.session_state.conversation_mode in ["document_qa", "hybrid"] and docs:
        if "qa_chain" not in st.session_state or "docs_hash" not in st.session_state or st.session_state.docs_hash != hash(str(docs)):
            with st.spinner("Initializing chatbot..."):
                try:
                    qa_chain = build_qa_chain(docs)
                    if qa_chain is None:
                        st.error("Failed to build QA chain - returned None")
                    else:
                        st.session_state.qa_chain = qa_chain
                        st.session_state.docs_hash = hash(str(docs))
                        st.success("Chatbot initialized successfully!")
                except Exception as e:
                    st.error(f"Failed to initialize chatbot: {str(e)}")
                    st.error(f"Error type: {type(e).__name__}")

# Chat interface
st.header("💬 Chat Interface")

# Display chat history
if st.session_state.chat_history:
    for i, (user_msg, bot_msg, msg_type) in enumerate(st.session_state.chat_history):
        with st.container():
            col1, col2 = st.columns([1, 4])
            with col1:
                st.write("👤 **You:**")
            with col2:
                st.write(user_msg)
        
        with st.container():
            col1, col2 = st.columns([1, 4])
            with col1:
                emoji = "🤖" if msg_type == "qa" else "📅" if msg_type == "appointment" else "🔄"
                st.write(f"{emoji} **Bot:**")
            with col2:
                st.write(bot_msg)
        st.divider()

# User input
query = st.text_input("Ask a question or request an appointment:", key="user_input")

if query:
    # Add user message to history
    user_message = query
    
    # Determine how to process the message based on mode
    if st.session_state.conversation_mode == "document_qa":
        # Document Q&A mode only
        if "qa_chain" not in st.session_state or st.session_state.qa_chain is None:
            st.error("QA chain is not initialized. Please upload documents first.")
        else:
            with st.spinner("Generating answer..."):
                try:
                    if hasattr(st.session_state.qa_chain, 'invoke'):
                        result = st.session_state.qa_chain.invoke({"query": query})
                    else:
                        result = st.session_state.qa_chain({"query": query})
                    
                    answer = result.get('result', 'No answer found')
                    sources = result.get('source_documents', [])
                    
                    bot_response = f"**Answer:** {answer}"
                    if sources:
                        bot_response += "\n\n**Sources:**\n"
                        for i, doc in enumerate(sources[:2]):  # Limit to 2 sources for brevity
                            content_preview = doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content
                            bot_response += f"• {content_preview}\n"
                    
                    st.session_state.chat_history.append((user_message, bot_response, "qa"))
                    
                except Exception as e:
                    error_response = f"Error generating answer: {str(e)}"
                    st.session_state.chat_history.append((user_message, error_response, "qa"))
    
    elif st.session_state.conversation_mode == "appointment":
        # Appointment booking mode only
        with st.spinner("Processing appointment request..."):
            try:
                result = st.session_state.tool_agents_manager.process_message(query)
                bot_response = result["response"]
                st.session_state.chat_history.append((user_message, bot_response, "appointment"))
                
                # Show appointment confirmation if completed
                if result.get("state") == "completed" and result.get("appointment_data"):
                    st.balloons()
                    st.success("🎉 Appointment successfully scheduled!")
                
            except Exception as e:
                error_response = f"Error processing appointment: {str(e)}"
                st.session_state.chat_history.append((user_message, error_response, "appointment"))
    
    else:  # hybrid mode
        # Hybrid mode - intelligently route based on content
        with st.spinner("Processing your request..."):
            try:
                # First, check if it's an appointment-related request
                form = ConversationalForm()
                is_appointment_request = form.is_requesting_callback(query)
                
                # Also check if we're in the middle of an appointment conversation
                current_form_state = st.session_state.tool_agents_manager.appointment_tool.get_form_state()
                
                if is_appointment_request or current_form_state != "idle":
                    # Handle as appointment request
                    result = st.session_state.tool_agents_manager.process_message(query)
                    bot_response = result["response"]
                    message_type = "appointment"
                    
                    # Show appointment confirmation if completed
                    if result.get("state") == "completed" and result.get("appointment_data"):
                        st.balloons()
                        st.success("🎉 Appointment successfully scheduled!")
                
                else:
                    # Handle as document Q&A
                    if "qa_chain" not in st.session_state or st.session_state.qa_chain is None:
                        bot_response = "I can help you with document questions once you upload some documents, or I can help you schedule an appointment. What would you like to do?"
                        message_type = "hybrid"
                    else:
                        if hasattr(st.session_state.qa_chain, 'invoke'):
                            result = st.session_state.qa_chain.invoke({"query": query})
                        else:
                            result = st.session_state.qa_chain({"query": query})
                        
                        answer = result.get('result', 'No answer found')
                        sources = result.get('source_documents', [])
                        
                        bot_response = f"**Answer:** {answer}"
                        if sources:
                            bot_response += "\n\n**Sources:**\n"
                            for i, doc in enumerate(sources[:2]):
                                content_preview = doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content
                                bot_response += f"• {content_preview}\n"
                        
                        # Add suggestion for appointment if answer seems insufficient
                        if len(answer) < 50 or "no answer" in answer.lower():
                            bot_response += "\n\n💡 *If you'd like to discuss this further, I can arrange a callback for you. Just say 'call me back' or 'schedule appointment'.*"
                        
                        message_type = "qa"
                
                st.session_state.chat_history.append((user_message, bot_response, message_type))
                
            except Exception as e:
                error_response = f"Error processing request: {str(e)}"
                st.session_state.chat_history.append((user_message, error_response, "hybrid"))

    # Rerun to update the display
    st.rerun()

# Footer with instructions
st.markdown("---")
st.markdown("""
### 💡 How to use this chatbot:

**Document Q&A Mode:**
- Upload PDF or text documents
- Ask questions about the content
- Get answers with source citations

**Appointment Booking Mode:**
- Say "call me back", "schedule appointment", or "book a meeting"
- Provide your name, phone, email, and preferred date/time
- Use natural language for dates like "next Monday", "tomorrow at 2 PM"

**Hybrid Mode (Recommended):**
- Ask document questions or request appointments seamlessly
- The bot automatically determines the best way to help you
- Switch between Q&A and appointment booking naturally

**Example appointment requests:**
- "Can you call me back to discuss this?"
- "I'd like to schedule a meeting for next Tuesday at 3 PM"
- "Book an appointment for tomorrow"
""")

# Display current appointment form state in hybrid/appointment mode
if st.session_state.conversation_mode in ["appointment", "hybrid"]:
    form_state = st.session_state.tool_agents_manager.appointment_tool.get_form_state()
    if form_state not in ["idle", "completed"]:
        with st.expander("📋 Current Form Progress", expanded=True):
            collected_info = st.session_state.tool_agents_manager.appointment_tool.get_collected_info()
            
            progress_items = [
                ("Name", collected_info.get('name')),
                ("Phone", collected_info.get('phone')),
                ("Email", collected_info.get('email')),
                ("Date", collected_info.get('appointment_date')),
                ("Time", collected_info.get('appointment_time')),
                ("Reason", collected_info.get('reason'))
            ]
            
            for label, value in progress_items:
                if value:
                    st.success(f"✅ {label}: {value}")
                else:
                    st.info(f"⏳ {label}: Pending")