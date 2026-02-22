from langchain_core.messages import HumanMessage, AIMessage
from src.agent.travel_agent import generate_travel_plan
from src.utils.logger import get_logger
from src.utils.custom_exception import CustomException

logger = get_logger(__name__)


class TravelPlanner:
    """Core travel planner that manages conversation state and generates travel plans."""

    def __init__(self):
        self.messages = []
        self.city = ""
        self.interests = []
        self.travel_plan = ""

        logger.info("Initialized TravelPlanner instance")

    def set_city(self, city: str):
        try:
            self.city = city
            self.messages.append(HumanMessage(content=city))
            logger.info(f"City set successfully: {city}")
        except Exception as e:
            logger.error(f"Error while setting city: {e}")
            raise CustomException("Failed to set city", e)

    def set_interests(self, interests_str: str):
        try:
            self.interests = [i.strip() for i in interests_str.split(",")]
            self.messages.append(HumanMessage(content=interests_str))
            logger.info(f"Interests set successfully: {self.interests}")
        except Exception as e:
            logger.error(f"Error while setting interests: {e}")
            raise CustomException("Failed to set interests", e)

    def create_travel_plan(self) -> str:
        try:
            logger.info(f"Generating travel plan for {self.city} with interests: {self.interests}")
            travel_plan = generate_travel_plan(self.city, self.interests)
            self.travel_plan = travel_plan
            self.messages.append(AIMessage(content=travel_plan))
            logger.info("Travel plan generated successfully")
            return travel_plan
        except Exception as e:
            logger.error(f"Error while creating travel plan: {e}")
            raise CustomException("Failed to create travel plan", e)
