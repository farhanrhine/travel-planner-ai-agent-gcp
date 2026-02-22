"""CLI entry point for the AI Travel Agent Planner."""

from dotenv import load_dotenv
from src.core.planner import TravelPlanner

load_dotenv()


def main():
    print("=" * 50)
    print("  ✈️  AI Travel Agent Planner")
    print("=" * 50)

    city = input("\nEnter the city name for your trip: ").strip()
    interests = input("Enter your interests (comma-separated): ").strip()

    if not city or not interests:
        print("❌ Both city and interests are required.")
        return

    planner = TravelPlanner()
    planner.set_city(city)
    planner.set_interests(interests)

    print("\n⏳ Generating your travel plan...\n")
    travel_plan = planner.create_travel_plan()

    print("=" * 50)
    print("📄 Your Travel Plan")
    print("=" * 50)
    print(travel_plan)


if __name__ == "__main__":
    main()