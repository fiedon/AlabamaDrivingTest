# Agent Instructions

## Core Principles
1. **Dependency Management**: Always use `uv` instead of standard `pip` or `python`.
2. **Execution**: Always run the application logic via `uv` or `docker`. Avoid direct `python script.py` execution.

## Detailed Guidelines

### Using `uv`
- **Virtual Environment**: Ensure a venv exists or create one using `uv venv`.
- **Install Dependencies**: 
  ```bash
  uv pip install -r requirements.txt
  ```
- **Run Scripts**:
  ```bash
  uv run <script_name>.py
  ```
  Example: `uv run main.py` or `uv run flask run`.

### Using Docker
- **Build**:
  ```bash
  docker build -t alabama-dl .
  ```
- **Run**:
  ```bash
  docker run -p 5000:5000 --env-file .env alabama-dl
  ```
- Use Docker for running the full web application to ensure environment consistency.

## Prohibited
- Do NOT run `python <file>` directly.
- Do NOT run `pip install` directly (use `uv pip install`).
