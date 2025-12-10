# agents/backhaul.py
from google.adk.agents.llm_agent import LlmAgent
from tools.backhaul_planner import insert_backhauls_tool

GEMINI_MODEL = "gemini-2.0-flash"

backhaul_agent = LlmAgent(
    name="BackhaulAgent",
    model=GEMINI_MODEL,
    instruction="""
You are a backhaul planner.

Input:
- The session state contains a key 'routes_plan' which is a JSON string:
  { "routes": [ { "driver": ..., "stops": [...], ... }, ... ] }

Tool:
- `insert_backhauls_tool(routes_plan)` takes that JSON object
  and returns an UPDATED routes JSON with backhaul stops inserted
  when routes pass near ADM / ethanol plants.

Task:
1. Read and parse 'routes_plan' from session state.
2. Call `insert_backhauls_tool(routes_plan)` EXACTLY ONCE.
3. Return ONLY the JSON the tool gives you.
4. Store it into session state under 'routes_with_backhauls' via output_key.
""",
    description="Inserts backhaul stops based on distance to ADM / ethanol sites.",
    tools=[insert_backhauls_tool],
    output_key="routes_with_backhauls",
)
