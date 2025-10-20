FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies
RUN uv pip install --system --no-cache -r pyproject.toml

# Copy application code
COPY . .

# Run the application
CMD ["python", "main.py"]
