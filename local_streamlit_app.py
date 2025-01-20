import os
import streamlit as st
import pandas as pd
import traceback
from dotenv import load_dotenv
from snowflake.snowpark import Session
import json
import re
import sys

# Set page config at the very start
st.set_page_config(
    page_title="AI Bill Brief - Arkansas Legislative Assistant",
    page_icon="🏛️",
    layout="wide"
)

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

def get_row_value(row, column):
    """Safely get a value from a Snowflake row object"""
    try:
        # Try direct attribute access
        return getattr(row, column, None)
    except:
        try:
            # Try dictionary-style access
            return row[column]
        except:
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
                    "name": get_row_value(s, "name")
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
            SELECT DISTINCT "source_file", "bill_subtitle", "bill_sponsor", "date_filed"
            FROM BILL_CHUNKS
            ORDER BY "date_filed" DESC
            LIMIT 5
        """).collect()
    except Exception as e:
        print(f"Error getting recent bills: {str(e)}")
        if st.session_state.debug:
            st.error(f"Error getting recent bills: {str(e)}")
        return []

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_bill_stats(_session):
    """Get cached bill statistics"""
    st.write(_session)
    if not _session:
        return {'total_bills': 0, 'latest_file_date': None}
        
    try:
        stats = _session.sql("""
            SELECT 
                COUNT(DISTINCT "source_file") as TOTAL_BILLS,
                MAX("date_filed") as latest_file_date
            FROM BILL_CHUNKS
        """).collect()
        if stats and len(stats) > 0:
            st.write(stats)
            return {
                'total_bills': get_row_value(stats[0], 'TOTAL_BILLS'),
                'latest_file_date': get_row_value(stats[0], 'LATEST_FILE_DATE')
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
        # For now, just get the essential columns since we'll extract other info from chunk
        columns = ["'chunk'", "source_file", "chunk_index"]
    
    try:
        # First, let's check what's in the database
        check_sql = """
            SELECT COUNT(*) as row_count 
            FROM BILL_CHUNKS;
        """
        row_count = session.sql(check_sql).collect()
        if st.session_state.debug:
            st.sidebar.write("Total rows in BILL_CHUNKS:", get_row_value(row_count[0], 'ROW_COUNT'))
        
        try:
            # Check what bills are available
            check_sql = """
                SELECT DISTINCT "source_file"
                FROM BILL_CHUNKS
                ORDER BY "source_file";
            """
            available_bills = session.sql(check_sql).collect()
            # print("available_bills", available_bills)
        except Exception as e:
            print("error 127")
            print(f"Error getting available bills: {str(e)}")
            if st.session_state.debug:
                st.sidebar.write(f"Error getting available bills: {str(e)}")
            return [], []
        
        # Display available bills
        if st.session_state.debug:
            st.sidebar.write("Available bills:", [get_row_value(r, "source_file") for r in available_bills])
        
        # Build query
        select_cols = ", ".join(columns)  # This ensures we get all needed columns
        where_clause = f"AND {filter}" if filter else ""
        
        # Extract specific bill number from query first
        bill_patterns = [
            # Senate Bills
            (r'\b(SB|sb|Senate Bill|senate bill)\s*(\d+)\b', 'SB'),
            # House Bills
            (r'\b(HB|hb|House Bill|house bill)\s*(\d+)\b', 'HB')
        ]
        
        bill_query = None
        for pattern, btype in bill_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                prefix = match.group(1).upper()
                number = match.group(2)
                bill_query = f"{btype}{number}"
                break
        
        if bill_query:
            if st.session_state.debug:
                st.sidebar.write(f"Extracted bill number: {bill_query}")
            
            # Debug: Show actual SQL query
            query_sql = f"""
                SELECT b."chunk", b."source_file", b."chunk_index"
                FROM BILL_CHUNKS b
                WHERE UPPER(b."source_file") = '{bill_query.upper()}.PDF'
                {where_clause}
                ORDER BY b."chunk_index"
                LIMIT {st.session_state.num_retrieved_chunks}
            """
            
            if st.session_state.debug:
                st.sidebar.write("SQL Query:", query_sql)
                # Check what's in the table for this bill
                check_sql = f"""
                    SELECT COUNT(*) as count
                    FROM BILL_CHUNKS
                    WHERE "source_file" = '{bill_query}.PDF'
                """
                count_result = session.sql(check_sql).collect()
                st.sidebar.write(f"Number of chunks found for {bill_query}.PDF:", get_row_value(count_result[0], 'COUNT'))
        
        else:
            # Check for general bill type queries
            bill_type_patterns = [
                # House Bills
                (r'(?:recent|latest|any|tell|show|about|summary).*(?:house bill|hb)s?', 'HB'),
                (r'(?:house bill|hb)s?.*(?:recent|latest|filed|new)', 'HB'),
                # Senate Bills
                (r'(?:recent|latest|any|tell|show|about|summary).*(?:senate bill|sb)s?', 'SB'),
                (r'(?:senate bill|sb)s?.*(?:recent|latest|filed|new)', 'SB'),
                # Fallback patterns
                (r'\b(?:house bill|hb)s?\b', 'HB'),
                (r'\b(?:senate bill|sb)s?\b', 'SB')
            ]
            
            bill_type = None
            for pattern, btype in bill_type_patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    bill_type = btype
                    break
            
            if bill_type:
                if st.session_state.debug:
                    st.sidebar.write(f"Looking for {bill_type} bills")
                
                try:
                    # Get the most recent bill of this type
                    query_sql = f"""
                        WITH RankedBills AS (
                            SELECT DISTINCT "source_file",
                                ROW_NUMBER() OVER (ORDER BY "source_file" DESC) as rn
                            FROM BILL_CHUNKS
                            WHERE "source_file" LIKE '{bill_type}%'
                        )
                        SELECT b."chunk", b."source_file", b."chunk_index"
                        FROM BILL_CHUNKS b
                        INNER JOIN RankedBills r ON r."source_file" = b."source_file"
                        WHERE r.rn = 1
                        ORDER BY b."chunk_index";
                    """
                except Exception as e:
                    print("error 125")
                    print(f"Error getting most recent {bill_type} bill: {str(e)}")
                    if st.session_state.debug:
                        st.sidebar.write(f"Error getting most recent {bill_type} bill: {str(e)}")
                    return []
            
            else:
                # Check for sponsor query patterns
                sponsor_patterns = [
                    r'(?:bills? (?:by|from|sponsored by)|what (?:bills|else) (?:has|have|did))?\s*(?:senator[s]?\s+([a-zA-Z.\s-]+))',
                    r'(?:what|any|other)\s+bills?\s+(?:by|from|sponsored by)\s+([a-zA-Z.\s-]+?)(?:\s+(?:sponsor|file|author)|[?.,]|$)'
                ]
                
                sponsor_name = None
                for pattern in sponsor_patterns:
                    match = re.search(pattern, query, re.IGNORECASE)
                    if match:
                        sponsor_name = match.group(1).strip()
                        break
                        
                if sponsor_name:
                    if st.session_state.debug:
                        st.sidebar.write(f"Looking for bills by sponsor: {sponsor_name}")
                    
                    # Get bills where first chunk contains the sponsor
                    query_sql = f"""
                        WITH RankedChunks AS (
                            SELECT "chunk", "source_file", "chunk_index",
                                   ROW_NUMBER() OVER (PARTITION BY "source_file" ORDER BY "chunk_index") as rn
                            FROM BILL_CHUNKS
                        )
                        SELECT DISTINCT b."chunk", b."source_file", b."chunk_index"
                        FROM BILL_CHUNKS b
                        INNER JOIN RankedChunks r ON r."source_file" = b."source_file"
                        WHERE r.rn = 1 
                        AND r."chunk" LIKE '%By:%'
                        AND r."chunk" LIKE '%{sponsor_name}%'
                        ORDER BY b."source_file", b."chunk_index";
                    """
                    
                else:
                    # Use text search as last resort
                    query_sql = f"""
                        SELECT b."chunk", b."source_file", b."chunk_index"
                        FROM BILL_CHUNKS b
                        WHERE CONTAINS(b."chunk", '{query}')
                        {where_clause}
                        ORDER BY b."chunk_index"
                        LIMIT {st.session_state.num_retrieved_chunks}
                    """
        
        if st.session_state.debug:
            st.sidebar.write("Query SQL:", query_sql)
            st.sidebar.write("Selected columns:", columns)
            
        results = session.sql(query_sql).collect()
        
        if not results:
            if st.session_state.debug:
                st.error("No results found")
                # Let's check if the table exists and has the right structure
                check_sql = """
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'BILL_CHUNKS';
                """
                table_info = session.sql(check_sql).collect()
                st.sidebar.write("Table structure:", [(get_row_value(r, 'COLUMN_NAME'), get_row_value(r, 'DATA_TYPE')) for r in table_info])
            return "", []
            
        # Format results for context
        context_parts = []
        current_bill = None
        bill_chunks = []
        
        for r in results:
            try:
                if st.session_state.debug:
                    st.sidebar.write("Processing result:")
                    for col in columns:
                        st.sidebar.write(f"{col}: {get_row_value(r, col)}")
                
                # Extract bill info from chunk
                chunk_text = get_row_value(r, "chunk")
                if not chunk_text:
                    if st.session_state.debug:
                        st.error("No chunk text found in result")
                    continue
                    
                bill_name = get_row_value(r, 'source_file')
                if bill_name:
                    bill_name = bill_name.replace('.pdf', '')
                else:
                    bill_name = 'Unknown Bill'
                
                # If this is a new bill, process the previous bill's chunks
                if current_bill and current_bill != bill_name and bill_chunks:
                    # Process the accumulated chunks
                    full_text = "\n".join(bill_chunks)
                    bill_info = extract_bill_info_from_chunk(full_text)
                    header = format_bill_header(current_bill, bill_info)
                    context_parts.append(f"{header}\n\n{full_text}\n")
                    bill_chunks = []
                
                # Update current bill and add chunk
                current_bill = bill_name
                bill_chunks.append(chunk_text)
                
            except Exception as e:
                print("error 123")
                print(f"Error formatting result: {str(e)}")
                if st.session_state.debug:
                    st.error(f"Error formatting result: {str(e)}")
                    st.sidebar.write("Available columns:", columns)
                    st.sidebar.write("Raw result:", r)
                continue
        
        # Process the last bill's chunks
        if current_bill and bill_chunks:
            full_text = "\n".join(bill_chunks)
            bill_info = extract_bill_info_from_chunk(full_text)
            header = format_bill_header(current_bill, bill_info)
            context_parts.append(f"{header}\n\n{full_text}\n")
        
        if not context_parts:
            return "", []
            
        # Add appropriate summary based on query type
        if bill_query:
            summary = f"Here's the bill you asked for:\n\n"
            context_parts.insert(0, summary)
        elif bill_type:
            summary = f"Here's the most recent {bill_type} bill:\n\n"
            context_parts.insert(0, summary)
        elif sponsor_name:
            bill_count = len(context_parts)
            summary = f"Found {bill_count} bill{'s' if bill_count != 1 else ''} sponsored by {sponsor_name}:\n\n"
            context_parts.insert(0, summary)
            
        return "\n---\n".join(context_parts), results
        
    except Exception as e:
        print("error 124")
        print(f"Search error: {str(e)}", e.with_traceback(None))
        if st.session_state.debug:
            st.error(f"Search error: {str(e)}")
            st.sidebar.write("Full error:", str(e))
        return "", []

def extract_bill_info_from_chunk(chunk):
    """Extract bill information from the chunk text"""
    info = {
        'sponsor': 'Unknown Sponsor',
        'subtitle': None,
        'date_filed': None,
        'summary': None
    }
    
    # Extract sponsor
    sponsor_match = re.search(r'By:\s*(Senator[s]?\s+[^\\n]+)', chunk)
    if sponsor_match:
        info['sponsor'] = sponsor_match.group(1).strip()
    
    # Extract subtitle
    subtitle_match = re.search(r'Subtitle\s*\n((?:[^\n]+\n?)+?)(?=\n\s*\n|BE IT ENACTED)', chunk)
    if subtitle_match:
        info['subtitle'] = subtitle_match.group(1).strip()
    
    # Extract date
    date_match = re.search(r'(\d{2}/\d{2}/\d{4})', chunk)
    if date_match:
        info['date_filed'] = date_match.group(1)
    
    # Extract summary (everything between "AN ACT" and "BE IT ENACTED")
    summary_match = re.search(r'AN ACT\s+(.+?)(?=\n\s*\n\s*Subtitle|BE IT ENACTED)', chunk, re.DOTALL)
    if summary_match:
        summary = summary_match.group(1).strip()
        # Clean up the summary
        summary = re.sub(r'\s+', ' ', summary)  # Replace multiple whitespace with single space
        info['summary'] = summary
        
    return info

def format_bill_header(bill_name, bill_info):
    """Format the bill header with consistent styling"""
    header_parts = []
    
    # Bill name
    header_parts.append(f"## {format_bill_reference(bill_name)}")
    
    # Summary if available
    if bill_info['summary']:
        header_parts.append(f"**Summary**: {bill_info['summary']}")
    
    # Subtitle if different from summary
    if bill_info['subtitle'] and (not bill_info['summary'] or bill_info['subtitle'] != bill_info['summary']):
        header_parts.append(f"**Subtitle**: {bill_info['subtitle']}")
    
    # Metadata
    meta_parts = []
    if bill_info['sponsor']:
        meta_parts.append(f"**Sponsor**: {bill_info['sponsor']}")
    if bill_info['date_filed']:
        meta_parts.append(f"**Filed**: {bill_info['date_filed']}")
    
    if meta_parts:
        header_parts.append(" | ".join(meta_parts))
    
    return "\n\n".join(header_parts)

def create_prompt(user_question):
    """Create prompt for the language model"""
    # Get current bill statistics
    bill_stats = get_bill_stats(session)
    
    prompt_context = ""
    results = []
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
            if 'SOURCE_FILE' in result:
                bill_name = get_row_value(result, 'SOURCE_FILE')
                if bill_name:
                    bill_name = bill_name.replace('.pdf', '')
                else:
                    bill_name = 'Unknown Bill'
                bill_ref = format_bill_reference(bill_name)
                processed_context = processed_context.replace(bill_name, bill_ref)

    prompt = f"""
            [INST]
            You are a helpful AI assistant specifically focused on Arkansas legislative bills filed for the 2025 session. 
            Your purpose is to help users understand and navigate these bills. You provide summaries of bills and information about the bill filing.

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
            8. When asked about bill sponsors, check the bill_sponsor metadata field in the context. If available, format the response as "The bill is sponsored by [Sponsor Name]"
            9. For questions about bill types:
               - Files with 'HB' in the name are House Bills (filed in the House of Representatives)
               - Files with 'SB' in the name are Senate Bills (filed in the Senate)
            10. When asked about bills without a specific bill number:
                - For general queries like "tell me about a house bill" or "recent senate bill", look at the source_file names in the context
                - Prioritize the most recently filed bills (check date_filed metadata)
                - Include the bill type (House/Senate), bill number, sponsor, and a brief summary from the context
                - Example response: "Here's a recent House Bill: [HB1234](URL) filed on [date]. The bill is sponsored by [Sponsor Name] and it [brief summary of the bill's purpose]"
            11. Response Style:
                - Always respond in clear, professional English
                - Be polite and courteous
                - Keep responses concise and to the point
                - Focus on factual information without editorializing
                - Use proper grammar and punctuation

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
    return Complete(model, prompt, session=session)

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
                        bill_name = get_row_value(bill, 'SOURCE_FILE').replace('.pdf', '')
                        subtitle = get_row_value(bill, 'BILL_SUBTITLE') if 'BILL_SUBTITLE' in bill else 'No subtitle available'
                        sponsor = get_row_value(bill, 'BILL_SPONSOR') if 'BILL_SPONSOR' in bill else 'Unknown'
                        date_filed = get_row_value(bill, 'DATE_FILED') if 'DATE_FILED' in bill else None
                        
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

def init_main_container():
    """Initialize the main container with welcome message and styling"""
    # Add custom CSS for modern styling
    st.markdown("""
        <style>
        .main-header {
            text-align: center;
            padding: 1rem;
            margin-bottom: 2rem;
        }
        .subheader {
            text-align: center;
            color: #666;
            margin-bottom: 2rem;
        }
        .stats-container {
            text-align: center;
            padding: 1rem;
            background-color: #f8f9fa;
            border-radius: 10px;
            margin-bottom: 2rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Main header with modern emojis
    st.markdown("""
        <div class="main-header">
            <h1>🏛️ AI Bill Brief</h1>
        </div>
        <div class="subheader">
            <h3>Your Intelligent Guide to Arkansas Legislative Bills ⚖️</h3>
        </div>
    """, unsafe_allow_html=True)
    
    # Get current statistics
    stats = get_bill_stats(session)
    
    # Display stats in a modern container
    st.markdown("""
        <div class="stats-container">
            <h4>📊 Current Session Statistics</h4>
    """, unsafe_allow_html=True)
    
    # Create three columns for stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "📝 Total Bills",
            f"{stats['total_bills']}"
        )
    
    with col2:
        st.metric(
            "📅 Session",
            "2025 Regular"
        )
    
    with col3:
        if stats['latest_file_date']:
            latest_date = stats['latest_file_date'].strftime("%m/%d/%Y")
        else:
            latest_date = "N/A"
        st.metric(
            "🔄 Last Updated",
            latest_date
        )
    
    # Add a welcoming prompt
    st.markdown("""
        <div style="text-align: center; margin-top: 2rem; margin-bottom: 2rem;">
            <p>💬 Ask me anything about Arkansas Legislative Bills!</p>
            <p style="color: #666; font-size: 0.9em;">
                Try: "What's in Senate Bill 8?" or "Show me recent House Bills" 🔍
            </p>
        </div>
    """, unsafe_allow_html=True)

def init_sidebar():
    """Initialize the sidebar with configuration options and help text"""
    with st.sidebar:
        # Center the flag image at the top
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image("flag.png", use_column_width=True)
        
        st.markdown("## Welcome to AI Bill Brief! 👋")
        st.markdown("""
        Your AI assistant for exploring Arkansas Legislative Bills from the 2025 Regular Session.
        
        ### How to Use 🤔
        You can ask questions like:
        - "Tell me about Senate Bill 8"
        - "What bills has Senator Payton filed?"
        - "Show me a recent House Bill"
        - "What's the latest SB?"
        
        ### Tips 💡
        - Be specific with bill numbers (e.g., "SB8" or "HB1056")
        - You can ask about sponsors using their names
        - Request recent bills by type (House or Senate)
        
        ### Official Resources 📚
        For official bill information, visit:
        [Arkansas State Legislature](https://arkleg.state.ar.us/?ddBienniumSession=2025%2F2025R)
        
        ### Disclaimer ⚠️
        This is an AI assistant for informational purposes only. Always verify information through official sources.
        """)
        
        st.divider()
        
        # Debug mode toggle
        st.session_state.debug = st.checkbox("Debug Mode", value=True) ## Replace with False later
        
        # Number of chunks slider
        st.session_state.num_retrieved_chunks = st.slider(
            "Max Chunks Retrieved",
            min_value=1,
            max_value=10,
            value=5,
            help="Maximum number of text chunks to retrieve per query"
        )

def load_bills_to_snowflake():
    """
    Process all PDFs in the bills directory and load them into Snowflake
    """
    print("Loading bills to Snowflake...")
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
        
        # First, clear existing data
        print("Clearing existing data from BILL_CHUNKS table...")
        try:
            session.sql("DELETE FROM BILL_CHUNKS").collect()
            print("Successfully cleared existing data")
        except Exception as e:
            print(f"Error clearing data: {str(e)}")
        
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
                
                # Convert source_file to uppercase in pandas first
                df['source_file'] = df['source_file'].str.upper()
                
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
        
def main():
    """Main function to run the Streamlit app"""
    # Initialize Snowflake session
    global session
    session = get_snowflake_session()
    
    if not session:
        print("❌ Failed to connect to the database. Please check your credentials and try again.")
        return
    
    # Check for --load_bills argument
    if len(sys.argv) > 1 and sys.argv[1] == "--load_bills":
        print("Loading bills to Snowflake...")
        load_bills_to_snowflake()
        return
        
    # Initialize session state
    init_session_state()
    
    # Load service metadata
    st.session_state.service_metadata = get_service_metadata(session)
    
    # Initialize UI components
    init_sidebar()
    init_main_container()
    
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
                st.markdown(question)

            # Display assistant response in chat message container
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                
                # Show thinking animation
                with st.spinner("Thinking..."):
                    question = question.replace("'", "")
                    prompt, results = create_prompt(question)
                    print("Prompt:", prompt)
                    print("Results:", results)
                    # st.session_state.messages.append({"role": "assistant", "content": results})
                    message_placeholder.markdown(results)



if __name__ == "__main__":
    main()
