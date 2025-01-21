# AI Bill Brief

AI Bill Brief is a revolutionary tool that democratizes access to legislative information by combining the power of Snowflake, Mistral LLM, and advanced AI technologies. This application transforms complex legislative bills into easily digestible insights, making civic engagement more accessible to everyone.

## About

This project was created for the [RAG 'n' ROLL: Amp up Search with Snowflake & Mistral hackathon](https://snowflake-mistral-rag.devpost.com/) on DevPost. The hackathon challenges developers to build innovative Retrieval Augmented Generation (RAG) applications using Snowflake Cortex Search for retrieval, Mistral LLM on Snowflake Cortex for generation, and Streamlit Community Cloud for the frontend.

## Impact & Outcomes

- **Accessibility**: Simplifies complex legislative language for the general public
- **Efficiency**: Reduces the time required to understand proposed bills through AI-powered summaries
- **Transparency**: Encourages informed civic engagement by making legislative data more accessible
- **Democratic Participation**: Empowers citizens to actively participate in the legislative process

## Features

- **PDF Processing**: 
  - Automatic processing of legislative bills
  - Metadata extraction including date filed, subtitle, and sponsor
  - Efficient chunking for better context retrieval

- **AI-Powered Search**: 
  - Context-aware retrieval using Snowflake's Cortex framework
  - Natural language bill queries
  - Maintains chat history for better conversation flow

- **Modern UI/UX**:
  - Clean, responsive interface with custom styling
  - Light purple theme with white chat containers
  - Centered chat input for better usability

- **Advanced Features**:
  - Configurable model selection
  - Adjustable context chunks
  - Debug mode for development

## Technology Stack

- **Retrieval**: Snowflake Cortex Search
- **Generation**: Mistral LLM (mistral-large2) on Snowflake Cortex
- **Frontend**: Streamlit
- **Data Processing**: PyPDF2 and langchain
- **Database**: Snowflake

## Prerequisites

- Python 3.8 or higher
- Snowflake account with appropriate permissions
- Required Python packages (see `requirements.txt`)
- Arkansas state flag image (`flag.png`) in the root directory

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/DEV_AIBillBrief.git
cd DEV_AIBillBrief
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Fill in your Snowflake credentials:
```bash
SNOWFLAKE_ACCOUNT=<your-account-identifier>
SNOWFLAKE_USER=<your-username>
SNOWFLAKE_PASSWORD=<your-password>
SNOWFLAKE_ROLE=<your-role>
SNOWFLAKE_WAREHOUSE=<your-warehouse>
SNOWFLAKE_DATABASE=<your-database>
SNOWFLAKE_SCHEMA=<your-schema>
```

4. Add required assets:
   - Place the Arkansas state flag image as `flag.png` in the root directory
   - Place your PDF bills in the `bills` directory

## Usage

1. Run the Streamlit application:
```bash
streamlit run local_streamlit_app.py
```

2. Use the web interface to:
   - Search through bill contents
   - Ask questions about specific bills
   - Find bills by sponsor
   - Browse recent bills
   - Get AI-powered insights using natural language queries

## Project Structure

- `local_streamlit_app.py`: Main Streamlit application
- `local_pdf_processor.py`: PDF processing and metadata extraction
- `requirements.txt`: Python dependencies
- `.env.example`: Template for environment variables
- `bills/`: Directory for PDF files
- `csv_files/`: Output directory for processed files

## Security

- Sensitive credentials are managed through environment variables
- The `.env` file containing credentials is ignored by git
- Use `.env.example` as a template for setup

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with Snowflake's Cortex framework
- Powered by Streamlit
- PDF processing with pdfplumber
- Natural language processing by Mistral AI
