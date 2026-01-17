# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pypdf",
# ]
# ///

import pypdf
import os

def extract_text_from_pdf(pdf_path, output_path):
    print(f"Extracting text from {pdf_path}...")
    try:
        reader = pypdf.PdfReader(pdf_path)
        full_text = ""
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            # Add page marker
            full_text += f"\n[[PAGE_{i+1}]]\n"
            full_text += text
            print(f"Extracted page {i+1}")
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full_text)
        print(f"Text extracted to {output_path}")
    except Exception as e:
        print(f"Error extracting text: {e}")

if __name__ == "__main__":
    pdf_path = "documents/ALEA DL Manual.pdf"
    output_path = "documents/manual_text.txt"
    
    if not os.path.exists(pdf_path):
        print(f"Error: File not found at {pdf_path}")
    else:
        extract_text_from_pdf(pdf_path, output_path)
