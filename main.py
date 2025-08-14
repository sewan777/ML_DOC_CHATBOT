import streamlit as st
import os
from dotenv import load_dotenv
from chatbot import load_docs, build_qa_chain
from langchain.docstore.document import Document

# Load environment variables
load_dotenv()

st.set_page_config(page_title="ML Chatbot", page_icon="🤖")

st.title("ML_DOC_CHATBOT 🤖")

# File upload
uploaded_files = st.file_uploader(
    "Upload your documents", 
    type=["pdf", "txt"], 
    accept_multiple_files=True
)

#Initialize documents
docs = []
if uploaded_files:
    with st.spinner("Loading documents..."):
        try:
            docs = load_docs(uploaded_files)
            st.success(f"Loaded {len(docs)} document chunks successfully!")
        except Exception as e:
            st.error(f"Error loading documents: {str(e)}")
            st.stop()
else:
 
               st.error("No documents uploaded. Please upload PDF(s) to proceed.")

#Initialize QA chain safely
if "qa_chain" not in st.session_state or "docs_hash" not in st.session_state or st.session_state.docs_hash != hash(str(docs)):
    if not docs:
        st.error("No documents to process. Please upload some files or check the example documents.")
        st.stop()
    
    with st.spinner("Initializing chatbot..."):
        try:
            qa_chain = build_qa_chain(docs)
            if qa_chain is None:
                st.error("Failed to build QA chain - returned None")
                st.stop()
            st.session_state.qa_chain = qa_chain
            st.session_state.docs_hash = hash(str(docs))
            st.success("Chatbot initialized successfully!")
        except Exception as e:
            st.error(f"Failed to initialize chatbot: {str(e)}")
            st.error(f"Error type: {type(e).__name__}")
            import traceback
            st.error(f"Traceback: {traceback.format_exc()}")
            st.stop()

# User input
query = st.text_input("Ask a question:")

if query:
    if "qa_chain" not in st.session_state or st.session_state.qa_chain is None:
        st.error("QA chain is not initialized. Please refresh the page.")
    else:
        with st.spinner("Generating answer..."):
            try:
                # Use invoke or __call__ instead of run for multiple outputs
                if hasattr(st.session_state.qa_chain, 'invoke'):
                    result = st.session_state.qa_chain.invoke({"query": query})
                else:
                    result = st.session_state.qa_chain({"query": query})
                
                # Extract the answer and sources
                answer = result.get('result', 'No answer found')
                sources = result.get('source_documents', [])
                
                st.write("**Answer:**", answer)
                
                if sources:
                    with st.expander("📚 Sources"):
                        for i, doc in enumerate(sources):
                            st.write(f"**Source {i+1}:**")
                            st.write(doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content)
                            if hasattr(doc, 'metadata') and doc.metadata.get('source'):
                                st.write(f"*From: {doc.metadata['source']}*")
                            st.write("---")
                            
            except Exception as e:
                st.error(f"Error generating answer: {str(e)}")
                st.error(f"Error type: {type(e).__name__}")
                import traceback
                st.error(f"Traceback: {traceback.format_exc()}")