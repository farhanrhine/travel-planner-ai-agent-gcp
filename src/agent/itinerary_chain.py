from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
# from src.config.config import GROQ_API_KEY
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(
    model= "qwen/qwen3-32b",
    temperature=0.3
)

#  groq_api_key = GROQ_API_KEY,


itnineary_prompt = ChatPromptTemplate([
    ("system" , "You are a helpful travel asssistant. Create a day trip itineary for {city} based on user's interest : {interests}. Provide a brief , bulleted itineary"),
    ("human" , "Create a itineary for my day trip")
])

def generate_itineary(city:str , interests:list[str]) -> str:
    response = llm.invoke(
        itnineary_prompt.format_messages(city=city,interests=', '.join(interests))
    )

    return response.content