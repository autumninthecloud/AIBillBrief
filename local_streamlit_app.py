import streamlit as st
import os
from local_pdf_processor import LocalPDFProcessor

MODELS = [
    "mistral-large2",
    "llama3.1-70b",
    "llama3.1-8b",
]

def init_messages():
    if st.session_state.clear_conversation or "messages" not in st.session_state:
        st.session_state.messages = []

def init_service_metadata():
    if "service_metadata" not in st.session_state:
        # Mock service metadata for local testing
        st.session_state.service_metadata = [
            {"name": "local_service", "search_column": "chunk"}
        ]

def init_config_options():
    st.sidebar.title("Configuration")
    st.sidebar.selectbox("Select Cortex Search Service", [s["name"] for s in st.session_state.service_metadata])
    st.sidebar.checkbox("Clear Conversation", key="clear_conversation")
    st.sidebar.checkbox("Debug Mode", key="debug_mode")

def query_cortex_search_service(query, columns=[], filter={}):
    # Mock query function for local testing
    return "Mock context document for query: " + query

def get_chat_history():
    return st.session_state.get("messages", [])

def complete(model, prompt):
    # Mock completion function for local testing
    return f"Generated completion for model {model}: {prompt}"

def make_chat_history_summary(chat_history, question):
    return f"Summary of chat history and question: {chat_history} {question}"

def create_prompt(user_question):
    context = query_cortex_search_service(user_question)
    return f"Prompt with context: {context}"

def main():
    st.title("Local Streamlit App")
    init_messages()
    init_service_metadata()
    init_config_options()
    user_question = st.text_input("Ask a question:")
    if user_question:
        prompt = create_prompt(user_question)
        model = st.selectbox("Select Model", MODELS)
        response = complete(model, prompt)
        st.write(response)

if __name__ == "__main__":
    main()
