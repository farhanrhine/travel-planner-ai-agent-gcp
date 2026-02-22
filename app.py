import re
import streamlit as st
from src.agent.travel_agent import stream_itinerary
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="AI Travel Planner", page_icon="✈️", layout="centered")
st.title("✈️ AI Travel Itinerary Planner")
st.caption("Plan your day trip itinerary by entering your city and interests")

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

# --- Input Form ---
with st.form("planner_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        city = st.text_input("🏙️ City", placeholder="e.g. Dubai, Paris, Tokyo")
    with col2:
        interests = st.text_input("🎯 Interests", placeholder="e.g. food, history, adventure")
    submitted = st.form_submit_button("🗺️ Generate Itinerary", use_container_width=True)

# --- Handle Submission ---
if submitted:
    if not city or not interests:
        st.warning("Please fill in both City and Interests.")
    else:
        interests_list = [i.strip() for i in interests.split(",")]
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

            status_placeholder.status("🧠 AI is reasoning...", state="running")

            for chunk in stream_itinerary(city, interests_list):
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

                # --- No thinking tags at all (model doesn't use them) ---
                if not in_thinking and not thinking_done and "<think>" not in full_response:
                    content_buffer = full_response
                    content_placeholder.markdown(content_buffer + "▌")

            # --- Final cleanup ---
            status_placeholder.empty()

            if thinking_done:
                content_buffer = full_response.split("</think>", 1)[-1].strip()
            else:
                content_buffer = full_response.strip()
                # Clean any stray think tags
                content_buffer = re.sub(r"<think>.*?</think>", "", content_buffer, flags=re.DOTALL).strip()

            # Remove the cursor
            content_placeholder.markdown(content_buffer)

            # Save to history
            st.session_state.chat_history.append({
                "query": user_query,
                "thinking": thinking_buffer if thinking_buffer else None,
                "content": content_buffer,
            })
