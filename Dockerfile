# ==============================================================================
# DOCKERFILE - AI Travel Agent Planner
# ==============================================================================
# This Dockerfile builds a container for the Streamlit application.
#
# BUILD COMMAND:
#   docker build -t travel-planner-ai-agent .
#
# RUN COMMAND:
#   docker run -p 8501:8501 --env-file .env travel-planner-ai-agent
#
# FOR KUBERNETES:
#   docker build -t your-dockerhub-username/travel-planner-ai-agent:latest .
#   docker push your-dockerhub-username/travel-planner-ai-agent:latest
# ==============================================================================

# Use Python 3.12 slim image (matches pyproject.toml requires-python >= 3.12)
FROM python:3.12-slim

# Set working directory inside container
# - Creates isolated /app folder inside the container (not on your local machine)
# - All subsequent commands (COPY, RUN, CMD) execute within this directory
# - Keeps application files organized and prevents conflicts with system files
WORKDIR /app

# Set environment variables
# - Prevents Python from writing .pyc files
# - Ensures output is sent straight to terminal (for logging)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
# - build-essential needed for some Python packages
# - curl needed for health checks
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv (fast Python package installer)
RUN pip install --no-cache-dir uv

# Copy dependency files first (for Docker layer caching)
# - This way, dependencies are only reinstalled when pyproject.toml changes
# - If only source code changes, Docker reuses the cached dependency layer
COPY pyproject.toml .
COPY uv.lock* ./

# Install Python dependencies using uv
RUN uv sync --no-dev --frozen

# Copy the rest of the application code
COPY . .

# Expose port 8501 (Streamlit default)
EXPOSE 8501

# Health check - Kubernetes/Docker can use this to check if app is alive
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run the Streamlit application
# - server.port=8501: Streamlit default port
# - server.address=0.0.0.0: Listen on all interfaces (required for Docker)
# - server.headless=true: Run without opening browser
CMD ["uv", "run", "streamlit", "run", "app.py", \
    "--server.port=8501", \
    "--server.address=0.0.0.0", \
    "--server.headless=true"]