# from langchain_groq import ChatGroq
# # from src.config.config import GROQ_API_KEY

# from dotenv import load_dotenv

# load_dotenv()


# llm = ChatGroq(
#     model="qwen/qwen3-32b",
#     temperature=0,
#     max_tokens=None,
#     reasoning_format="parsed",
#     timeout=None,
#     max_retries=2,
#     # other params...
# )

# messages = [
#     (
#         "system",
#         "You are a helpful assistant that translates English to French. Translate the user sentence.",
#     ),
#     ("human", "I love programming."),
# ]
# ai_msg = llm.invoke(messages)
# print(ai_msg.content)