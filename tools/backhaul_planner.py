# tools/backhaul_planner.py
from __future__ import annotations

from typing import Dict, Any, List, Optional, Tuple
from tools.distance_matrix import distance_matrix_tool

# Backhaul pickup locations (canonical names)
BACKHAUL_SITES = [
    "ADM Columbus, NE",        # Liquid Corn
    "Sutherland, NE",          # Ethanol
    "Wood River, NE",
    "Aurora, NE",
    "Council Bluffs, IA",
    "Central City, NE",
    "Hastings, NE",
    "York, NE",
]

# Detour budget in minutes (soft constraint, not a hard mile radius)
DEFAULT_DETOUR_BUDGET_MIN = 20.0


def insert_backhauls_tool(
    routes_plan: Dict[str, Any],
    detour_budget_minutes: float = DEFAULT_DETOUR_BUDGET_MIN,
) -> Dict[str, Any]:
    """
    Insert backhaul pickups on reload legs (stop -> base).

    Backhaul rules:
    - Only consider legs where leg.type == "reload_to_base"
    - Prefer smallest detour minutes
    - Insert at most ONE backhaul per reload leg
    - Skip if detour would significantly worsen fairness
    """

    base = routes_plan.get("base_reload_location")
    routes = routes_plan.get("routes", [])
    if not base or not routes:
        return routes_plan

    # Compute average minutes first (for fairness guardrails)
    total_minutes = [r.get("total_duration_minutes", 0.0) for r in routes]
    avg_minutes = sum(total_minutes) / max(len(total_minutes), 1)

    updated_routes: List[Dict[str, Any]] = []

    for route in routes:
        driver_minutes = route.get("total_duration_minutes", 0.0)
        legs = route.get("legs", [])

        new_legs: List[Dict[str, Any]] = []
        added_minutes = 0.0
        added_miles = 0.0

        for leg in legs:
            # Always keep the original leg unless replaced
            if leg.get("type") != "reload_to_base":
                new_legs.append(leg)
                continue

            stop = leg["from"]
            base_leg_minutes = leg.get("duration_minutes", 0.0)
            base_leg_miles = leg.get("distance_miles", 0.0)

            # Fairness guardrail: if this driver is already heavy, be stricter
            effective_budget = detour_budget_minutes
            if driver_minutes > avg_minutes + 15:
                effective_budget = detour_budget_minutes / 2

            # Compute detours via backhaul sites
            best_site = None
            best_detour_minutes = None
            best_distances = None

            # Build matrix: stop -> sites, sites -> base
            out = distance_matrix_tool([stop] + BACKHAUL_SITES)
            back = distance_matrix_tool(BACKHAUL_SITES + [base])

            for i, site in enumerate(BACKHAUL_SITES):
                stop_to_site_min = out["duration_minutes"][0][i + 1]
                site_to_base_min = back["duration_minutes"][i][len(BACKHAUL_SITES)]

                if stop_to_site_min <= 0 or site_to_base_min <= 0:
                    continue

                detour_minutes = (stop_to_site_min + site_to_base_min) - base_leg_minutes

                if detour_minutes < 0:
                    detour_minutes = 0.0  # effectively on the way

                if detour_minutes <= effective_budget:
                    if best_detour_minutes is None or detour_minutes < best_detour_minutes:
                        best_detour_minutes = detour_minutes
                        best_site = site
                        best_distances = (
                            out["distance_miles"][0][i + 1],
                            back["distance_miles"][i][len(BACKHAUL_SITES)],
                        )

            # If no reasonable backhaul, keep original reload leg
            if best_site is None:
                new_legs.append(leg)
                continue

            # Insert backhaul legs instead of direct reload
            stop_to_site_miles, site_to_base_miles = best_distances

            new_legs.append(
                {
                    "type": "backhaul_pickup",
                    "from": stop,
                    "to": best_site,
                    "distance_miles": stop_to_site_miles,
                    "duration_minutes": None,
                }
            )
            new_legs.append(
                {
                    "type": "return_to_base",
                    "from": best_site,
                    "to": base,
                    "distance_miles": site_to_base_miles,
                    "duration_minutes": None,
                }
            )

            added_minutes += best_detour_minutes
            added_miles += stop_to_site_miles + site_to_base_miles - base_leg_miles

        # Update totals
        route["legs"] = new_legs
        route["total_duration_minutes"] = route.get("total_duration_minutes", 0.0) + added_minutes
        route["total_distance_miles"] = route.get("total_distance_miles", 0.0) + added_miles
        route["backhaul_minutes_added"] = round(added_minutes, 2)

        updated_routes.append(route)

    routes_plan["routes"] = updated_routes
    routes_plan["notes"] = routes_plan.get("notes", []) + [
        "Backhauls inserted only on reload legs using detour-minutes logic.",
        f"Default detour budget: {detour_budget_minutes} minutes.",
    ]

    return routes_plan
