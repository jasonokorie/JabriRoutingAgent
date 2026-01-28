# tools/distance_matrix.py
import os
import time
import requests
from typing import List, Dict, Any, Optional, Union

GOOGLE_DISTANCE_MATRIX_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"
METERS_PER_MILE = 1609.344


def _require_api_key() -> str:
    # Read at runtime (important for ADK Web UI loading .env)
    key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not key:
        raise RuntimeError(
            "GOOGLE_MAPS_API_KEY is not set. Add it to your .env and restart adk web."
        )
    return key


def _normalize_locations(items: List[str]) -> List[str]:
    cleaned = []
    for x in items:
        if not isinstance(x, str) or not x.strip():
            continue
        cleaned.append(" ".join(x.split()))  # collapse whitespace
    return cleaned


def distance_matrix_tool(
    locations: Optional[List[str]] = None,
    origins: Optional[List[str]] = None,
    destinations: Optional[List[str]] = None,
    mode: str = "driving",
    departure_time: Optional[Union[int, str]] = None,
    traffic_model: Optional[str] = None,
    timeout_s: int = 30,
) -> Dict[str, Any]:
    """
    Google Maps Distance Matrix wrapper.

    Usage patterns:
      1) NxN matrix:
         distance_matrix_tool(locations=[...])

      2) Origins x Destinations matrix:
         distance_matrix_tool(origins=[...], destinations=[...])

    Returns:
      {
        "origins": [...],
        "destinations": [...],
        "distance_miles": [[...], ...],     # float or None per cell
        "duration_minutes": [[...], ...],   # float or None per cell
        "raw_status": "OK",
        "timestamp": 1730000000
      }
    """
    api_key = _require_api_key()

    # Determine query shape
    if locations is not None:
        locs = _normalize_locations(locations)
        if not locs:
            return {
                "origins": [],
                "destinations": [],
                "distance_miles": [],
                "duration_minutes": [],
                "raw_status": "EMPTY_INPUT",
                "timestamp": int(time.time()),
            }
        origins_list = locs
        destinations_list = locs
    else:
        origins_list = _normalize_locations(origins or [])
        destinations_list = _normalize_locations(destinations or [])
        if not origins_list or not destinations_list:
            return {
                "origins": origins_list,
                "destinations": destinations_list,
                "distance_miles": [],
                "duration_minutes": [],
                "raw_status": "EMPTY_INPUT",
                "timestamp": int(time.time()),
            }

    params: Dict[str, Any] = {
        "origins": "|".join(origins_list),
        "destinations": "|".join(destinations_list),
        "key": api_key,
        "units": "imperial",
        "mode": mode,
    }

    # Traffic-aware durations require departure_time
    # departure_time can be "now" or unix epoch seconds
    if departure_time is not None:
        params["departure_time"] = departure_time
        if traffic_model:
            params["traffic_model"] = traffic_model

    resp = requests.get(GOOGLE_DISTANCE_MATRIX_URL, params=params, timeout=timeout_s)
    resp.raise_for_status()
    data = resp.json()

    status = data.get("status", "UNKNOWN")
    if status != "OK":
        raise RuntimeError(f"Distance Matrix API error: {status} - {data}")

    # API might return formatted addresses; keep yours too
    rows = data.get("rows", [])
    o = len(origins_list)
    d = len(destinations_list)

    distance_miles: List[List[Optional[float]]] = [[None for _ in range(d)] for _ in range(o)]
    duration_minutes: List[List[Optional[float]]] = [[None for _ in range(d)] for _ in range(o)]

    for i, row in enumerate(rows):
        elements = row.get("elements", [])
        for j, el in enumerate(elements):
            el_status = el.get("status", "UNKNOWN")
            if el_status == "OK":
                dist_m = el["distance"]["value"]  # meters
                dur_s = el["duration"]["value"]  # seconds

                distance_miles[i][j] = dist_m / METERS_PER_MILE
                duration_minutes[i][j] = dur_s / 60.0
            else:
                # Keep None so planners can detect missing routes and avoid hallucinations
                distance_miles[i][j] = None
                duration_minutes[i][j] = None

    return {
        "origins": origins_list,
        "destinations": destinations_list,
        "distance_miles": distance_miles,
        "duration_minutes": duration_minutes,
        "raw_status": status,
        "timestamp": int(time.time()),
    }
