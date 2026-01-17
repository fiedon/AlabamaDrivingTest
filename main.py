from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import exam_logic
import os
import random
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

app = Flask(__name__)
app.secret_key = "super_secret_key_change_this_for_prod"  # Needed for session

# Load questions once at startup
try:
    ALL_QUESTIONS = exam_logic.load_questions()
    # Create lookup map for easy access
    QUESTION_MAP = {q["id"]: q for q in ALL_QUESTIONS}
    print(f"Loaded {len(ALL_QUESTIONS)} questions.")
except Exception as e:
    print(f"Error loading questions: {e}")
    ALL_QUESTIONS = []
    QUESTION_MAP = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/start")
def start_exam():
    """Initializes a new exam session."""
    session.clear()
    
    # Generate new exam questions
    current_exam = exam_logic.generate_exam(ALL_QUESTIONS)
    
    # Store ONLY IDs in session to keep cookie small
    session["exam_ids"] = [q["id"] for q in current_exam]
    session["current_index"] = 0
    session["score"] = 0
    session["answers"] = {} # question_id: selected_option
    session["incorrect_answers"] = [] # detailed list for review
    
    return redirect(url_for("quiz"))

@app.route("/upload", methods=["POST"])
def upload_pdf():
    """Handles PDF upload and custom exam generation."""
    if "file" not in request.files:
        return redirect(url_for("index"))
        
    file = request.files["file"]
    if file.filename == "":
        return redirect(url_for("index"))

    if not os.environ.get("GEMINI_API_KEY"):
         # In a real app, use flash messages. For now, simple error page or redirect.
         return "Error: GEMINI_API_KEY not set in environment.", 500

    try:
        import pdf_processor
        
        # Process PDF
        text = pdf_processor.extract_text_from_pdf(file)
        if not text:
             return "Error: Could not extract text from PDF.", 400
             
        # Generate Questions
        custom_questions = pdf_processor.generate_quiz_from_text(text)
        
        if not custom_questions:
            return "Error: Failed to generate questions from text. Please try again.", 500
            
        # Store in session
        session.clear()
        session["custom_questions"] = custom_questions
        # Create a map for these custom questions in the session (or rely on index)
        # To keep it simple, we'll store the full list in session for now, 
        # or just store IDs if we had a persistent store. 
        # Since we don't have a DB, session is the store.
        # But session size is limited (4096 bytes usually for client side cookies).
        # 30 questions with text might exceed cookie size!
        
        # CRITICAL: Flask default session is client-side cookie. 
        # Storing 30 full questions will likely fail or get truncated.
        # We should use server-side session or just store a temporary global?
        # Global is bad for multi-user.
        # For this single-user local app, we can maybe cheat with a global dict keyed by session ID
        # or just rely on the user running this locally.
        
        # Let's use a global cache keyed by a random ID stored in session.
        exam_id = os.urandom(8).hex()
        session["exam_id"] = exam_id
        session["current_index"] = 0
        session["score"] = 0
        session["answers"] = {}
        session["incorrect_answers"] = []
        session["is_custom"] = True
        
        # Global storage for custom exams (in-memory)
        if not hasattr(app, "custom_exams"):
            app.custom_exams = {}
        app.custom_exams[exam_id] = custom_questions
        
        return redirect(url_for("quiz"))
        
    except Exception as e:
        print(f"Upload error: {e}")
        return f"An error occurred: {e}", 500

@app.route("/quiz")
def quiz():
    """Displays the current question."""
    
    # Check if custom exam
    is_custom = session.get("is_custom", False)
    exam_id = session.get("exam_id")
    
    questions = []
    
    if is_custom and exam_id:
        if not hasattr(app, "custom_exams"):
             app.custom_exams = {}
        questions = app.custom_exams.get(exam_id, [])
        if not questions:
            # Expired or restart
            return redirect(url_for("index"))
    else:
        # Standard Exam
        if "exam_ids" not in session:
            return redirect(url_for("index"))
        exam_ids = session["exam_ids"]
        # Reconstruct list from IDs
        questions = [QUESTION_MAP.get(qid) for qid in exam_ids if qid in QUESTION_MAP]

    idx = session.get("current_index", 0)
    
    if idx >= len(questions):
        return redirect(url_for("results"))
        
    question_data = questions[idx]
    
    return render_template(
        "quiz.html", 
        question=question_data, 
        index=idx + 1, 
        total=len(questions)
    )

@app.route("/answer", methods=["POST"])
def submit_answer():
    """Processes a user answer."""
    selected_option = request.form.get("option")
    if not selected_option:
        return redirect(url_for("quiz"))

    # Determine which set of questions we are using
    is_custom = session.get("is_custom", False)
    exam_id = session.get("exam_id")
    questions = []
    
    if is_custom and exam_id:
        if not hasattr(app, "custom_exams"):
             app.custom_exams = {}
        questions = app.custom_exams.get(exam_id, [])
    else:
        if "exam_ids" not in session:
            return redirect(url_for("index"))
        questions = [QUESTION_MAP.get(qid) for qid in session["exam_ids"] if qid in QUESTION_MAP]

    if not questions:
        return redirect(url_for("index"))

    # Get current question
    idx = session["current_index"]
    if idx >= len(questions):
        return redirect(url_for("results"))
        
    current_q = questions[idx]
    
    # Record answer
    # Use ID if available, otherwise index might have to do if IDs aren't unique in custom?
    # Custom IDs are 1..30 generated by LLM.
    q_id = current_q.get("id", idx)
    session["answers"][str(q_id)] = selected_option
    
    # Check correctness
    if selected_option == current_q["correct_answer"]:
        session["score"] += 1
    else:
        incorrect = session.get("incorrect_answers", [])
        # Optimize: Store minimal info. For standard exams, just ID is enough if we look it up later.
        # But for custom exams, we might not have a global map easily accessible in 'results' without loading session.
        # Compromise: Store simplified object.
        incorrect.append({
            "id": q_id,
            "user_answer": selected_option,
            # "question": ... # Don't store full text if possible, only needed for custom.
        })
        session["incorrect_answers"] = incorrect

        session["incorrect_answers"] = incorrect

    # Check for early failure
    # Pass rate is 80%. 
    # Max allowed wrong = total - ceil(total * 0.8)
    # e.g. 30 questions -> 24 needed -> 6 wrong allowed -> 7th wrong kills it.
    
    total_q = len(questions)
    pass_threshold = int(total_q * 0.8)
    max_wrong = total_q - pass_threshold
    
    current_wrong = len(session.get("incorrect_answers", []))
    
    if current_wrong > max_wrong:
        # User has failed
        return redirect(url_for("results"))

    # Move to next
    session["current_index"] += 1
    session.modified = True # Ensure session is saved
    
    return redirect(url_for("quiz"))

@app.route("/results")
def results():
    # Helper to get total count
    is_custom = session.get("is_custom", False)
    exam_id = session.get("exam_id")
    total = 0
    questions_map = {}
    
    if is_custom and exam_id:
         if hasattr(app, "custom_exams"):
             custom_qs = app.custom_exams.get(exam_id, [])
             total = len(custom_qs)
             questions_map = {q.get("id", i): q for i, q in enumerate(custom_qs)}
    elif "exam_ids" in session:
        total = len(session["exam_ids"])
        questions_map = QUESTION_MAP
    else:
        return redirect(url_for("index"))
        
    score = session.get("score", 0)
    passed = score >= (total * 0.8) # 80% pass rate generic
    
    # Reconstruct full incorrect details
    raw_incorrect = session.get("incorrect_answers", [])
    detailed_incorrect = []
    
    for item in raw_incorrect:
        qid = item.get("id")
        # Try to find question
        # For custom exams, IDs might be integers or strings, be careful with lookup
        q_data = questions_map.get(qid)
        if not q_data and str(qid) in questions_map: # Try string lookup
             q_data = questions_map.get(str(qid))
             
        if q_data:
            detailed_incorrect.append({
                "question": q_data["question"],
                "user_answer": item["user_answer"],
                "correct_answer": q_data["correct_answer"],
                "explanation": q_data["explanation"]
            })
    
    return render_template(
        "results.html", 
        score=score, 
        total=total, 
        passed=passed, 
        incorrect_answers=detailed_incorrect
    )

@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
