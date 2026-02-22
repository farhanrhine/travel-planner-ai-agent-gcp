"""Travel Agent using the new langchain create_agent API."""

from dotenv import load_dotenv
load_dotenv()

import json
import re as _re
from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langchain_core.messages import AIMessageChunk
from src.config.config import LLM_MODEL
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
    model=LLM_MODEL,
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


def parse_voice_input(transcript: str) -> dict:
    """Extract city and interests from a voice transcript using LLM.

    Args:
        transcript: The raw transcribed text from speech-to-text.

    Returns:
        Dict with "city" (str) and "interests" (list[str]).
        Returns empty values if parsing fails.
    """
    logger.info(f"Parsing voice input: {transcript}")

    result = model.invoke([
        {
            "role": "system",
            "content": (
                "You are a travel data extractor. "
                "I will give you a voice transcript. Extract the specific CITY and a list of INTERESTS. "
                "If the user says a country or region (like Japan), try to identify the main city mentioned (like Tokyo) "
                "or use the most prominent city. "
                "Return ONLY a JSON object like: "
                '{"city": "Tokyo", "interests": ["anime", "food"]}. '
                "No processing talk, no markdown."
            ),
        },
        {"role": "user", "content": transcript},
    ])

    try:
        content = result.content.strip()
        content = _re.sub(r"<think>.*?</think>", "", content, flags=_re.DOTALL).strip()
        # Find JSON object in response
        match = _re.search(r"\{.*\}", content, _re.DOTALL)
        if match:
            parsed = json.loads(match.group())
            city = parsed.get("city", "")
            interests = parsed.get("interests", [])
            logger.info(f"Parsed voice input — city: {city}, interests: {interests}")
            return {"city": city, "interests": interests}
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Failed to parse voice input: {e}")

    return {"city": "", "interests": []}


def generate_audio_summary(travel_plan_text: str) -> str:
    """Create a short, spoken-style summary of the travel plan for TTS.

    Args:
        travel_plan_text: The full travel plan markdown.

    Returns:
        A short (max 700 chars) summary meant for narration.
    """
    logger.info("Generating spoken summary for TTS...")

    result = model.invoke([
        {
            "role": "system",
            "content": (
                "You are the voice of a friendly travel agent. "
                "Convert the provided travel plan into a short spoken script of 100-120 words. "
                "RULES: "
                "1. Speak directly to the user (e.g., 'Welcome to Dubai! We'll start at...') "
                "2. NO markdown, NO bullet points, NO special characters like #, *, or -. "
                "3. NO introductory text like 'Here is your summary' or 'I have summarized'. "
                "4. ONLY output the transcript to be read out loud. "
                "5. Stop immediately if you approach 120 words."
            ),
        },
        {"role": "user", "content": f"Plan to transcribe:\n\n{travel_plan_text}"},
    ])

    summary = result.content.strip()
    
    # 1. Clean out any leftover markdown or meta-tags
    summary = _re.sub(r"<think>.*?</think>", "", summary, flags=_re.DOTALL).strip()
    summary = _re.sub(r"[#*_\\-]", "", summary)
    
    # 2. Strict character limit for TTS model safety (approx 1200 tokens)
    if len(summary) > 850:
        summary = summary[:850].rsplit(' ', 1)[0] + "." # Clean cut at last word
    
    logger.info(f"Final spoken transcript ({len(summary)} chars): {summary[:100]}...")
    return summary
