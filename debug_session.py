import requests
import re

BASE_URL = "http://localhost:5000"
s = requests.Session()

# 1. Start Exam
print("Starting exam...")
r = s.get(f"{BASE_URL}/start", allow_redirects=True)
print(f"Start URL: {r.url}, Status: {r.status_code}")

if "/quiz" not in r.url:
    print("FAILED: Did not redirect to quiz")
    exit(1)

# Extract content to find current question info
content = r.text
match = re.search(r"Question (\d+) / (\d+)", content)
if match:
    print(f"Current Question: {match.group(1)} / {match.group(2)}")
else:
    print("FAILED: Could not find question number")
    exit(1)

# 2. Submit Answer
print("\nSubmitting answer...")
# We need to find valid options or just send a dummy one if validation isn't strict?
# The app checks: if selected_option == current_q["correct_answer"]:
# It accepts any string in 'option'.
r = s.post(f"{BASE_URL}/answer", data={"option": "Test Answer"}, allow_redirects=True)
print(f"Answer URL: {r.url}, Status: {r.status_code}")

# 3. Check Next Question
content = r.text
match = re.search(r"Question (\d+) / (\d+)", content)
if match:
    current = int(match.group(1))
    print(f"Current Question: {current} / {match.group(2)}")
    if current == 2:
        print("SUCCESS: Moved to question 2")
    else:
        print(f"FAILED: Still on question {current}")
else:
    # check if results?
    if "/results" in r.url:
         print("Moved to results (Exam finished?)")
    else:
         print("FAILED: Unknown state")
         print(content[:500])
