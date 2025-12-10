# tools/backhaul_planner.py
from typing import Dict, Any, List
from tools.distance_matrix import distance_matrix_tool

# Backhaul pickup locations
BACKHAUL_SITES = [
    "ADM Columbus, NE",              # Liquid Corn
    "Sutherland, NE",                # Ethanol plant
    "Wood River, NE",
    "Aurora, NE",
    "Council Bluffs, IA",
    "Central City, NE",
    "Hastings, NE",
    "York, NE",
]

DETOUR_THRESHOLD_MILES = 10.0  # "nearby" threshold


def insert_backhauls_tool(routes_plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Insert backhaul stops when a route passes near a backhaul site.

    Input format:
    {
      "routes": [
        {
          "driver": "...",
          "stops": [
            "START: ...",
            "2103 Harvest Dr, Aurora, NE 68818",
            ...
          ],
          "total_distance_miles": ...,
          "total_duration_minutes": ...
        },
        ...
      ]
    }

    Output: same format, but with additional stops like
    "ADM Columbus, NE (Backhaul Pickup)" after nearby stops.
    """
    routes = routes_plan.get("routes", [])
    if not routes:
        return {"routes": []}

    updated_routes: List[Dict[str, Any]] = []

    for route in routes:
        stops = route.get("stops", [])
        if not stops:
            updated_routes.append(route)
            continue

        new_stops: List[str] = []
        total_distance = route.get("total_distance_miles", 0.0)
        total_duration = route.get("total_duration_minutes", 0.0)

        for stop in stops:
            new_stops.append(stop)

            # Skip START pseudo-node for distance checks
            if stop.startswith("START:"):
                continue

            # For each backhaul site, see if it's within DETOUR_THRESHOLD_MILES
            for site in BACKHAUL_SITES:
                # Compute distance from this stop to the site
                matrix = distance_matrix_tool([stop, site])
                dist_miles = matrix["distance_miles"][0][1]
                dur_minutes = matrix["duration_minutes"][0][1]

                if dist_miles > 0 and dist_miles <= DETOUR_THRESHOLD_MILES:
                    backhaul_label = f"{site} (Backhaul Pickup)"
                    if backhaul_label not in new_stops:
                        new_stops.append(backhaul_label)
                        total_distance += dist_miles
                        total_duration += dur_minutes
                    # We only add one site at a time per stop
                    break

        updated_routes.append(
            {
                "driver": route.get("driver"),
                "stops": new_stops,
                "total_distance_miles": total_distance,
                "total_duration_minutes": total_duration,
            }
        )

    return {"routes": updated_routes}
