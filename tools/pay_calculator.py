# tools/pay_calculator.py
from typing import Optional, Dict, Any


MIN_RATE_PER_TON = 7.00
RATE_PER_MILE = 5.50
TONS_PER_LOAD = 24.0
DRIVER_PAY_PERCENT = 0.29


def route_pay_calculator_tool(
    distance_miles: float,
    tons: float,
    hours: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Calculate freight revenue and driver pay for a route.

    Business Rules (Confirmed):
    - Freight rate per ton:
        max($7.00, (5.50 * distance_miles) / 24)
    - Each delivery = 24 tons (handled upstream)
    - Driver earns 29% of total freight revenue
    - Pay/hour computed only if hours > 0

    Args:
        distance_miles: Total miles driven for the route
        tons: Total tons hauled on the route (e.g., deliveries * 24)
        hours: Total driving hours (optional)

    Returns:
        {
          "distance_miles": float,
          "tons": float,
          "freight_rate_per_ton": float,
          "total_freight_revenue": float,
          "driver_pay": float,
          "pay_per_hour": Optional[float]
        }
    """

    # Defensive normalization
    distance_miles = max(float(distance_miles or 0.0), 0.0)
    tons = max(float(tons or 0.0), 0.0)

    # Edge case: no work = no pay
    if distance_miles == 0 or tons == 0:
        return {
            "distance_miles": round(distance_miles, 2),
            "tons": tons,
            "freight_rate_per_ton": 0.0,
            "total_freight_revenue": 0.0,
            "driver_pay": 0.0,
            "pay_per_hour": 0.0 if hours and hours > 0 else None,
        }

    # Core freight math
    calculated_rate = (RATE_PER_MILE * distance_miles) / TONS_PER_LOAD
    freight_rate_per_ton = max(MIN_RATE_PER_TON, calculated_rate)
    total_freight_revenue = freight_rate_per_ton * tons
    driver_pay = DRIVER_PAY_PERCENT * total_freight_revenue

    pay_per_hour: Optional[float] = None
    if hours is not None and hours > 0:
        pay_per_hour = driver_pay / hours

    return {
        "distance_miles": round(distance_miles, 2),
        "tons": tons,
        "freight_rate_per_ton": round(freight_rate_per_ton, 2),
        "total_freight_revenue": round(total_freight_revenue, 2),
        "driver_pay": round(driver_pay, 2),
        "pay_per_hour": round(pay_per_hour, 2) if pay_per_hour is not None else None,
    }

