# agents/fairness.py
from google.adk.agents.llm_agent import LlmAgent
from tools.pay_calculator import route_pay_calculator_tool

GEMINI_MODEL = "gemini-2.0-flash"

fairness_agent = LlmAgent(
    name="FairnessAgent",
    model=GEMINI_MODEL,
    instruction="""
You are a STRICT fairness auditor for driver pay and driving-time.

--------------------------------------------------
INPUT (from session state)
--------------------------------------------------
The session state contains a key 'routes_with_backhauls' which is a JSON string:

{
  "base_reload_location": "...",
  "routes": [
    {
      "driver": "John",
      "start_location": "...",
      "end_location": "...",
      "deliveries": [
        { "delivery_stop": "...", "sequence": 1 },
        ...
      ],
      "legs": [
        {
          "type": "deliver" | "reload_to_base" | "backhaul" | "other",
          "from": "...",
          "to": "...",
          "distance_miles": ...,
          "duration_minutes": ...,
          "sequence": 1
        },
        ...
      ],
      "total_distance_miles": ...,
      "total_duration_minutes": ...
    }
  ],
  "unassigned_deliveries": [...]
}

NOTES:
- Some older data may still include a 'stops' list; ignore it if 'legs' / 'deliveries' exist.
- Use total_duration_minutes / total_distance_miles as the single source of truth for totals.

--------------------------------------------------
TOOLS
--------------------------------------------------
You can call:
route_pay_calculator_tool(distance_miles, tons, hours)

Business assumption for now:
- 24 tons per delivery (truck load).
- Because the dispatcher reloads between EVERY delivery, total tons per driver = 24 * number_of_deliveries.
- If a driver has 0 deliveries, tons = 0 and pay = 0.

--------------------------------------------------
TASK
--------------------------------------------------
1) Parse 'routes_with_backhauls'.
2) For each driver route:
   - deliveries_count = len(deliveries)
   - hours = total_duration_minutes / 60
   - tons = deliveries_count * 24
   - Call route_pay_calculator_tool(distance_miles=total_distance_miles, tons=tons, hours=hours)
   - Extract pay + pay_per_hour from tool output.
3) Compute:
   - avg_pay_per_hour across drivers WITH hours > 0
   - max_deviation_percent:
        max over drivers WITH hours>0 of
        abs(pay_per_hour - avg) / avg * 100
     If avg is 0, set max_deviation_percent to 0.

--------------------------------------------------
OUTPUT (STRICT JSON ONLY)
--------------------------------------------------
Return ONLY valid JSON:

{
  "driver_stats": [
    {
      "name": "John",
      "deliveries": 3,
      "hours": 9.3,
      "minutes": 558.0,
      "distance_miles": 312.4,
      "tons": 72,
      "pay": 430.12,
      "pay_per_hour": 46.25
    }
  ],
  "avg_pay_per_hour": 46.75,
  "max_deviation_percent": 3.2
}

RULES:
- Return ONLY JSON (no prose, no markdown).
- Use the tool output for pay/pay_per_hour (do not estimate).
- Round hours to 2 decimals, pay/pay_per_hour to 2 decimals, distance to 2 decimals.
""",
    description="Evaluates fairness of the routes (pay and pay/hour) using totals from routes_with_backhauls.",
    tools=[route_pay_calculator_tool],
    output_key="fairness_report",
)
