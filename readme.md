# ✈️ AI Travel Agent Planner

An AI-powered travel planning agent built with **LangChain's `create_agent`** and **Streamlit**. Enter a city and your interests — or just **speak** to the agent — and it generates a detailed day trip plan with an **interactive route map** and a **voice summary**.

## Workflow

![Travel Planner Workflow](workflow.svg)

## App Flow

![App Flow](app-flow.svg)

## Features

- **AI Agent** — Uses `create_agent` from LangChain (LangGraph-powered)
- **Voice Capabilities** — Speak your request naturally with **Speech-to-Text** (Whisper)
- **Audio Narrator** — Listen to a high-quality summary of your plan with **Text-to-Speech** (Orpheus)
- **Chat Streaming** — Responses stream token by token in real-time
- **Reasoning Toggle** — AI thinking is hidden behind a collapsible button
- **Route Map** — Interactive Folium map with numbered stops and colored route lines
- **Chat History** — Previous conversations persist in the session

## Tech Stack

- **LLM**: Groq (Qwen 3 32B) via `langchain-groq`
- **Speech-to-Text**: Whisper Large V3 Turbo (via Groq)
- **Text-to-Speech**: Orpheus V1 English (via Groq)
- **Agent**: `langchain.agents.create_agent` (LangChain v1.2.9)
- **Frontend**: Streamlit
- **Maps**: Folium + Geopy (Nominatim geocoding)
- **Logging**: Python `logging` → file-based logs
- **Package Manager**: uv
- **Deployment**: Docker + Kubernetes
- **Monitoring**: ELK Stack (Elasticsearch, Logstash, Kibana, Filebeat)

## Project Structure

```
travel-planner-ai-agent/
├── app.py                        # Streamlit web app (main entry point)
├── main.py                       # CLI entry point
├── pyproject.toml                # Dependencies (managed with uv)
├── Dockerfile                    # Docker container (Python 3.12 + uv)
├── .dockerignore                 # Excludes dev tools from Docker image
├── .env                          # API keys (not committed)
├── .gitignore                    # Git ignore rules
│
├── src/
│   ├── agent/
│   │   └── travel_agent.py      # create_agent, streaming, location/voice parsing
│   ├── core/
│   │   └── planner.py           # TravelPlanner class (manages state)
│   ├── config/
│   │   └── config.py            # Environment variable loading
│   └── utils/
│       ├── logger.py            # File-based logging setup
│       ├── custom_exception.py  # Custom exception with file/line info
│       ├── map_utils.py         # Geocoding + Folium route map generation
│       └── audio_utils.py       # Groq Whisper and Orpheus integration
│
├── k8s-deployment.yaml           # Kubernetes deployment + service
├── elasticsearch.yaml            # Elasticsearch for log storage
├── logstash.yaml                 # Logstash pipeline config
├── kibana.yaml                   # Kibana dashboard
├── filebeat.yaml                 # Filebeat log collector (DaemonSet)
│
├── .agent/
│   └── skills/
│       └── excalidraw-diagram-generator/  # Skill for generating diagrams
│
├── workflow.svg                  # Project workflow diagram (vector)
├── app-flow.svg                  # App flow diagram (vector)
├── workflow.excalidraw           # Editable workflow (Excalidraw)
├── app-flow.excalidraw           # Editable app flow (Excalidraw)
```

### ⚠️ Agent Skills

This project uses **[AI agent skills](https://github.com/github/awesome-copilot)** to extend capabilities (e.g., generating Excalidraw diagrams).

**How to install skills:**

```bash
# Browse available skills
npx skills

# Add a specific skill to the project
npx skills add https://github.com/github/awesome-copilot --skill excalidraw-diagram-generator
```

> **Note:** Skills are dev tools only — they are excluded from the Docker image via `.dockerignore` but pushed to GitHub for local development.

## Setup

### 1. Clone and install

```bash
git clone https://github.com/farhanrhine/travel-planner-ai-agent-gcp.git
cd travel-planner-ai-agent-gcp
uv sync
```

### 2. Add your API keys

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_api_key
```

### 3. Run the app

```bash
uv run streamlit run app.py
```

App opens at `http://localhost:8501`

### 4. Run via CLI (optional)

```bash
uv run python main.py
```

## How It Works

1. **Input**: User either types their request (✍️ **Type** tab) or speaks it (🎤 **Speak** tab).
2. **STT**: If spoken, **Whisper** transcribes the audio, and the LLM extracts the city and interests.
3. **Agent**: `create_agent` invokes the Groq LLM to generate the detailed travel plan.
4. **Streaming**: The response streams in real-time, with AI reasoning hidden behind a toggle expander.
5. **TTS**: After generation, the LLM creates a short narrated summary, which **Orpheus** converts to audio for playback.
6. **MAPPING**: The AI extracts location names from the plan, geocodes them via **Nominatim**, and plots them on an **interactive Folium map**.

## Docker

```bash
docker build -t travel-agent .
docker run -p 8501:8501 --env-file .env travel-agent
```

## Kubernetes

```bash
kubectl apply -f k8s-deployment.yaml
```

For the ELK logging stack:

```bash
kubectl create namespace logging
kubectl apply -f elasticsearch.yaml
kubectl apply -f logstash.yaml
kubectl apply -f kibana.yaml
kubectl apply -f filebeat.yaml
```
