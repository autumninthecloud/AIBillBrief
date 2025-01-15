# AI Bill Brief

AI Bill Brief is a revolutionary tool that democratizes access to legislative information by combining the power of Snowflake, Mistral LLM, and advanced AI technologies. This application transforms complex legislative bills into easily digestible insights, making civic engagement more accessible to everyone.

## Impact & Outcomes

- **Accessibility**: Simplifies complex legislative language for the general public, making bills and policies understandable to all citizens
- **Efficiency**: Reduces the time required to understand proposed bills and policies through AI-powered summaries and natural language queries
- **Transparency**: Encourages informed civic engagement by making legislative data more accessible and understandable
- **Democratic Participation**: Empowers citizens to actively participate in the legislative process by better understanding the laws that affect them

## About

This project was created for the [RAG 'n' ROLL: Amp up Search with Snowflake & Mistral hackathon](https://snowflake-mistral-rag.devpost.com/) on DevPost. The hackathon challenges developers to build innovative Retrieval Augmented Generation (RAG) applications using:

- Cortex Search for retrieval
- Mistral LLM (mistral-large2) on Snowflake Cortex for generation
- Streamlit Community Cloud for front end

The competition aims to push the boundaries of AI technology and showcase how RAG applications can revolutionize information interaction, with $10,000 in prizes available for innovative solutions.

## Features

- **PDF Processing**: 
  - Automatic processing of legislative bills
  - Metadata extraction including date filed, subtitle, and sponsor
  - Efficient chunking for better context retrieval

- **AI-Powered Search**: 
  - Uses Snowflake's Cortex framework for intelligent document search
  - Context-aware retrieval for more relevant results
  - Maintains chat history for better conversation flow

- **Modern UI/UX**:
  - Clean, modern interface with custom styling
  - Centered chat input for better usability
  - Responsive design with proper spacing
  - Light purple theme with white chat containers

- **Advanced Features**:
  - Natural language bill queries
  - Configurable model selection
  - Adjustable context chunks
  - Debug mode for development

## Technology Stack

This project implements the hackathon's required technology stack:
- **Retrieval**: Snowflake Cortex Search for efficient document retrieval
- **Generation**: Mistral LLM (mistral-large2) on Snowflake Cortex for natural language processing
- **Frontend**: Streamlit for an interactive and user-friendly interface
- **Data Processing**: PyPDF2 and langchain for PDF processing
- **Database**: Snowflake for secure and scalable data storage

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
   - Fill in your Snowflake credentials in the `.env` file:
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

1. Ensure all prerequisites are met and assets are in place

2. Run the Streamlit application:
```bash
streamlit run local_streamlit_app.py
```

3. Use the web interface to:
   - Search through bill contents
   - Ask questions about specific bills (e.g., "Tell me about Senate Bill 8")
   - Find bills by sponsor (e.g., "What bills has Senator Payton filed?")
   - Browse recent bills (e.g., "Show me a recent House Bill")
   - Get AI-powered insights using natural language queries

## Project Structure

- `local_streamlit_app.py`: Main Streamlit application with UI and LLM integration
- `local_pdf_processor.py`: PDF processing and metadata extraction
- `requirements.txt`: Python dependencies
- `.env.example`: Template for environment variables
- `bills/`: Directory for PDF files
- `csv_files/`: Output directory for processed files

## Dependencies

Key Python packages:
- streamlit
- snowflake-connector-python
- snowflake-snowpark-python
- snowflake-cortex
- PyPDF2
- langchain
- pandas
- python-dotenv

## Development

This project was developed as part of the RAG 'n' ROLL hackathon (December 2023 - January 2024) and follows the competition's technical requirements:

1. Uses Snowflake Cortex Search for efficient document retrieval
2. Implements Mistral LLM (mistral-large2) for natural language processing
3. Provides a user interface through Streamlit Community Cloud
4. Focuses on Retrieval Augmented Generation (RAG) for enhanced search capabilities

The application demonstrates how RAG can be used to make legislative documents more accessible and understandable through AI-powered search and analysis.

## Security

- Sensitive credentials are managed through environment variables
- The `.env` file containing actual credentials is ignored by git
- Use `.env.example` as a template for setting up your own credentials

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
- Natural language processing powered by Mistral AI's large language models
