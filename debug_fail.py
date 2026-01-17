import requests
import re

BASE_URL = "http://localhost:5000"
s = requests.Session()

# 1. Start Exam
print("Starting exam...")
r = s.get(f"{BASE_URL}/start", allow_redirects=True)
if "/quiz" not in r.url:
    print("FAILED: Did not start")
    exit(1)

# 2. Intentionally Fail 7 times (for 30 q exam, >6 is fail)
# We assume standard 30 questions.
print("\nSubmitting 7 incorrect answers...")

for i in range(1, 8):
    # Retrieve current page to get context if needed
    current_url = r.url
    print(f"  Q{i}: URL before submit: {current_url}")
    
    if "/results" in current_url:
        print(f"FAILED EARLY? at iteration {i}")
        break

    # Submit a likely wrong answer
    # We don't know the correct one easily without parsing or cheating.
    # We can try to send 'WRONG_ANSWER' as the option.
    r = s.post(f"{BASE_URL}/answer", data={"option": "DEFINITELY_WRONG_ANSWER_xyz"}, allow_redirects=True)
    
    if "/results" in r.url:
        print(f"SUCCESS: Redirected to results after {i} incorrect answers.")
        break
    else:
        print(f"  Continued to next question (Status: {r.status_code})")

if "/results" not in r.url:
    print("FAILED: Did not redirect to results after 7 wrong answers.")
else:
    print("Test Complete.")
