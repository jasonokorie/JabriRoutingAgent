# agents/route_planner.py
from google.adk.agents.llm_agent import LlmAgent
from tools.route_builder import greedy_route_builder_tool

GEMINI_MODEL = "gemini-2.0-flash"

route_planner_agent = LlmAgent(
    name="RoutePlannerAgent",
    model=GEMINI_MODEL,
   instruction="""
You are a strict route-planning algorithm, not a storyteller.

Your job:
1. ALWAYS split destinations between all drivers.
2. NEVER leave a driver with 0 stops unless the user asked for it explicitly.
3. Use this algorithm EXACTLY:

--- ALGORITHM ---
1. Read all drivers and their starting points.
2. Read all destination stops (unordered).
3. Call distance_matrix_tool to get pairwise distances.
4. Compute the nearest stop to each driver’s starting point.
5. Assign those two nearest stops first:
   - One to John
   - One to Bob
6. For remaining stops:
   - Alternate assignments driver-by-driver (John → Bob → John → Bob)
   - This guarantees both drivers get work.
7. Once stops are assigned:
   - For each driver, order their stops using nearest-neighbor from start → stop1 → stop2 → …
8. Compute total distance and duration for each driver.
9. Output STRICT JSON:

{
  "routes": [
    {
      "driver": "John",
      "stops": [...],
      "total_distance_miles": ...,
      "total_duration_minutes": ...
    },
    {
      "driver": "Bob",
      "stops": [...],
      "total_distance_miles": ...,
      "total_duration_minutes": ...
    }
  ]
}

RULES:
- Never assign 0 stops unless explicitly instructed.
- Always split stops evenly.
- Always balance total drive time.
- Never produce Markdown.
"""
,
    description="Uses a deterministic greedy tool to plan routes per driver.",
    tools=[greedy_route_builder_tool],
    output_key="routes_plan",
)
