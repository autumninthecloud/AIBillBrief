import pdfplumber
import os
import csv
import snowflake.connector


def extract_text_from_pdfs(pdf_folder, output_folder):
    pdf_texts = []
    for pdf_file in os.listdir(pdf_folder):
        if pdf_file.endswith(".pdf"):
            pdf_path = os.path.join(pdf_folder, pdf_file)
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""

            # Print the extracted text for debugging purposes
            print(f"Extracted text from {pdf_file}:\n{text}\n")

            # Define the output CSV file path
            csv_file_path = os.path.join(output_folder, pdf_file.replace('.pdf', '.csv'))

            # Write the extracted text to a CSV file
            with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["file_name", "content"])
                writer.writerow([pdf_file, text])

            pdf_texts.append({"file_name": pdf_file, "content": text})

    return pdf_texts


def upload_to_snowflake(data, table_name, user, password, account, warehouse, database, schema):
    # Establish a connection to Snowflake
    conn = snowflake.connector.connect(
        user="ANRAINS",
        password="Giraffe23!",
        account="pib01610",
        warehouse="COMPUTE_WH",
        database="SNOW_PDF",
        schema="PUBLIC"
    )
    
    try:
        # Create a cursor object
        cur = conn.cursor()
        
        # Create table if not exists
        create_table_query = f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            file_name STRING,
            content STRING
        )
        '''
        cur.execute(create_table_query)

        # Insert data into the table
        insert_query = f"INSERT INTO {table_name} (file_name, content) VALUES (%s, %s)"
        cur.executemany(insert_query, [(item['file_name'], item['content']) for item in data])

    finally:
        # Close the cursor and connection
        cur.close()
        conn.close()


# Example usage
pdf_folder = "bills"
output_folder = "csv_files"
os.makedirs(output_folder, exist_ok=True)

# Extract text from PDFs
pdf_texts = extract_text_from_pdfs(pdf_folder, output_folder)

# Upload to Snowflake
upload_to_snowflake(
    data=pdf_texts,
    table_name='extracted_texts',
    user='<YOUR_USERNAME>',
    password='<YOUR_PASSWORD>',
    account='<YOUR_ACCOUNT_IDENTIFIER>',
    warehouse='<YOUR_WAREHOUSE>',
    database='<YOUR_DATABASE>',
    schema='<YOUR_SCHEMA>'
)
