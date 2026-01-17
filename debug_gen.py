
import os
from dotenv import load_dotenv
import pdf_processor

load_dotenv()

print("Testing PDF Processor...")
pdf_path = "documents/ALEA DL Manual.pdf"

if not os.path.exists(pdf_path):
    print(f"PDF not found at {pdf_path}")
    exit(1)

print(f"Extracting text from {pdf_path}...")
with open(pdf_path, "rb") as f:
    text = pdf_processor.extract_text_from_pdf(f)

print(f"Extracted {len(text)} characters.")
if not text:
    print("Text extraction failed.")
    exit(1)

print("Generating questions (truncated test)...")
# Monkey patch generate_quiz_from_text to reduce batch count for testing if needed, 
# but let's just run it and see the error.
try:
    questions = pdf_processor.generate_quiz_from_text(text)
    print(f"Generated {len(questions)} questions.")
except Exception as e:
    print(f"Error: {e}")
