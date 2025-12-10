# agents/fairness.py
from google.adk.agents.llm_agent import LlmAgent
from tools.pay_calculator import route_pay_calculator_tool

GEMINI_MODEL = "gemini-2.0-flash"

fairness_agent = LlmAgent(
    name="FairnessAgent",
    model=GEMINI_MODEL,
    instruction="""
You are a fairness auditor for driver pay and hours.

Input:
- The session state contains a key 'routes_with_backhauls' which is a JSON string
  in the format:
  {
    "routes": [
      {
        "driver": "...",
        "stops": [...],
        "total_distance_miles": ...,
        "total_duration_minutes": ...
      },
      ...
    ]
  }

Tools:
- You can call `route_pay_calculator_tool(distance_miles, tons, hours)`.

Task:
1. Read and parse 'routes_with_backhauls'.
2. For each driver route:
   - Compute total hours from 'total_duration_minutes' (divide by 60).
   - Assume 24 tons per full route for now.
   - Call 'route_pay_calculator_tool' with distance_miles and hours.
3. Produce a FAIRNESS REPORT in JSON:

{
  "driver_stats": [
    {
      "name": "John",
      "hours": 9.3,
      "pay": 430.12,
      "pay_per_hour": 46.25
    },
    {
      "name": "Bob",
      "hours": 8.8,
      "pay": 415.77,
      "pay_per_hour": 47.25
    }
  ],
  "avg_pay_per_hour": 46.75,
  "max_deviation_percent": 3.2
}

Rules:
- Parse and validate the JSON before using it.
- Use the tool output numerically, not by guessing.
- Return ONLY the final fairness JSON (no prose, no markdown).
""",
    description="Evaluates fairness of the routes using pay calculations.",
    tools=[route_pay_calculator_tool],
    output_key="fairness_report",
)
