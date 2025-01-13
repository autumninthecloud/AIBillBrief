-- Set the context
USE ROLE ACCOUNTADMIN;
USE DATABASE SNOW_PDF;
USE SCHEMA PUBLIC;

-- Create a table to store the bill chunks with metadata
CREATE OR REPLACE TABLE BILL_CHUNKS (
    chunk TEXT,
    chunk_index NUMBER,
    source_file VARCHAR,
    chunk_length NUMBER,
    timestamp TIMESTAMP_NTZ,
    date_filed TIMESTAMP_NTZ,
    bill_subtitle TEXT,
    bill_sponsor VARCHAR
);

-- Create the Cortex Search Service with metadata fields
CREATE OR REPLACE CORTEX SEARCH SERVICE bill_search_service
ON TABLE BILL_CHUNKS (
    INPUT_DOCS => ARRAY_CONSTRUCT(
        OBJECT_CONSTRUCT(
            'text_fields', ARRAY_CONSTRUCT('chunk'),
            'metadata_fields', ARRAY_CONSTRUCT(
                'chunk_index',
                'source_file',
                'date_filed',
                'bill_subtitle',
                'bill_sponsor'
            )
        )
    )
)
MIN_TOKEN_OCCURRENCE => 2,
MAX_TOKEN_OCCURRENCE_PERCENTAGE => 80,
SIMILARITY_METRIC => 'COSINE';

-- Grant necessary permissions
GRANT ALL ON TABLE SNOW_PDF.PUBLIC.BILL_CHUNKS TO ROLE ACCOUNTADMIN;
GRANT USAGE ON CORTEX SEARCH SERVICE SNOW_PDF.PUBLIC.bill_search_service TO ROLE ACCOUNTADMIN;
