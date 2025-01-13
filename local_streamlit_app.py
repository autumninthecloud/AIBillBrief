import os
import streamlit as st
import pandas as pd
import traceback
from dotenv import load_dotenv
from snowflake.snowpark import Session
from snowflake.core import Root
from snowflake.cortex import Complete
from local_pdf_processor import LocalPDFProcessor
import json

# Load environment variables from .env file
load_dotenv()

# Custom CSS to set background color
st.markdown("""
    <style>
        .stApp {
            background-color: #E6E6FA;  /* Light purple color */
        }
        .stChatMessage {
            background-color: white !important;
        }
        /* Style the chat input */
        .stChatInput {
            border-radius: 8px !important;
            background-color: white !important;
            margin-top: 20px !important;
            margin-bottom: 20px !important;
            padding: 10px !important;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1) !important;
        }
        /* Add some space after messages */
        .stChatMessageContent {
            margin-bottom: 15px !important;
        }
    </style>
""", unsafe_allow_html=True)

# Define your connection parameters
# These values are loaded from environment variables
# Create a .env file with these variables (see .env.example)
connection_parameters = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT"),
    "user": os.getenv("SNOWFLAKE_USER"),
    "password": os.getenv("SNOWFLAKE_PASSWORD"),
    "role": os.getenv("SNOWFLAKE_ROLE"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
    "database": os.getenv("SNOWFLAKE_DATABASE"),
    "schema": os.getenv("SNOWFLAKE_SCHEMA")
}

# Validate that all required environment variables are set
required_env_vars = [
    "SNOWFLAKE_ACCOUNT",
    "SNOWFLAKE_USER",
    "SNOWFLAKE_PASSWORD",
    "SNOWFLAKE_ROLE",
    "SNOWFLAKE_WAREHOUSE",
    "SNOWFLAKE_DATABASE",
    "SNOWFLAKE_SCHEMA"
]

missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Global session variable
session = None
root = None

@st.cache_resource
def get_snowflake_session():
    """Get cached Snowflake session"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get Snowflake credentials from environment variables
        account = os.getenv('SNOWFLAKE_ACCOUNT')
        user = os.getenv('SNOWFLAKE_USER')
        password = os.getenv('SNOWFLAKE_PASSWORD')
        role = os.getenv('SNOWFLAKE_ROLE')
        warehouse = os.getenv('SNOWFLAKE_WAREHOUSE')
        database = os.getenv('SNOWFLAKE_DATABASE')
        schema = os.getenv('SNOWFLAKE_SCHEMA')
        
        if not all([account, user, password, role, warehouse, database, schema]):
            st.error("Missing Snowflake credentials")
            return None
            
        # Create Snowflake session
        return Session.builder.configs({
            "account": account,
            "user": user,
            "password": password,
            "role": role,
            "warehouse": warehouse,
            "database": database,
            "schema": schema
        }).create()
    
    except Exception as e:
        st.error(f"Snowflake Connection Error: {str(e)}")
        return None

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_service_metadata(_session):
    """Get cached service metadata"""
    if not _session:
        return []
        
    try:
        services = _session.sql("SHOW CORTEX SEARCH SERVICES;").collect()
        service_metadata = []
        if services:
            for s in services:
                service_metadata.append({
                    "name": s["name"]
                })
        return service_metadata
    except Exception as e:
        if st.session_state.debug:
            st.error(f"Error getting service metadata: {str(e)}")
        return []

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_recent_bills(_session):
    """Get cached recent bills"""
    if not _session:
        return []
        
    try:
        return _session.sql("""
            SELECT DISTINCT source_file, bill_subtitle, bill_sponsor, date_filed
            FROM BILL_CHUNKS
            ORDER BY date_filed DESC
            LIMIT 5
        """).collect()
    except Exception as e:
        if st.session_state.debug:
            st.error(f"Error getting recent bills: {str(e)}")
        return []

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_bill_stats(_session):
    """Get cached bill statistics"""
    if not _session:
        return {'total_bills': 0, 'latest_file_date': None}
        
    try:
        stats = _session.sql("""
            SELECT 
                COUNT(DISTINCT source_file) as total_bills,
                MAX(date_filed) as latest_file_date
            FROM BILL_CHUNKS
        """).collect()
        if stats and len(stats) > 0:
            return {
                'total_bills': stats[0]['TOTAL_BILLS'],
                'latest_file_date': stats[0]['LATEST_FILE_DATE']
            }
        return {'total_bills': 0, 'latest_file_date': None}
    except Exception as e:
        if st.session_state.debug:
            st.error(f"Error getting bill stats: {str(e)}")
        return {'total_bills': 0, 'latest_file_date': None}

def format_date(date):
    """Safely format a date with null check"""
    if date is None:
        return "No date"
    try:
        return date.strftime('%Y-%m-%d')
    except:
        return str(date)

def init_session_state():
    """Initialize all session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "debug" not in st.session_state:
        st.session_state.debug = False
    if "use_chat_history" not in st.session_state:
        st.session_state.use_chat_history = True
    if "model_name" not in st.session_state:
        st.session_state.model_name = "mistral-large2"
    if "num_retrieved_chunks" not in st.session_state:
        st.session_state.num_retrieved_chunks = 5
    if "num_chat_messages" not in st.session_state:
        st.session_state.num_chat_messages = 10
    if "service_metadata" not in st.session_state:
        st.session_state.service_metadata = []
    if "selected_cortex_search_service" not in st.session_state:
        st.session_state.selected_cortex_search_service = None

def query_cortex_search_service(query, columns=None, filter=None):
    """Query the cortex search service"""
    if columns is None:
        columns = ["chunk", "source_file", "chunk_index", "bill_subtitle", "bill_sponsor", "date_filed"]
    
    try:
        # Build query
        select_cols = ", ".join(columns)
        where_clause = f"AND {filter}" if filter else ""
        
        # Use semantic search on the table directly
        query_sql = f"""
            SELECT {select_cols}
            FROM BILL_CHUNKS
            WHERE SEMANTIC_CONTAINS(chunk, '{query}', 'bill_search_service')
            {where_clause}
            LIMIT {st.session_state.num_retrieved_chunks}
        """
        
        if st.session_state.debug:
            st.sidebar.write("Query SQL:", query_sql)
            
        results = session.sql(query_sql).collect()
        
        if not results:
            if st.session_state.debug:
                st.error("No results found")
            return "", []
            
        # Format results for context
        context_parts = []
        for r in results:
            try:
                bill_name = r['SOURCE_FILE'].replace('.pdf', '') if r['SOURCE_FILE'] else 'Unknown Bill'
                sponsor = r['BILL_SPONSOR'] if r['BILL_SPONSOR'] else 'Unknown Sponsor'
                chunk = r['CHUNK'] if r['CHUNK'] else 'No content available'
                
                context_parts.append(
                    f"From {format_bill_reference(bill_name)} "
                    f"(Filed: {format_date(r['DATE_FILED'])}, "
                    f"Sponsor: {sponsor}):\n"
                    f"{chunk}\n"
                )
            except Exception as e:
                if st.session_state.debug:
                    st.error(f"Error formatting result: {str(e)}")
                continue
        
        if not context_parts:
            return "", []
            
        return "\n---\n".join(context_parts), results
        
    except Exception as e:
        if st.session_state.debug:
            st.error(f"Search error: {str(e)}")
        return "", []

def init_config_options():
    """Initialize configuration options in sidebar"""
    global session
    
    # Display bill metadata with links
    with st.sidebar.expander("Recent Bills", expanded=False):
        recent_bills = get_recent_bills(session)
        if recent_bills:
            for bill in recent_bills:
                try:
                    if bill and 'SOURCE_FILE' in bill:
                        bill_name = bill['SOURCE_FILE'].replace('.pdf', '')
                        subtitle = bill['BILL_SUBTITLE'] if 'BILL_SUBTITLE' in bill else 'No subtitle available'
                        sponsor = bill['BILL_SPONSOR'] if 'BILL_SPONSOR' in bill else 'Unknown'
                        date_filed = bill['DATE_FILED'] if 'DATE_FILED' in bill else None
                        
                        st.markdown(
                            f"**{format_bill_reference(bill_name)}**  \n"
                            f"Filed: {format_date(date_filed)}  \n"
                            f"Sponsor: {sponsor}  \n"
                            f"_{subtitle}_  \n"
                            "---"
                        )
                except Exception as e:
                    if st.session_state.debug:
                        st.error(f"Error displaying bill: {str(e)}")
                    continue
        else:
            st.write("No recent bills available")

    # Clear conversation button
    if st.sidebar.button("Clear conversation"):
        st.session_state.messages = []
        st.rerun()

    # Debug and chat history toggles
    st.session_state.debug = st.sidebar.toggle("Debug", value=st.session_state.debug)
    st.session_state.use_chat_history = st.sidebar.toggle("Use chat history", value=st.session_state.use_chat_history)

    # Advanced options
    with st.sidebar.expander("Advanced options"):
        # Select Cortex search service if available
        if st.session_state.service_metadata:
            st.session_state.selected_cortex_search_service = st.selectbox(
                "Select cortex search service:",
                [s["name"] for s in st.session_state.service_metadata],
                index=0 if st.session_state.selected_cortex_search_service is None else 
                      [s["name"] for s in st.session_state.service_metadata].index(st.session_state.selected_cortex_search_service)
            )
        
        st.session_state.model_name = st.selectbox(
            "Select model:", 
            ["mistral-large2", "llama3.1-70b", "llama3.1-8b"],
            index=["mistral-large2", "llama3.1-70b", "llama3.1-8b"].index(st.session_state.model_name)
        )
        st.session_state.num_retrieved_chunks = st.number_input(
            "Select number of context chunks",
            value=st.session_state.num_retrieved_chunks,
            min_value=1,
            max_value=10,
        )
        st.session_state.num_chat_messages = st.number_input(
            "Number of chat messages to include",
            value=st.session_state.num_chat_messages,
            min_value=1,
            max_value=50,
        )

def load_bills_to_snowflake():
    """
    Process all PDFs in the bills directory and load them into Snowflake
    """
    try:
        print("Starting bill loading process...")
        
        # Create processor
        processor = LocalPDFProcessor('bills', 'csv_files')
        print("Created PDF processor")
        
        # Process PDFs
        print("Processing PDFs...")
        processor.process_pdfs()
        print("Finished processing PDFs")
        
        # Get list of CSV files
        csv_files = [f for f in os.listdir('csv_files') if f.endswith('.csv')]
        print(f"Found {len(csv_files)} CSV files: {csv_files}")
        
        # Process each CSV file
        for csv_file in csv_files:
            try:
                print(f"Processing {csv_file}...")
                
                # Read CSV file
                df = pd.read_csv(f'csv_files/{csv_file}')
                print(f"Read CSV file with {len(df)} rows")
                
                # Convert timestamp columns to proper format
                if 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                if 'date_filed' in df.columns:
                    df['date_filed'] = pd.to_datetime(df['date_filed'])
                
                # Convert to Snowpark DataFrame
                print(f"Writing {csv_file} to Snowflake...")
                snow_df = session.create_dataframe(df)
                snow_df.write.mode("append").save_as_table("BILL_CHUNKS")
                print(f"Successfully wrote {csv_file} to Snowflake")
                
            except Exception as e:
                print(f"Error processing {csv_file}: {str(e)}")
                print(f"Error type: {type(e)}")
                print(f"Traceback: {traceback.format_exc()}")
                continue
                
    except Exception as e:
        print(f"Error in load_bills_to_snowflake: {str(e)}")
        print(f"Error type: {type(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        
def create_prompt(user_question):
    """Create prompt for the language model"""
    # Get current bill statistics
    bill_stats = get_bill_stats(session)
    
    if st.session_state.use_chat_history:
        chat_history = get_chat_history()
        if chat_history != []:
            prompt_context, results = query_cortex_search_service(
                user_question,
                columns=["chunk", "source_file"],
                filter={}
            )
        else:
            prompt_context, results = query_cortex_search_service(
                user_question,
                columns=["chunk", "source_file"],
                filter={}
            )
            chat_history = ""

    # Process context to include bill links
    processed_context = prompt_context
    if results:
        for result in results:
            if 'source_file' in result:
                bill_name = result['source_file'].replace('.pdf', '')
                bill_ref = format_bill_reference(bill_name)
                processed_context = processed_context.replace(bill_name, bill_ref)

    prompt = f"""
            [INST]
            You are a helpful AI assistant specifically focused on Arkansas legislative bills filed for the 2025 session. Your purpose is to help users understand and navigate these bills.

            Current Bill Statistics:
            - Total Bills Filed: {bill_stats['total_bills']}
            - Latest Filing Date: {bill_stats['latest_file_date']}

            IMPORTANT RESPONSE GUIDELINES:
            1. ONLY answer questions about Arkansas legislative bills for the 2025 session
            2. If a user asks about:
               - Bills from other states
               - Federal legislation
               - Past Arkansas sessions
               - Any non-legislative topics
               Respond with: "I'm specifically designed to help with Arkansas legislative bills for the 2025 session. That topic is outside my scope. 
               Would you like to know:
               - How many bills have been filed so far?
               - What bills were filed this week?
               - Information about a specific bill?"
            3. For valid questions, use the context provided between <context> tags and chat history between <chat_history> tags
            4. Never say "according to the provided context" or similar phrases
            5. For questions about bill counts or statistics, use the Current Bill Statistics provided above
            6. If you can't find information about a specific bill in the context, say "I don't have information about that specific bill in my current database."
            7. When referring to bills, use the markdown link format provided in the context. For example: [SB1](URL)

            <chat_history>
            {chat_history}
            </chat_history>
            <context>
            {processed_context}
            </context>
            <question>
            {user_question}
            </question>
            [/INST]
            Answer:
            """
    return prompt, results

def get_bill_url(bill_name):
    """Generate URL for a bill"""
    return f"https://arkleg.state.ar.us/Home/FTPDocument?path=%2FBills%2F2025R%2FPublic%2F{bill_name}.pdf"

def format_bill_reference(bill_name):
    """Format a bill reference with its URL"""
    url = get_bill_url(bill_name)
    return f"[{bill_name}]({url})"

def get_chat_history():
    """Get chat history"""
    start_index = max(
        0, len(st.session_state.messages) - st.session_state.num_chat_messages
    )
    return st.session_state.messages[start_index : len(st.session_state.messages) - 1]

def complete(model, prompt):
    """Generate completion using Snowflake"""
    return Complete(model, prompt, session=session).replace("$", "\$")

def main():
    st.title("AR Legislative AI Bill Bot ")
    st.markdown("""
    ### Welcome! Ask me anything about bills filed for the upcoming 2025 session! 
    I'm here to help you understand and navigate through Arkansas legislative bills.
    """)

    # Initialize session state
    init_session_state()

    # Initialize Snowflake
    global session
    session = get_snowflake_session()
    
    # Get service metadata
    st.session_state.service_metadata = get_service_metadata(session)
    
    # Initialize UI components
    init_config_options()

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Create a container for the chat interface
    chat_container = st.container()

    # Check if chat should be disabled
    disable_chat = session is None
    
    # Debug information
    if st.session_state.debug:
        st.sidebar.write("Debug Info:")
        st.sidebar.write(f"Session Active: {session is not None}")
        st.sidebar.write(f"Chat Disabled: {disable_chat}")
    
    if question := st.chat_input("Ask a question...", disabled=disable_chat):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": question})
        
        # Display user message in chat message container
        with chat_container:
            with st.chat_message("user"):
                st.markdown(question.replace("$", "\$"))

            # Display assistant response in chat message container
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                
                # Show thinking animation
                with st.spinner("Thinking..."):
                    question = question.replace("'", "")
                    prompt, results = create_prompt(question)
                    generated_response = complete(
                        st.session_state.model_name, prompt
                    )
                
                # Display the response
                message_placeholder.markdown(generated_response)
                
                # Add to chat history
                st.session_state.messages.append(
                    {"role": "assistant", "content": generated_response}
                )

if __name__ == "__main__":
    main()
