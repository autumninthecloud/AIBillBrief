import os
import PyPDF2
import pandas as pd
from langchain.text_splitter import RecursiveCharacterTextSplitter
import re
from datetime import datetime
import traceback

class LocalPDFProcessor:
    def __init__(self, pdf_folder, output_folder):
        self.pdf_folder = pdf_folder
        self.output_folder = output_folder
        os.makedirs(self.output_folder, exist_ok=True)

    def read_pdf(self, pdf_path):
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text().replace('\n', ' ').replace('\0', ' ')
        return text

    def extract_metadata_from_first_page(self, pdf_path):
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            if len(reader.pages) > 0:
                first_page_text = reader.pages[0].extract_text()
                
                # Extract date filed
                bottom_text = first_page_text[-500:]
                date_pattern = r'(\d{2}/\d{2}/\d{4}\s+\d{1,2}:\d{2}:\d{2}\s+(?:AM|PM)\s+WFP\d{3})'
                date_match = re.search(date_pattern, bottom_text)
                date_filed = None
                if date_match:
                    date_str = date_match.group(1)
                    try:
                        datetime_str = ' '.join(date_str.split()[:-1])
                        date_filed = pd.to_datetime(datetime_str)
                    except Exception as e:
                        print(f"Error parsing date from {date_str}: {e}")

                # Extract subtitle - looking for text after "SUBTITLE:" or similar patterns
                subtitle_patterns = [
                    r'SUBTITLE:?\s*([^\n]+)',
                    r'Subtitle:?\s*([^\n]+)',
                    r'SUBTITLE\s+(?:OF\s+)?(?:THE\s+)?(?:BILL)?:?\s*([^\n]+)'
                ]
                
                bill_subtitle = None
                for pattern in subtitle_patterns:
                    subtitle_match = re.search(pattern, first_page_text[:1500])
                    if subtitle_match:
                        bill_subtitle = subtitle_match.group(1).strip()
                        break

                # Extract bill sponsor - looking for specific patterns
                sponsor_patterns = [
                    r'By(?:\sRepresentative|\sSenator)\s+([A-Z][A-Za-z\s,.-]+?)(?:\n|,|\s{2,})',
                    r'Sponsored by:\s*([A-Z][A-Za-z\s,.-]+?)(?:\n|,|\s{2,})',
                    r'SPONSOR(?:ED)?\s*(?:BY)?\s*:?\s*([A-Z][A-Za-z\s,.-]+?)(?:\n|,|\s{2,})'
                ]
                
                bill_sponsor = None
                for pattern in sponsor_patterns:
                    sponsor_match = re.search(pattern, first_page_text[:1000])
                    if sponsor_match:
                        bill_sponsor = sponsor_match.group(1).strip()
                        break

                return {
                    'date_filed': date_filed,
                    'bill_subtitle': bill_subtitle,
                    'bill_sponsor': bill_sponsor
                }
        return {
            'date_filed': None,
            'bill_subtitle': None,
            'bill_sponsor': None
        }

    def chunk_text(self, text):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=300,
            length_function=len
        )
        return text_splitter.split_text(text)

    def process_pdfs(self):
        for pdf_file in os.listdir(self.pdf_folder):
            if pdf_file.endswith('.pdf'):
                pdf_path = os.path.join(self.pdf_folder, pdf_file)
                text = self.read_pdf(pdf_path)
                chunks = self.chunk_text(text)
                metadata = self.extract_metadata_from_first_page(pdf_path)
                self.save_chunks_to_csv(pdf_file, chunks, metadata)

    def save_chunks_to_csv(self, pdf_file, chunks, metadata):
        try:
            print(f"Saving chunks for {pdf_file}...")
            csv_file_path = os.path.join(self.output_folder, pdf_file.replace('.pdf', '.csv'))
            
            # Create DataFrame with chunks
            df = pd.DataFrame({
                'chunk': chunks,
                'chunk_index': range(len(chunks)),
                'source_file': pdf_file,
                'chunk_length': [len(chunk) for chunk in chunks],
                'timestamp': pd.Timestamp.now(),
                'date_filed': metadata.get('date_filed'),
                'bill_subtitle': metadata.get('bill_subtitle'),
                'bill_sponsor': metadata.get('bill_sponsor')
            })
            
            # Convert timestamps to proper format
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
            if df['date_filed'].notna().any():
                df['date_filed'] = pd.to_datetime(df['date_filed']).dt.strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"Created DataFrame with {len(chunks)} chunks")
            df.to_csv(csv_file_path, index=False)
            print(f"Saved {csv_file_path}")
            return df
        except Exception as e:
            print(f"Error saving chunks to CSV for {pdf_file}: {str(e)}")
            print(f"Error type: {type(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return None

# Example usage
pdf_folder = 'bills'
output_folder = 'csv_files'
processor = LocalPDFProcessor(pdf_folder, output_folder)
processor.process_pdfs()
