"""Map utilities for generating route maps from location names."""

import folium
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from src.utils.logger import get_logger

logger = get_logger(__name__)

# --- Geocoder (free, no API key needed) ---
geolocator = Nominatim(user_agent="ai-travel-agent-planner")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)


def geocode_locations(locations: list[str], city: str) -> list[dict]:
    """Convert location names to lat/lng coordinates.

    Args:
        locations: List of place/location names.
        city: The city context (appended for better geocoding accuracy).

    Returns:
        List of dicts with name, lat, lng for each successfully geocoded location.
    """
    results = []
    for place in locations:
        try:
            query = f"{place}, {city}"
            location = geocode(query)
            if location:
                results.append({
                    "name": place,
                    "lat": location.latitude,
                    "lng": location.longitude,
                })
                logger.info(f"Geocoded: {place} → ({location.latitude}, {location.longitude})")
            else:
                logger.warning(f"Could not geocode: {place}")
        except Exception as e:
            logger.error(f"Geocoding error for {place}: {e}")
    return results


def create_route_map(geocoded_locations: list[dict]) -> folium.Map:
    """Create a Folium map with markers and a route line.

    Args:
        geocoded_locations: List of dicts with name, lat, lng.

    Returns:
        A folium.Map object with markers and polyline route.
    """
    if not geocoded_locations:
        return None

    # Center map on the first location
    center_lat = sum(loc["lat"] for loc in geocoded_locations) / len(geocoded_locations)
    center_lng = sum(loc["lng"] for loc in geocoded_locations) / len(geocoded_locations)

    route_map = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=13,
        tiles="CartoDB positron",
    )

    # Add numbered markers for each stop
    colors = ["red", "blue", "green", "purple", "orange", "darkred", "cadetblue", "darkgreen"]
    for i, loc in enumerate(geocoded_locations):
        color = colors[i % len(colors)]
        folium.Marker(
            location=[loc["lat"], loc["lng"]],
            popup=f"<b>Stop {i + 1}:</b> {loc['name']}",
            tooltip=f"Stop {i + 1}: {loc['name']}",
            icon=folium.Icon(color=color, icon="info-sign"),
        ).add_to(route_map)

    # Draw route line connecting all stops
    if len(geocoded_locations) > 1:
        route_coords = [[loc["lat"], loc["lng"]] for loc in geocoded_locations]
        folium.PolyLine(
            route_coords,
            weight=4,
            color="#3388ff",
            opacity=0.8,
            dash_array="10",
        ).add_to(route_map)

    # Fit map to show all markers
    bounds = [[loc["lat"], loc["lng"]] for loc in geocoded_locations]
    route_map.fit_bounds(bounds, padding=(30, 30))

    return route_map
