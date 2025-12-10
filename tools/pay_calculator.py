# tools/pay_calculator.py
from typing import Optional, Dict, Any


def route_pay_calculator_tool(
    distance_miles: float,
    tons: float = 24.0,
    hours: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Calculate freight rate and driver pay for a single route.

    Business rules:
      - Minimum freight rate: $7/ton
      - Standard rate: (5.5 * distance_miles) / 24 tons
      - Driver gets 29% of freight revenue.
    """
    base_rate_per_ton = (5.5 * distance_miles) / 24.0
    freight_rate_per_ton = max(7.0, base_rate_per_ton)
    total_freight_revenue = freight_rate_per_ton * tons
    driver_pay = 0.29 * total_freight_revenue

    pay_per_hour = None
    if hours and hours > 0:
        pay_per_hour = driver_pay / hours

    return {
        "distance_miles": distance_miles,
        "tons": tons,
        "freight_rate_per_ton": round(freight_rate_per_ton, 2),
        "total_freight_revenue": round(total_freight_revenue, 2),
        "driver_pay": round(driver_pay, 2),
        "pay_per_hour": round(pay_per_hour, 2) if pay_per_hour else None,
    }
