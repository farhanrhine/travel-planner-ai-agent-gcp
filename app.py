import re
import streamlit as st
from streamlit_folium import st_folium
from src.agent.travel_agent import (
    stream_travel_plan, 
    extract_locations, 
    parse_voice_input, 
    generate_audio_summary
)
from src.utils.map_utils import geocode_locations, create_route_map
from src.utils.audio_utils import transcribe_audio, text_to_speech
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="AI Travel Agent Planner", page_icon="✈️", layout="wide")
st.title("✈️ AI Travel Agent Planner")
st.caption("Your smart AI agent that plans the perfect day trip — just tell it where and what you love!")

# --- Session State ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Display Previous Chat History ---
for entry in st.session_state.chat_history:
    with st.chat_message("user"):
        st.markdown(entry["query"])
    with st.chat_message("assistant"):
        if entry.get("thinking"):
            with st.expander("💭 View AI Reasoning", expanded=False):
                st.markdown(entry["thinking"])
        st.markdown(entry["content"])
        if entry.get("audio"):
            st.audio(entry["audio"], format="audio/wav")
        if entry.get("map_data"):
            with st.expander("🗺️ View Route Map", expanded=True):
                route_map = create_route_map(entry["map_data"])
                if route_map:
                    st_folium(route_map, use_container_width=True, height=500, returned_objects=[])

# --- Input Tabs: Type or Speak ---
tab_type, tab_voice = st.tabs(["✍️ Type", "🎤 Speak"])

city = None
interests = None
interests_list = None
submitted = False

with tab_type:
    with st.form("planner_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            city_input = st.text_input("🏙️ City", placeholder="e.g. Dubai, Paris, Tokyo")
        with col2:
            interests_input = st.text_input("🎯 Interests", placeholder="e.g. food, history, adventure")
        submitted = st.form_submit_button("🗺️ Plan My Trip", use_container_width=True)

    if submitted:
        if not city_input or not interests_input:
            st.warning("Please fill in both City and Interests.")
            submitted = False
        else:
            city = city_input
            interests = interests_input
            interests_list = [i.strip() for i in interests.split(",")]

with tab_voice:
    st.markdown("**Speak your travel request naturally.** Example: *'Plan a trip to Dubai, I love street food and beaches'*")
    audio_value = st.audio_input("🎤 Record your request", key="voice_input")

    if audio_value:
        with st.spinner("🎧 Transcribing your voice..."):
            audio_bytes = audio_value.read()
            transcript = transcribe_audio(audio_bytes)

        if transcript:
            st.success(f"📝 **Heard:** {transcript}")

            with st.spinner("🧠 Parsing city & interests..."):
                parsed = parse_voice_input(transcript)
                city = parsed.get("city", "")
                interests_list = parsed.get("interests", [])
                interests = ", ".join(interests_list)

            if city and interests_list:
                st.info(f"🏙️ **City:** {city} • 🎯 **Interests:** {interests}")
                submitted = True
            else:
                st.warning("Couldn't extract city or interests from your speech. Please try again.")
        else:
            st.error("Could not transcribe audio. Please try again.")

# --- Handle Submission (shared by both tabs) ---
if submitted and city and interests_list:
    user_query = f"Plan a day trip in **{city}** • Interests: **{interests}**"

    # Show user message
    with st.chat_message("user"):
        st.markdown(user_query)

    # Stream assistant response
    with st.chat_message("assistant"):
        full_response = ""
        thinking_buffer = ""
        content_buffer = ""
        in_thinking = False
        thinking_done = False

        # Placeholders for dynamic updates
        status_placeholder = st.empty()
        thinking_expander_placeholder = st.empty()
        content_placeholder = st.empty()
        audio_placeholder = st.empty()
        map_placeholder = st.empty()

        status_placeholder.status("🧠 AI is reasoning...", state="running")

        for chunk in stream_travel_plan(city, interests_list):
            full_response += chunk

            # --- Detect <think> start ---
            if "<think>" in full_response and not in_thinking and not thinking_done:
                in_thinking = True

            # --- Detect </think> end ---
            if "</think>" in full_response and in_thinking:
                in_thinking = False
                thinking_done = True

                # Extract reasoning content
                match = re.search(r"<think>(.*?)</think>", full_response, re.DOTALL)
                if match:
                    thinking_buffer = match.group(1).strip()

                # Replace spinner with expander
                status_placeholder.empty()
                with thinking_expander_placeholder.expander("💭 View AI Reasoning", expanded=False):
                    st.markdown(thinking_buffer)

                # Start showing content after </think>
                after_think = full_response.split("</think>", 1)[-1].strip()
                if after_think:
                    content_buffer = after_think
                    content_placeholder.markdown(content_buffer + "▌")
                continue

            # --- Stream visible content (after thinking is done) ---
            if thinking_done and not in_thinking:
                content_buffer = full_response.split("</think>", 1)[-1].strip()
                content_placeholder.markdown(content_buffer + "▌")

            # --- No thinking tags at all ---
            if not in_thinking and not thinking_done and "<think>" not in full_response:
                content_buffer = full_response
                content_placeholder.markdown(content_buffer + "▌")

        # --- Final cleanup ---
        status_placeholder.empty()

        if thinking_done:
            content_buffer = full_response.split("</think>", 1)[-1].strip()
        else:
            content_buffer = full_response.strip()
            content_buffer = re.sub(r"<think>.*?</think>", "", content_buffer, flags=re.DOTALL).strip()

        # Remove the cursor
        content_placeholder.markdown(content_buffer)

        # --- Generate Audio (TTS) ---
        audio_data = None
        with audio_placeholder.container():
            with st.spinner("🔊 Generating spoken summary..."):
                try:
                    # 1. Have the LLM write a short narrated script
                    spoken_script = generate_audio_summary(content_buffer)
                    
                    # 2. Convert that script to speech
                    audio_data = text_to_speech(spoken_script)
                    
                    if audio_data:
                        st.markdown("### 🔊 Listen to Your Plan")
                        st.audio(audio_data, format="audio/wav")
                except Exception as e:
                    st.info(f"Could not generate audio: {e}")

        # --- Generate Route Map ---
        map_data = None
        with map_placeholder.container():
            with st.spinner("📍 Plotting locations on map..."):
                try:
                    locations = extract_locations(content_buffer, city)
                    if locations:
                        geocoded = geocode_locations(locations, city)
                        if geocoded:
                            map_data = geocoded
                            route_map = create_route_map(geocoded)
                            if route_map:
                                st.markdown("### 🗺️ Your Route Map")
                                st_folium(route_map, use_container_width=True, height=500, returned_objects=[])
                except Exception as e:
                    st.info(f"Could not generate map: {e}")

        # Save to history
        st.session_state.chat_history.append({
            "query": user_query,
            "thinking": thinking_buffer if thinking_buffer else None,
            "content": content_buffer,
            "audio": audio_data,
            "map_data": map_data,
        })
