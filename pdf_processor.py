import os
import json
import time
import typing
import pypdf
from google import genai
from pydantic import BaseModel

class Question(BaseModel):
    category: str
    question: str
    options: list[str]
    correct_answer: str
    explanation: str

class QuizBatch(BaseModel):
    questions: list[Question]

def extract_text_from_pdf(stream) -> str:
    """Extracts text from a PDF file stream."""
    try:
        reader = pypdf.PdfReader(stream)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return ""

def generate_quiz_from_text(text: str) -> list[dict]:
    """
    Uses Gemini (via google-genai SDK) to generate a quiz from the provided text.
    Returns a list of question dictionaries.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")

    client = genai.Client(api_key=api_key)
    
    # Use Flash for speed and cost effectiveness
    model_id = "gemini-2.0-flash"

    all_questions = []
    target_count = 200
    batch_size = 50
    batches = target_count // batch_size
    
    for i in range(batches):
        print(f"Generating batch {i+1}/{batches}...")
        prompt = f"""
        You are an expert exam creator. based on the following text, create {batch_size} UNIQUE multiple-choice questions.
        This is batch {i+1} of {batches}. Ensure these questions cover different parts of the text if possible.
        The questions should be challenging but fair, directly derivable from the text provided.
        """
        
        max_retries = 3
        retry_delay = 60
        
        for attempt in range(max_retries):
            try:
                # Use structured generation with Pydantic model
                response = client.models.generate_content(
                    model=model_id,
                    contents=[prompt, text],
                    config={
                        'response_mime_type': 'application/json',
                        'response_schema': QuizBatch,
                    },
                )
                
                # Parse response
                batch_data = response.parsed
                if not batch_data or not batch_data.questions:
                    print(f"Empty batch received in batch {i+1}")
                    raise ValueError("Empty response")

                # Convert Pydantic models to dicts
                batch_questions = [q.model_dump() for q in batch_data.questions]
                
                # Add to total
                all_questions.extend(batch_questions)
                
                # Success, break retry loop but sleep before next batch
                time.sleep(5) 
                break
                
            except Exception as e:
                print(f"Error in batch {i+1} attempt {attempt+1}: {e}")
                if "429" in str(e) or "quota" in str(e).lower() or "resource_exhausted" in str(e).lower():
                    sleep_time = retry_delay * (2 ** attempt)
                    print(f"Rate limit hit. Sleeping for {sleep_time}s...")
                    time.sleep(sleep_time)
                else:
                    # Non-retriable error (or we decide not to retry)
                    break

    # Post-process: Add IDs and cleaning
    validated_questions = []
    seen_questions = set()
    
    for i, q in enumerate(all_questions):
        # Basic validation (Pydantic handles most, but check for empty fields if needed)
        
        # Dedup based on question text
        q_text = q["question"].strip().lower()
        if q_text in seen_questions:
            continue
        seen_questions.add(q_text)
        
        # ID assignment (1-indexed)
        q["id"] = i + 1
        validated_questions.append(q)
            
    return validated_questions
