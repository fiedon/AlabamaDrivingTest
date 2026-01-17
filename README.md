# Alabama Driver License Prep

A modern Python application designed to help users prepare for the Alabama Driver License written exam. This application simulates the official test environment, provides instant feedback, and tracks your progress.

## Features

-   **Realistic Exam Simulation**: 30 questions per exam with an 80% passing threshold (24 correct answers), matching official requirements.
-   **Review System**: Detailed review of incorrect answers at the end of each exam, showing user selection, correct answer, and explanation.
-   **Visual Questions**: Support for questions involving traffic signs and diagrams.
-   **Modern UI**: Built with `customtkinter` for a sleek, responsive, and user-friendly interface.
-   **Dynamic Question Pool**: Randomly generates exams from a larger pool of questions to ensure varied practice.

## Prerequisites

-   **Python 3.10+** (if running locally)
-   **uv** (for dependency management)
-   **Docker** (optional, for containerized execution)

## Installation & Usage

Following the project's [Agent Instructions](./AGENT_INSTRUCTIONS.md), please use `uv` or `docker` for all operations.

### Option 1: Running Locally with `uv`

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/fiedon/AlabamaDrivingTest.git
    cd AlabamaDrivingTest
    ```

2.  **Set up the environment**:
    ```bash
    uv venv
    uv pip install -r requirements.txt
    ```

3.  **Run the application**:
    ```bash
    uv run app.py
    ```

### Option 2: Running with Docker

1.  **Build the image**:
    ```bash
    docker build -t alabama-dl .
    ```

2.  **Run the container**:
    ```bash
    docker run -p 5000:5000 --env-file .env alabama-dl
    ```
    *(Note: The main application is a GUI app. Docker is primarily used for the web-based components or backend services if applicable. For the desktop GUI, use the `uv` method directly on your host machine.)*

## Project Structure

-   `app.py`: Main entry point for the Desktop GUI application.
-   `exam_logic.py`: Core logic for exam generation and scoring.
-   `pdf_processor.py`: Utilities for processing source PDFs (e.g., driver manuals).
-   `generate_questions.py`: Script to generate question pools from source content.
-   `requirements.txt`: Project dependencies.

## Contributing

1.  Fork the repository.
2.  Create your feature branch (`git checkout -b feature/amazing-feature`).
3.  Commit your changes (`git commit -m 'Add some amazing feature'`).
4.  Push to the branch (`git push origin feature/amazing-feature`).
5.  Open a Pull Request.

## License

Distributed under the MIT License. See `LICENSE` for more information.
