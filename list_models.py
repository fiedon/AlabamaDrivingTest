
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

try:
    print("Listing models...")
    # New SDK method for listing models might differ, let's assume client.models.list() based on patterns, 
    # but the instructions didn't explicitly show listing models. 
    # Checking documentation or making an educated guess based on 'client.models'.
    # Actually, usually it is client.models.list()
    for m in client.models.list():
        print(m.name)
except Exception as e:
    print(f"Error listing models: {e}")
