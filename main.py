"""CLI entry point for the Travel Planner AI Agent."""

from dotenv import load_dotenv
from src.core.planner import TravelPlanner

load_dotenv()


def main():
    print("=" * 50)
    print("  ✈️  AI Travel Itinerary Planner")
    print("=" * 50)

    city = input("\nEnter the city name for your trip: ").strip()
    interests = input("Enter your interests (comma-separated): ").strip()

    if not city or not interests:
        print("❌ Both city and interests are required.")
        return

    planner = TravelPlanner()
    planner.set_city(city)
    planner.set_interests(interests)

    print("\n⏳ Generating your itinerary...\n")
    itinerary = planner.create_itinerary()

    print("=" * 50)
    print("📄 Your Itinerary")
    print("=" * 50)
    print(itinerary)


if __name__ == "__main__":
    main()