import customtkinter as ctk
import exam_logic
from tkinter import messagebox
from PIL import Image
import os

# Set theme
ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window setup
        self.title("Alabama Driver License Prep")
        self.geometry("800x600")
        self.minsize(600, 500)

        # Data
        self.all_questions = exam_logic.load_questions()
        self.current_exam = []
        self.current_question_index = 0
        self.score = 0
        self.user_answers = {} # Map question ID to selected option

        # Grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Initialize Frames
        self.start_frame = StartFrame(self, self.start_exam)
        self.quiz_frame = QuizFrame(self, self.submit_answer, self.next_question)
        self.results_frame = ResultsFrame(self, self.restart_exam)

        # Show Start Screen
        self.show_frame("start")

    def show_frame(self, frame_name):
        """Switches between frames."""
        self.start_frame.grid_forget()
        self.quiz_frame.grid_forget()
        self.results_frame.grid_forget()

        if frame_name == "start":
            self.start_frame.grid(row=0, column=0, sticky="nsew")
        elif frame_name == "quiz":
            self.quiz_frame.grid(row=0, column=0, sticky="nsew")
        elif frame_name == "results":
            self.results_frame.grid(row=0, column=0, sticky="nsew")

    def start_exam(self):
        """Generates a new exam and switches to the quiz screen."""
        try:
            self.current_exam = exam_logic.generate_exam(self.all_questions)
            self.current_question_index = 0
            self.score = 0
            self.user_answers = {}
            self.incorrect_answers = []
            self.load_question()
            self.show_frame("quiz")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start exam: {e}")

    def load_question(self):
        """Loads the current question into the quiz frame."""
        question_data = self.current_exam[self.current_question_index]
        is_last = self.current_question_index == len(self.current_exam) - 1
        self.quiz_frame.update_question(
            question_data, 
            self.current_question_index + 1, 
            len(self.current_exam),
            is_last
        )

    def submit_answer(self, selected_option):
        """Records the user's answer."""
        # This is called when 'Next' or 'Submit' is clicked, passing the selected value
        current_q = self.current_exam[self.current_question_index]
        
        # Check correctness
        if selected_option == current_q["correct_answer"]:
            self.score += 1
        else:
            self.incorrect_answers.append({
                "question": current_q["question"],
                "user_answer": selected_option,
                "correct_answer": current_q["correct_answer"],
                "explanation": current_q["explanation"]
            })
            
        self.user_answers[current_q["id"]] = selected_option
        
        # Move to next or finish
        if self.current_question_index < len(self.current_exam) - 1:
            self.current_question_index += 1
            self.load_question()
        else:
            self.finish_exam()

    def next_question(self):
        # Wrapper if needed, but logic is in submit_answer for now
        pass

    def finish_exam(self):
        """Calculates score and shows results."""
        passed = self.score >= 24
        self.results_frame.update_results(self.score, len(self.current_exam), passed, self.incorrect_answers)
        self.show_frame("results")

    def restart_exam(self):
        """Returns to start screen."""
        self.show_frame("start")


class StartFrame(ctk.CTkFrame):
    def __init__(self, master, start_callback):
        super().__init__(master)
        self.start_callback = start_callback

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        self.label_title = ctk.CTkLabel(self, text="Alabama Driver License Prep", font=("Roboto", 32, "bold"))
        self.label_title.grid(row=1, column=0, pady=20, padx=20)

        self.label_subtitle = ctk.CTkLabel(self, text="Practice for the official written exam.\n30 Questions | 80% to Pass", font=("Roboto", 16))
        self.label_subtitle.grid(row=2, column=0, pady=10)

        self.btn_start = ctk.CTkButton(self, text="Start Exam", command=self.start_callback, font=("Roboto", 18), height=50, width=200)
        self.btn_start.grid(row=3, column=0, pady=40)


class QuizFrame(ctk.CTkFrame):
    def __init__(self, master, submit_callback, next_callback):
        super().__init__(master)
        self.submit_callback = submit_callback
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # Question area expands

        # Progress
        self.label_progress = ctk.CTkLabel(self, text="Question 1/30", font=("Roboto", 14))
        self.label_progress.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 0))

        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        self.progress_bar.set(0)

        # Question
        self.label_question = ctk.CTkLabel(self, text="Question Text", font=("Roboto", 20), wraplength=700, justify="left")
        self.label_question.grid(row=2, column=0, sticky="nw", padx=20, pady=(20, 10))

        # Image Label (Hidden by default)
        self.label_image = ctk.CTkLabel(self, text="")
        self.label_image.grid(row=3, column=0, pady=10)

        # Options
        self.options_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.options_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=10)
        self.radio_var = ctk.StringVar(value="")
        self.radio_buttons = []

        # Buttons
        self.btn_action = ctk.CTkButton(self, text="Next", command=self.on_action, font=("Roboto", 16), height=40)
        self.btn_action.grid(row=5, column=0, sticky="e", padx=20, pady=20)

    def update_question(self, question_data, index, total, is_last):
        self.label_progress.configure(text=f"Question {index}/{total} - {question_data['category']}")
        self.progress_bar.set(index / total)
        self.label_question.configure(text=question_data["question"])
        
        # Handle Image
        if question_data.get("image"):
            image_path = os.path.join("images", question_data["image"])
            if os.path.exists(image_path):
                try:
                    pil_image = Image.open(image_path)
                    # Resize if too big, keeping aspect ratio
                    max_size = (400, 300)
                    pil_image.thumbnail(max_size)
                    
                    ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=pil_image.size)
                    self.label_image.configure(image=ctk_image)
                    self.label_image.image = ctk_image # Keep reference
                    self.label_image.grid(row=3, column=0, pady=10) # Show
                except Exception as e:
                    print(f"Error loading image: {e}")
                    self.label_image.grid_forget()
            else:
                self.label_image.grid_forget()
        else:
            self.label_image.grid_forget()
        
        # Clear old options
        for btn in self.radio_buttons:
            btn.destroy()
        self.radio_buttons.clear()
        self.radio_var.set("") # Reset selection

        # Create new options
        for option in question_data["options"]:
            btn = ctk.CTkRadioButton(
                self.options_frame, 
                text=option, 
                variable=self.radio_var, 
                value=option,
                font=("Roboto", 16)
            )
            btn.pack(anchor="w", pady=10, padx=10)
            self.radio_buttons.append(btn)

        self.btn_action.configure(text="Submit Exam" if is_last else "Next Question")
        self.btn_action.configure(state="disabled") # Disable until selected
        
        # Enable button when option selected
        # CustomTkinter radio buttons don't have a direct command for this easily without trace
        # So we'll use a trace on the variable
        self.radio_var.trace_add("write", self.enable_button)

    def enable_button(self, *args):
        self.btn_action.configure(state="normal")

    def on_action(self):
        selected = self.radio_var.get()
        if selected:
            self.submit_callback(selected)


class ResultsFrame(ctk.CTkFrame):
    def __init__(self, master, restart_callback):
        super().__init__(master)
        self.restart_callback = restart_callback

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        self.label_title = ctk.CTkLabel(self, text="Exam Completed", font=("Roboto", 32, "bold"))
        self.label_title.grid(row=1, column=0, pady=20)

        self.label_score = ctk.CTkLabel(self, text="Score: 0/30", font=("Roboto", 24))
        self.label_score.grid(row=2, column=0, pady=10)

        self.label_status = ctk.CTkLabel(self, text="PASS", font=("Roboto", 28, "bold"), text_color="green")
        self.label_status.grid(row=3, column=0, pady=20)

        self.review_frame = ctk.CTkScrollableFrame(self, label_text="Review Incorrect Answers", width=700, height=300)
        self.review_frame.grid(row=4, column=0, sticky="nsew", padx=20, pady=10)

        self.btn_restart = ctk.CTkButton(self, text="Restart Exam", command=self.restart_callback, font=("Roboto", 18), height=50, width=200)
        self.btn_restart.grid(row=5, column=0, pady=20)

    def update_results(self, score, total, passed, incorrect_answers):
        self.label_score.configure(text=f"Score: {score}/{total} ({(score/total)*100:.1f}%)")
        if passed:
            self.label_status.configure(text="PASSED", text_color="#2CC985") # Green
        else:
            self.label_status.configure(text="FAILED", text_color="#FF4B4B") # Red

        # Clear previous review
        for widget in self.review_frame.winfo_children():
            widget.destroy()
            
        if not incorrect_answers:
            lbl = ctk.CTkLabel(self.review_frame, text="Perfect Score! No incorrect answers.", font=("Roboto", 16))
            lbl.pack(pady=20)
        else:
            for item in incorrect_answers:
                # Create a card/frame for each item
                card = ctk.CTkFrame(self.review_frame)
                card.pack(fill="x", pady=5, padx=5)
                
                q_lbl = ctk.CTkLabel(card, text=f"Q: {item['question']}", wraplength=600, justify="left", font=("Roboto", 14, "bold"))
                q_lbl.pack(anchor="w", padx=10, pady=(10, 5))
                
                user_lbl = ctk.CTkLabel(card, text=f"Your Answer: {item['user_answer']}", text_color="#FF4B4B", wraplength=600, justify="left", font=("Roboto", 14))
                user_lbl.pack(anchor="w", padx=10, pady=2)
                
                corr_lbl = ctk.CTkLabel(card, text=f"Correct Answer: {item['correct_answer']}", text_color="#2CC985", wraplength=600, justify="left", font=("Roboto", 14))
                corr_lbl.pack(anchor="w", padx=10, pady=2)
                
                exp_lbl = ctk.CTkLabel(card, text=f"Explanation: {item['explanation']}", wraplength=600, justify="left", font=("Roboto", 12))
                exp_lbl.pack(anchor="w", padx=10, pady=(5, 10))

if __name__ == "__main__":
    app = App()
    app.mainloop()
