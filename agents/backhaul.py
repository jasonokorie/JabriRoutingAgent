# agents/backhaul.py
from google.adk.agents.llm_agent import LlmAgent
from tools.backhaul_planner import insert_backhauls_tool

GEMINI_MODEL = "gemini-2.0-flash"

backhaul_agent = LlmAgent(
    name="BackhaulAgent",
    model=GEMINI_MODEL,
    instruction="""
You are BackhaulAgent. You MUST use the tool.

INPUT (from session state)
- session state key: 'routes_plan'
- It is a JSON object with this shape (abbrev):
{
  "base_reload_location": "...",
  "routes": [
    {
      "driver": "...",
      "deliveries": [{"delivery_stop": "...", "sequence": 1}, ...],
      "legs": [
        {"type":"deliver", "from": base, "to": stop, ...},
        {"type":"reload_to_base", "from": stop, "to": base, ...},
        ...
      ],
      "total_duration_minutes": ...
    }
  ]
}

REAL BACKHAUL RULES
- Backhauls are opportunistic:
  - If a backhaul pickup is on the way back to base (GI) after a delivery, add it.
  - If it is nearby (small detour) and does not cause a big time imbalance, add it.
- There is NO fixed mile radius; use "detour minutes budget" instead.
- Backhaul insertion should primarily consider legs where:
  leg.type == "reload_to_base"
  (i.e., stop -> base travel)

TOOL
- insert_backhauls_tool(routes_plan) inserts backhaul legs/stops.
- You MUST call insert_backhauls_tool EXACTLY ONCE.

TASK
1) Read and parse routes_plan from session state (it is already JSON).
2) Call insert_backhauls_tool(routes_plan) exactly once.
3) Return ONLY the JSON output from the tool (no prose, no markdown).
""",
    description="Inserts backhaul pickups along reload legs based on distance to ADM / ethanol sites.",
    tools=[insert_backhauls_tool],
    output_key="routes_with_backhauls",
)
