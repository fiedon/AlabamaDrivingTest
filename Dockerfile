FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

COPY requirements.txt .
# Use uv pip install
RUN uv pip install --system --no-cache -r requirements.txt

COPY . .

EXPOSE 10000

# Standard Gunicorn config
# Use shell form to allow variable expansion for PORT (default 10000)
CMD exec gunicorn -w 4 -b 0.0.0.0:${PORT:-10000} main:app
