# tools/route_builder.py
from typing import List, Dict, Any
from tools.distance_matrix import distance_matrix_tool

MAX_HOURS_PER_DRIVER = 10.0  # legal limit


def greedy_route_builder_tool(drivers: List[Dict[str, str]], stops: List[str]) -> Dict[str, Any]:
    """
    Build routes for drivers using a simple nearest-neighbor greedy algorithm.

    Args:
        drivers: list of dicts, each like {"name": "John", "start": "address"}
        stops: list of destination addresses (strings)

    Returns:
        {
          "routes": [
            {
              "driver": "John",
              "stops": [...],                    # ordered list including START
              "total_distance_miles": float,
              "total_duration_minutes": float
            },
            ...
          ]
        }
    """
    if not drivers or not stops:
        return {"routes": []}

    # Build a global location list: driver starts + stops
    all_locations: List[str] = []
    start_indices: Dict[str, int] = {}  # driver -> index in all_locations

    # Add driver starts first
    for d in drivers:
        start = d["start"]
        if start not in all_locations:
            all_locations.append(start)
        start_indices[d["name"]] = all_locations.index(start)

    # Add stops
    for s in stops:
        if s not in all_locations:
            all_locations.append(s)

    # Compute NxN distance + duration matrix once
    matrix = distance_matrix_tool(all_locations)
    distances = matrix["distance_miles"]
    durations = matrix["duration_minutes"]

    # Map addresses to indices for quick lookup
    addr_to_index = {addr: i for i, addr in enumerate(all_locations)}

    # Track which stops are unassigned globally
    unassigned_stops = set(stops)

    routes: List[Dict[str, Any]] = []

    for d in drivers:
        name = d["name"]
        start_addr = d["start"]
        start_idx = start_indices[name]

        current_idx = start_idx
        route_stops: List[str] = [f"START: {start_addr}"]
        total_distance = 0.0
        total_duration = 0.0

        # Greedy: keep adding the nearest unassigned stop that fits under 10 hours
        while unassigned_stops:
            best_stop = None
            best_dist = None
            best_dur = None

            for stop in list(unassigned_stops):
                stop_idx = addr_to_index[stop]
                dist = distances[current_idx][stop_idx]
                dur = durations[current_idx][stop_idx]
                if best_stop is None or dur < best_dur:
                    best_stop = stop
                    best_dist = dist
                    best_dur = dur

            if best_stop is None:
                break

            # Check if adding this stop would exceed MAX_HOURS_PER_DRIVER
            projected_duration = total_duration + best_dur
            projected_hours = projected_duration / 60.0
            if projected_hours > MAX_HOURS_PER_DRIVER:
                # Can't add more stops for this driver
                break

            # Assign this stop to the driver route
            route_stops.append(best_stop)
            total_distance += best_dist
            total_duration = projected_duration
            current_idx = addr_to_index[best_stop]
            unassigned_stops.remove(best_stop)

        routes.append(
            {
                "driver": name,
                "stops": route_stops,
                "total_distance_miles": total_distance,
                "total_duration_minutes": total_duration,
            }
        )

    return {"routes": routes}
