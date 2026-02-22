"""Travel Agent using the new langchain create_agent API."""

from dotenv import load_dotenv
load_dotenv()

import json
import re as _re
from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langchain_core.messages import AIMessageChunk
from src.utils.logger import get_logger

logger = get_logger(__name__)

# --- System Prompt ---
TRAVEL_SYSTEM_PROMPT = (
    "You are an expert AI travel agent. "
    "When the user provides a city and their interests, create a detailed, "
    "well-structured day trip plan. "
    "Include timings, location names, and short descriptions for each stop. "
    "Format the output with bullet points and clear sections (Morning, Afternoon, Evening). "
    "Make the plan practical, enjoyable, and tailored to the user's interests."
)

# --- LLM ---
model = ChatGroq(
    model="qwen/qwen3-32b",
    temperature=0.3,
    max_tokens=2000,
    timeout=30,
    max_retries=2,
)

# --- Create Agent (new langchain.agents.create_agent API) ---
travel_agent = create_agent(
    model=model,
    tools=[],
    system_prompt=TRAVEL_SYSTEM_PROMPT,
    name="travel-planner-agent",
)

logger.info("Travel agent created successfully using create_agent")


def generate_travel_plan(city: str, interests: list[str]) -> str:
    """Generate a travel plan (non-streaming, for CLI usage)."""
    user_message = (
        f"Create a day trip plan for {city} "
        f"based on my interests: {', '.join(interests)}."
    )

    logger.info(f"Invoking travel agent for city={city}, interests={interests}")

    result = travel_agent.invoke({
        "messages": [{"role": "user", "content": user_message}]
    })

    ai_message = result["messages"][-1]
    logger.info("Travel agent executed successfully")
    return ai_message.content


def stream_travel_plan(city: str, interests: list[str]):
    """Stream travel plan tokens from the travel agent.

    Yields:
        str: Individual text chunks as they are generated.
    """
    user_message = (
        f"Create a day trip plan for {city} "
        f"based on my interests: {', '.join(interests)}."
    )

    logger.info(f"Streaming travel plan for city={city}, interests={interests}")

    for event in travel_agent.stream(
        {"messages": [{"role": "user", "content": user_message}]},
        stream_mode="messages",
    ):
        msg, metadata = event
        if isinstance(msg, AIMessageChunk) and msg.content:
            yield msg.content

    logger.info("Streaming completed")


def extract_locations(travel_plan_text: str, city: str) -> list[str]:
    """Extract location/place names from the travel plan using LLM.

    Args:
        travel_plan_text: The full travel plan text.
        city: The destination city.

    Returns:
        List of location name strings in visit order.
    """
    logger.info(f"Extracting locations from travel plan for {city}")

    result = model.invoke([
        {
            "role": "system",
            "content": (
                "You are a location extractor. Given a travel plan, extract ONLY the "
                "specific place/landmark/location names in the order they appear. "
                "Return ONLY a JSON array of strings. No explanation, no thinking, no markdown. "
                "Example: [\"Burj Khalifa\", \"Dubai Mall\", \"Dubai Marina\"]"
            ),
        },
        {
            "role": "user",
            "content": f"Extract location names from this {city} travel plan:\n\n{travel_plan_text}",
        },
    ])

    try:
        # Try to parse JSON from the response
        content = result.content.strip()
        # Remove <think>...</think> if present
        content = _re.sub(r"<think>.*?</think>", "", content, flags=_re.DOTALL).strip()
        # Find the JSON array in the response
        match = _re.search(r"\[.*\]", content, _re.DOTALL)
        if match:
            locations = json.loads(match.group())
            logger.info(f"Extracted {len(locations)} locations: {locations}")
            return locations
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Failed to parse locations: {e}")

    return []
