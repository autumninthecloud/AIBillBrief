import os
import PyPDF2
import pandas as pd
from langchain.text_splitter import RecursiveCharacterTextSplitter

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

    def process_pdfs(self):
        for pdf_file in os.listdir(self.pdf_folder):
            if pdf_file.endswith('.pdf'):
                pdf_path = os.path.join(self.pdf_folder, pdf_file)
                text = self.read_pdf(pdf_path)
                chunks = self.chunk_text(text)
                self.save_chunks_to_csv(pdf_file, chunks)

    def chunk_text(self, text):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=300,
            length_function=len
        )
        return text_splitter.split_text(text)

    def save_chunks_to_csv(self, pdf_file, chunks):
        csv_file_path = os.path.join(self.output_folder, pdf_file.replace('.pdf', '.csv'))
        df = pd.DataFrame(chunks, columns=['chunk'])
        df.to_csv(csv_file_path, index=False)

# Example usage
pdf_folder = 'bills'
output_folder = 'csv_files'
processor = LocalPDFProcessor(pdf_folder, output_folder)
processor.process_pdfs()
