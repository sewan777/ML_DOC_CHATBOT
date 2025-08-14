import asyncio
import os
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from langchain.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain.text_splitter import CharacterTextSplitter
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.memory import ConversationBufferMemory
import PyPDF2
import io

def load_docs(uploaded_files):
    """Load documents from uploaded files."""
    docs = []
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    
    for uploaded_file in uploaded_files:
        if uploaded_file.type == "application/pdf":
            # Handle PDF files
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            
            # Split text into chunks
            chunks = text_splitter.split_text(text)
            for chunk in chunks:
                docs.append(Document(page_content=chunk, metadata={"source": uploaded_file.name}))
                
        elif uploaded_file.type == "text/plain":
            # Handle text files
            text = str(uploaded_file.read(), "utf-8")
            chunks = text_splitter.split_text(text)
            for chunk in chunks:
                docs.append(Document(page_content=chunk, metadata={"source": uploaded_file.name}))
    
    return docs

def build_qa_chain(docs):
    """Build QA chain with free Google Gemini LLM."""
    
    if not docs:
        raise ValueError("No documents provided to build QA chain")
    
    # Only need Google API key (free tier available)
    if not os.getenv('GOOGLE_API_KEY'):
        raise ValueError("GOOGLE_API_KEY not found in environment variables")
    
    print(f"Building QA chain with {len(docs)} documents")
    
    # Simple approach: try to set up event loop if needed
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Event loop is closed")
    except RuntimeError:
        # No event loop exists, create one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        print("Created new event loop")
    
    try:
        print("Initializing embeddings...")
        # Step 1: Initialize embeddings
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        print("Embeddings initialized successfully")

        print("Creating vector store...")
        # Step 2: Create a vector store from docs
        vectorstore = FAISS.from_documents(docs, embeddings)
        print("Vector store created successfully")

        print("Creating retriever...")
        # Step 3: Create retriever
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        print("Retriever created successfully")

        print("Initializing Google Gemini LLM...")
        # Step 4: Initialize Google Gemini LLM (free tier available)
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",  # Free tier model
            temperature=0.1,
            convert_system_message_to_human=True
        )
        print("Google Gemini LLM initialized successfully")

        print("Building QA chain...")
        # Step 5: Build QA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True
        )
        print("QA chain built successfully")

        # Verify the chain
        if qa_chain is None:
            raise RuntimeError("QA chain is None")
        
        print("QA chain verification passed")
        return qa_chain

    except Exception as e:
        print(f"Error in build_qa_chain: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise

def build_agent_with_tools(docs, form_handler):
    """Build agent with document QA and appointment booking tools."""
    
    if not os.getenv('GOOGLE_API_KEY'):
        raise ValueError("GOOGLE_API_KEY not found in environment variables")
    
    # Initialize embeddings and vector store
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vectorstore = FAISS.from_documents(docs, embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    
    # Initialize LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0.1,
        convert_system_message_to_human=True
    )
    
    # Build QA chain for documents
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )
    
    # Define tools
    def document_qa_tool(query):
        """Tool function for document QA"""
        try:
            if hasattr(qa_chain, 'invoke'):
                result = qa_chain.invoke({"query": query})
            else:
                result = qa_chain({"query": query})
            
            answer = result.get('result', 'No answer found')
            sources = result.get('source_documents', [])
            
            response = f"Answer: {answer}\n\n"
            if sources:
                response += "Sources:\n"
                for i, doc in enumerate(sources[:2]):  # Limit to 2 sources
                    response += f"- Source {i+1}: {doc.page_content[:100]}...\n"
            
            return response
        except Exception as e:
            return f"Error querying documents: {str(e)}"
    
    def book_appointment_tool(input_text):
        """Tool function to start appointment booking"""
        form_handler.reset_form()
        form_handler.form_active = True
        form_handler.current_step = 'name'
        return "I'd be happy to help you book an appointment! Let's start by collecting some information. What's your full name?"
    
    def process_form_tool(user_input):
        """Tool function to process form input"""
        if form_handler.form_active:
            return form_handler.process_form_input(user_input)
        else:
            return "No active form to process."
    
    # Create tools list
    tools = [
        Tool(
            name="Document_QA",
            func=document_qa_tool,
            description="Use this tool to answer questions based on uploaded documents. Input should be a question about the documents."
        ),
        Tool(
            name="Book_Appointment",
            func=book_appointment_tool,
            description="Use this tool when user wants to book an appointment or asks you to call them. Input should be 'start_booking'."
        ),
        Tool(
            name="Process_Form_Input",
            func=process_form_tool,
            description="Use this tool to process user input during the appointment booking form. Input should be the user's response."
        )
    ]
    
    # Initialize memory
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    
    # Initialize the agent
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
        memory=memory,
        verbose=True,
        handle_parsing_errors=True
    )
    
    return agent