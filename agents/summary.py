# agents/summary.py
from google.adk.agents.llm_agent import LlmAgent

GEMINI_MODEL = "gemini-2.0-flash"

summary_agent = LlmAgent(
    name="HumanReviewAgent",
    model=GEMINI_MODEL,
    instruction="""
You are generating a daily schedule summary for Russ, the dispatcher.

Session state will contain:
- 'routes_with_backhauls': JSON string, format:
  {
    "routes": [
      {
        "driver": "John",
        "stops": [...],
        "total_distance_miles": ...,
        "total_duration_minutes": ...
      },
      ...
    ]
  }
- 'fairness_report': JSON string, format:
  {
    "driver_stats": [
      {
        "name": "John",
        "hours": ...,
        "pay": ...,
        "pay_per_hour": ...
      },
      ...
    ],
    "avg_pay_per_hour": ...,
    "max_deviation_percent": ...
  }

Task:
1. Read and parse BOTH 'routes_with_backhauls' and 'fairness_report'.
2. Produce a human-readable summary for Russ that includes:
   - For each driver:
     - Start location (from the first stop, after 'START:')
     - Ordered list of stops (group backhaul pickups visually)
     - Total hours (from fairness report)
     - Estimated pay and pay/hour
   - A short global fairness summary:
     - Average pay/hour
     - Max deviation percent
3. Format as simple, readable text with headings and bullet points.
4. Do NOT output JSON. This is for humans.

Tone:
- Clear, concise, dispatch-ops style.
- Avoid technical jargon about agents or tools.
""",
    description="Creates a human-readable daily schedule summary for Russ.",
    tools=[],
    output_key="human_summary",
)
