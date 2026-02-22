"""Map utilities for generating premium route maps from location names."""

import re as _re
import folium
from folium import DivIcon
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from src.utils.logger import get_logger

logger = get_logger(__name__)

# --- Geocoder (free, no API key needed) ---
geolocator = Nominatim(user_agent="ai-travel-agent-planner")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

# --- Route segment colors (gradient from green → blue → purple → red) ---
ROUTE_COLORS = [
    "#22c55e",  # green (start)
    "#06b6d4",  # cyan
    "#3b82f6",  # blue
    "#8b5cf6",  # violet
    "#d946ef",  # fuchsia
    "#f43f5e",  # rose
    "#ef4444",  # red
    "#f97316",  # orange
    "#eab308",  # yellow
    "#14b8a6",  # teal
]


def geocode_locations(locations: list[str], city: str) -> list[dict]:
    """Convert location names to lat/lng coordinates.
    
    Args:
        locations: List of place/location names.
        city: The city context.
    """
    results = []
    
    # Clean the city name (remove "take me", "trip to", etc. if they leaked in)
    clean_city = _re.sub(r"(?i)take me to|plan a trip to|trip to|go to|in ", "", city).strip()
    
    for place in locations:
        try:
            # ONLY search within the specific city to avoid global jumps
            query = f"{place}, {clean_city}"
            location = geocode(query)
            
            if location:
                results.append({
                    "name": place,
                    "lat": location.latitude,
                    "lng": location.longitude,
                })
                logger.info(f"Geocoded: {place} ({clean_city}) -> ({location.latitude}, {location.longitude})")
            else:
                logger.warning(f"Could not find '{place}' in '{clean_city}'")
        except Exception as e:
            logger.error(f"Geocoding error for {place}: {e}")
    return results


def _numbered_icon(number: int, name: str, color: str) -> DivIcon:
    """Create a circular numbered marker icon with a place name label below it."""
    # Escape single quotes in name for HTML safety
    safe_name = name.replace("'", "&#39;")
    return DivIcon(
        icon_size=(150, 60),
        icon_anchor=(75, 16),
        html=f'''
        <div style="display: flex; flex-direction: column; align-items: center; width: 150px;">
            <div style="
                background: {color};
                color: white;
                width: 32px;
                height: 32px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 700;
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
                border: 3px solid white;
                box-shadow: 0 2px 8px rgba(0,0,0,0.4);
                flex-shrink: 0;
            ">{number}</div>
            <div style="
                background: rgba(30, 41, 59, 0.85);
                color: white;
                padding: 2px 8px;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 600;
                margin-top: 4px;
                white-space: nowrap;
                border: 1px solid rgba(255,255,255,0.2);
                box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                pointer-events: none;
            ">{safe_name}</div>
        </div>
        ''',
    )


def _start_icon() -> DivIcon:
    """Create a special START marker."""
    return DivIcon(
        icon_size=(40, 40),
        icon_anchor=(20, 40),
        html='''
        <div style="
            background: #22c55e;
            color: white;
            padding: 4px 10px;
            border-radius: 8px;
            font-weight: 700;
            font-size: 12px;
            font-family: 'Segoe UI', Arial, sans-serif;
            border: 2px solid white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.4);
            white-space: nowrap;
        ">🚩 START</div>
        ''',
    )


def _end_icon() -> DivIcon:
    """Create a special END marker."""
    return DivIcon(
        icon_size=(40, 40),
        icon_anchor=(20, 40),
        html='''
        <div style="
            background: #ef4444;
            color: white;
            padding: 4px 10px;
            border-radius: 8px;
            font-weight: 700;
            font-size: 12px;
            font-family: 'Segoe UI', Arial, sans-serif;
            border: 2px solid white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.4);
            white-space: nowrap;
        ">🏁 END</div>
        ''',
    )


def _popup_html(stop_num: int, name: str, total: int) -> str:
    """Generate a styled HTML popup for a marker."""
    if stop_num == 1:
        badge = '<span style="background:#22c55e;color:white;padding:2px 8px;border-radius:12px;font-size:11px;">START</span>'
    elif stop_num == total:
        badge = '<span style="background:#ef4444;color:white;padding:2px 8px;border-radius:12px;font-size:11px;">END</span>'
    else:
        badge = f'<span style="background:#3b82f6;color:white;padding:2px 8px;border-radius:12px;font-size:11px;">Stop {stop_num}</span>'

    return f'''
    <div style="font-family:'Segoe UI',Arial,sans-serif;min-width:160px;">
        <div style="margin-bottom:6px;">{badge}</div>
        <div style="font-size:15px;font-weight:600;color:#1e293b;">{name}</div>
        <div style="font-size:11px;color:#94a3b8;margin-top:4px;">Stop {stop_num} of {total}</div>
    </div>
    '''


def create_route_map(geocoded_locations: list[dict]) -> folium.Map:
    """Create a premium Folium map with numbered markers and colored route segments.

    Args:
        geocoded_locations: List of dicts with name, lat, lng.

    Returns:
        A folium.Map object with numbered markers and colorful route segments.
    """
    if not geocoded_locations:
        return None

    total = len(geocoded_locations)

    # Center map on average of all locations
    center_lat = sum(loc["lat"] for loc in geocoded_locations) / total
    center_lng = sum(loc["lng"] for loc in geocoded_locations) / total

    route_map = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=13,
        tiles="CartoDB dark_matter",
    )

    # --- Add numbered markers ---
    for i, loc in enumerate(geocoded_locations):
        stop_num = i + 1
        color = ROUTE_COLORS[i % len(ROUTE_COLORS)]

        # Numbered circle marker
        folium.Marker(
            location=[loc["lat"], loc["lng"]],
            popup=folium.Popup(_popup_html(stop_num, loc["name"], total), max_width=250),
            tooltip=f"Stop {stop_num}: {loc['name']}",
            icon=_numbered_icon(stop_num, loc["name"], color),
        ).add_to(route_map)

    # --- Add START label above first marker ---
    first = geocoded_locations[0]
    folium.Marker(
        location=[first["lat"] + 0.002, first["lng"]],
        icon=_start_icon(),
    ).add_to(route_map)

    # --- Add END label above last marker ---
    if total > 1:
        last = geocoded_locations[-1]
        folium.Marker(
            location=[last["lat"] + 0.002, last["lng"]],
            icon=_end_icon(),
        ).add_to(route_map)

    # --- Draw colored route segments between consecutive stops ---
    if total > 1:
        for i in range(total - 1):
            loc_a = geocoded_locations[i]
            loc_b = geocoded_locations[i + 1]
            color = ROUTE_COLORS[i % len(ROUTE_COLORS)]

            # Route line segment
            folium.PolyLine(
                locations=[
                    [loc_a["lat"], loc_a["lng"]],
                    [loc_b["lat"], loc_b["lng"]],
                ],
                weight=5,
                color=color,
                opacity=0.85,
                dash_array="12 6",
                tooltip=f"Route: Stop {i + 1} → Stop {i + 2}",
            ).add_to(route_map)

            # Direction arrow at midpoint
            mid_lat = (loc_a["lat"] + loc_b["lat"]) / 2
            mid_lng = (loc_a["lng"] + loc_b["lng"]) / 2
            folium.Marker(
                location=[mid_lat, mid_lng],
                icon=DivIcon(
                    icon_size=(24, 24),
                    icon_anchor=(12, 12),
                    html=f'''
                    <div style="
                        background: {color};
                        color: white;
                        width: 24px;
                        height: 24px;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 12px;
                        border: 2px solid white;
                        box-shadow: 0 1px 4px rgba(0,0,0,0.3);
                    ">→</div>
                    ''',
                ),
                tooltip=f"Stop {i + 1} → Stop {i + 2}",
            ).add_to(route_map)

    # --- Fit map bounds to show all markers ---
    bounds = [[loc["lat"], loc["lng"]] for loc in geocoded_locations]
    route_map.fit_bounds(bounds, padding=(50, 50))

    return route_map
