"""Audio utilities for speech-to-text and text-to-speech using Groq."""

from groq import Groq
from src.utils.logger import get_logger

logger = get_logger(__name__)

# --- Groq client (uses GROQ_API_KEY from environment) ---
client = Groq()


def transcribe_audio(audio_bytes: bytes) -> str:
    """Convert speech to text using Whisper Large V3 Turbo on Groq.

    Args:
        audio_bytes: Raw audio bytes (WAV format from Streamlit mic).

    Returns:
        Transcribed text string.
    """
    logger.info("Transcribing audio with Whisper Large V3 Turbo...")

    transcription = client.audio.transcriptions.create(
        file=("recording.wav", audio_bytes),
        model="whisper-large-v3-turbo",
        language="en",
    )

    text = transcription.text.strip()
    logger.info(f"Transcription result: {text}")
    return text


def text_to_speech(text: str) -> bytes:
    """Convert text to speech using Orpheus V1 English on Groq.

    Args:
        text: Text to convert to speech (max ~4000 chars).

    Returns:
        Audio bytes in WAV format.
    """
    logger.info(f"Converting {len(text)} chars to speech with Orpheus...")

    # TTS model has tight token limits (1200 TPM) — truncate significantly
    if len(text) > 1000:
        text = text[:1000] + "..."

    response = client.audio.speech.create(
        model="canopylabs/orpheus-v1-english",
        input=text,
        voice="diana",
        response_format="wav",
    )

    audio_bytes = response.read()
    logger.info(f"TTS generated {len(audio_bytes)} bytes of audio")
    return audio_bytes
