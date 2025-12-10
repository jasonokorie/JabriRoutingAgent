# tools/distance_matrix.py
import os
import requests
from typing import List, Dict, Any

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


def distance_matrix_tool(locations: List[str]) -> Dict[str, Any]:
    """
    Calls the Google Maps Distance Matrix API to get a full NxN
    distance + duration matrix for the given locations.

    Args:
        locations: list of address strings.

    Returns:
        {
          "locations": [...],
          "distance_miles": [[...], ...],
          "duration_minutes": [[...], ...]
        }
    """
    if not GOOGLE_MAPS_API_KEY:
        raise RuntimeError("GOOGLE_MAPS_API_KEY is not set in your environment")

    if len(locations) == 0:
        return {"locations": [], "distance_miles": [], "duration_minutes": []}

    url = "https://maps.googleapis.com/maps/api/distancematrix/json"

    # We ask for an NxN matrix: every location is origin and destination.
    params = {
        "origins": "|".join(locations),
        "destinations": "|".join(locations),
        "key": GOOGLE_MAPS_API_KEY,
        "units": "imperial",  # miles
    }

    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()

    status = data.get("status")
    if status != "OK":
        raise RuntimeError(f"Distance Matrix API error: {status} - {data}")

    rows = data.get("rows", [])
    n = len(locations)
    distance_miles = [[0.0 for _ in range(n)] for _ in range(n)]
    duration_minutes = [[0.0 for _ in range(n)] for _ in range(n)]

    for i, row in enumerate(rows):
        elements = row.get("elements", [])
        for j, el in enumerate(elements):
            el_status = el.get("status")
            if el_status == "OK":
                dist_m = el["distance"]["value"]  # meters
                dur_s = el["duration"]["value"]  # seconds
                distance_miles[i][j] = dist_m / 1609.344
                duration_minutes[i][j] = dur_s / 60.0
            else:
                # If the API can't compute, leave zeros or handle specially.
                distance_miles[i][j] = 0.0
                duration_minutes[i][j] = 0.0

    return {
        "locations": locations,
        "distance_miles": distance_miles,
        "duration_minutes": duration_minutes,
    }
