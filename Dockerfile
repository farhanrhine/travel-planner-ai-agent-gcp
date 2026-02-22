## Parent image (must be 3.12+ to match pyproject.toml)
FROM python:3.12-slim

## Essential environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

## Work directory inside the docker container
WORKDIR /app

## Installing system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

## Install uv for fast dependency management
RUN pip install --no-cache-dir uv

## Copy dependency files first (better Docker layer caching)
COPY pyproject.toml uv.lock ./

## Install dependencies using uv
RUN uv sync --no-dev --frozen

## Copy the rest of the application
COPY . .

## Expose Streamlit port
EXPOSE 8501

## Run the app using uv
CMD ["uv", "run", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]