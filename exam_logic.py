import json
import random
import os

def load_questions(filepath="question_pool/questions.json"):
    """Loads questions from the JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Question file not found at {filepath}")
    
    with open(filepath, "r") as f:
        return json.load(f)

def generate_exam(questions):
    """
    Generates a 30-question exam with the following distribution:
    - Road Signs & Signals: 5-8 questions
    - Traffic Laws: 10-12 questions
    - Safe Driving Practices: 10-12 questions
    """
    
    # Categorize questions
    road_signs = [q for q in questions if q["category"] == "Road Signs & Signals"]
    traffic_laws = [q for q in questions if q["category"] == "Traffic Laws"]
    safe_driving = [q for q in questions if q["category"] == "Safe Driving Practices"]
    
    # Determine counts for this session
    # We need a total of 30.
    # Let's pick random counts within ranges, then adjust to ensure sum is 30.
    
    # Strategy: Pick a random number for two categories, calculate the third.
    # If the third is out of bounds, retry.
    
    while True:
        n_signs = random.randint(5, 8)
        n_laws = random.randint(10, 12)
        n_safe = 30 - n_signs - n_laws
        
        if 10 <= n_safe <= 12:
            break
            
    # Select questions
    selected_signs = random.sample(road_signs, min(n_signs, len(road_signs)))
    selected_laws = random.sample(traffic_laws, min(n_laws, len(traffic_laws)))
    selected_safe = random.sample(safe_driving, min(n_safe, len(safe_driving)))
    
    exam_questions = selected_signs + selected_laws + selected_safe
    random.shuffle(exam_questions)
    
    return exam_questions

if __name__ == "__main__":
    # Test the logic
    try:
        all_questions = load_questions()
        exam = generate_exam(all_questions)
        print(f"Generated exam with {len(exam)} questions.")
        
        # Verify distribution
        counts = {
            "Road Signs & Signals": 0,
            "Traffic Laws": 0,
            "Safe Driving Practices": 0
        }
        for q in exam:
            counts[q["category"]] += 1
            
        print("Distribution:")
        for cat, count in counts.items():
            print(f"  {cat}: {count}")
            
    except Exception as e:
        print(f"Error: {e}")
