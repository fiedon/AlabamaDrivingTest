FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

COPY requirements.txt .
# Use uv pip install
RUN uv pip install --system --no-cache -r requirements.txt

COPY . .

EXPOSE 5000

# Increase Gunicorn timeout to 300s to allow for long generation times (4 batches * 5-10s)
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:5000", "--timeout", "300", "main:app"]
