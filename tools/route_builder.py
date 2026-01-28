from __future__ import annotations

from typing import List, Dict, Any, Optional, Tuple
from tools.distance_matrix import distance_matrix_tool

MAX_HOURS_PER_DRIVER = 10.0  # legal driving limit (hours)


def _safe_min(x: Optional[float], default: float = 10**12) -> float:
    return x if x is not None else default


def greedy_route_builder_tool(
    drivers: List[Dict[str, str]],
    stops: List[str],
    base_reload_location: str = "Grand Island, NE",
    max_hours_per_driver: float = MAX_HOURS_PER_DRIVER,
) -> Dict[str, Any]:
    """
    Fairness-first ROUND-ROBIN route builder.

    Real-world rules enforced:
    - Day-by-day planning
    - Reload required between every delivery (base -> stop -> base)
    - Equal work distribution is more important than shortest path
    - Drivers should end back at base unless downstream logic overrides

    Args:
        drivers: [{"name":"John","start":"...","home":"..."}]
        stops: delivery addresses
        base_reload_location: reload base (GI)
        max_hours_per_driver: legal limit

    Returns:
        {
          "base_reload_location": "...",
          "routes": [...],
          "unassigned_deliveries": [...],
          "notes": [...]
        }
    """

    if not drivers:
        return {
            "base_reload_location": base_reload_location,
            "routes": [],
            "unassigned_deliveries": stops or [],
        }

    # Clean inputs
    stops = [s for s in stops if isinstance(s, str) and s.strip()]
    if not stops:
        routes = []
        for d in drivers:
            routes.append(
                {
                    "driver": d["name"],
                    "start_location": d.get("start", ""),
                    "end_location": d.get("start", ""),
                    "deliveries": [],
                    "legs": [],
                    "total_distance_miles": 0.0,
                    "total_duration_minutes": 0.0,
                }
            )
        return {
            "base_reload_location": base_reload_location,
            "routes": routes,
            "unassigned_deliveries": [],
        }

    # --- DISTANCE LOOKUPS (BASE-CENTRIC) ---
    out = distance_matrix_tool(
        origins=[base_reload_location],
        destinations=stops,
    )
    back = distance_matrix_tool(
        origins=stops,
        destinations=[base_reload_location],
    )

    out_dists = out["distance_miles"][0]
    out_durs = out["duration_minutes"][0]
    back_dists = [row[0] for row in back["distance_miles"]]
    back_durs = [row[0] for row in back["duration_minutes"]]

    # --- PER-STOP ROUND TRIP COST ---
    stop_costs: Dict[str, Dict[str, Optional[float]]] = {}
    for i, stop in enumerate(stops):
        rt_miles = None
        rt_mins = None

        if out_dists[i] is not None and back_dists[i] is not None:
            rt_miles = float(out_dists[i] + back_dists[i])

        if out_durs[i] is not None and back_durs[i] is not None:
            rt_mins = float(out_durs[i] + back_durs[i])

        stop_costs[stop] = {
            "out_miles": out_dists[i],
            "out_mins": out_durs[i],
            "back_miles": back_dists[i],
            "back_mins": back_durs[i],
            "round_trip_miles": rt_miles,
            "round_trip_mins": rt_mins,
        }

    # Sort deliveries so large jobs get distributed early
    sorted_stops = sorted(
        stops,
        key=lambda s: _safe_min(stop_costs[s]["round_trip_mins"]),
        reverse=True,
    )

    # --- INITIALIZE DRIVER STATE ---
    driver_state: Dict[str, Dict[str, Any]] = {}
    for d in drivers:
        driver_state[d["name"]] = {
            "driver": d["name"],
            "start_location": d.get("start", ""),
            "home_location": d.get("home", d.get("start", "")),
            "deliveries": [],
            "legs": [],
            "total_distance_miles": 0.0,
            "total_duration_minutes": 0.0,
        }

    def can_add(driver_name: str, stop: str) -> bool:
        mins = stop_costs[stop]["round_trip_mins"]
        if mins is None:
            return False
        projected = driver_state[driver_name]["total_duration_minutes"] + mins
        return (projected / 60.0) <= max_hours_per_driver

    # --- ROUND ROBIN ASSIGNMENT ---
    unassigned = []
    driver_names = [d["name"] for d in drivers]
    driver_count = len(driver_names)
    driver_idx = 0

    for stop in sorted_stops:
        assigned = False
        attempts = 0

        while attempts < driver_count:
            name = driver_names[driver_idx]

            if can_add(name, stop):
                driver_state[name]["deliveries"].append(stop)
                driver_state[name]["total_distance_miles"] += float(
                    stop_costs[stop]["round_trip_miles"] or 0.0
                )
                driver_state[name]["total_duration_minutes"] += float(
                    stop_costs[stop]["round_trip_mins"] or 0.0
                )
                assigned = True
                driver_idx = (driver_idx + 1) % driver_count
                break

            driver_idx = (driver_idx + 1) % driver_count
            attempts += 1

        if not assigned:
            unassigned.append(stop)

    # --- BUILD LEGS & FINAL ROUTES ---
    for name, st in driver_state.items():
        legs = []
        total_miles = 0.0
        total_mins = 0.0
        seq = 1

        for stop in st["deliveries"]:
            c = stop_costs[stop]

            legs.append(
                {
                    "type": "deliver",
                    "from": base_reload_location,
                    "to": stop,
                    "distance_miles": c["out_miles"],
                    "duration_minutes": c["out_mins"],
                    "sequence": seq,
                }
            )
            legs.append(
                {
                    "type": "reload_to_base",
                    "from": stop,
                    "to": base_reload_location,
                    "distance_miles": c["back_miles"],
                    "duration_minutes": c["back_mins"],
                    "sequence": seq,
                }
            )

            if c["round_trip_miles"] is not None:
                total_miles += c["round_trip_miles"]
            if c["round_trip_mins"] is not None:
                total_mins += c["round_trip_mins"]

            seq += 1

        st["legs"] = legs
        st["total_distance_miles"] = total_miles
        st["total_duration_minutes"] = total_mins
        st["end_location"] = base_reload_location if st["deliveries"] else st["start_location"]

        st["deliveries"] = [
            {"delivery_stop": stop, "sequence": i + 1}
            for i, stop in enumerate(st["deliveries"])
        ]

    routes = [driver_state[d["name"]] for d in drivers]

    return {
        "base_reload_location": base_reload_location,
        "routes": routes,
        "unassigned_deliveries": unassigned,
        "notes": [
            "Round-robin assignment for fairness",
            "Reload enforced between every delivery",
            "Day-by-day planning; no global optimization",
        ],
    }
