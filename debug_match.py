
import re

def normalize(text):
    # Lowercase and remove all non-alphanumeric (keep spaces)
    text = text.lower()
    return re.sub(r'[^a-z0-9\s]', '', text).strip()

manual_text = """
[[PAGE_1]]
...
[[PAGE_21]]
Turns
...
Right turns
To make a right turn, use the following method:
• Signaling well in advance.
• Enter the right lane well in advance of the turn and make a tight turn into the right lane of the cross street.
"""

# Real manual text sample (simulated for now, will read file in real run)
with open("documents/manual_text.txt", "r", encoding="utf-8") as f:
    full_manual = f.read()

# Remove page markers for search
clean_manual = re.sub(r'\[\[PAGE_\d+\]\]', ' ', full_manual)
norm_manual = normalize(clean_manual)

# Target explanation
target = "Enter the right lane well in advance of the turn and make a tight turn into the right lane of the cross street."
norm_target = normalize(target)

print(f"Target: '{norm_target}'")
print(f"Found in manual: {norm_target in norm_manual}")

if not norm_target in norm_manual:
    print("Match failed. Finding partial match...")
    # split into words and find max overlap
    words = norm_target.split()
    for i in range(len(words)):
        sub = " ".join(words[i:i+5]) # 5 word chunks
        if sub in norm_manual:
            print(f"Found chunk: '{sub}'")
        else:
            print(f"Failed chunk: '{sub}'")
            break

