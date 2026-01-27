# main.py
import os
import json
import dotenv
import google.generativeai as genai

from google.genai import types
from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner

from agents.route_planner import route_planner_agent
from agents.backhaul import backhaul_agent
from agents.fairness import fairness_agent
from agents.summary import summary_agent

# ---------------------------------------------------------
# ENV + MODEL CONFIG
# ---------------------------------------------------------
dotenv.load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise RuntimeError("Please set GOOGLE_API_KEY in your .env file")

genai.configure(api_key=api_key)

# Quick fix: ADK may load agents from a top-level package named 'agents'.
# To avoid app-name mismatch errors during development, set app name
# to 'agents' so the session service and runner agree. For a cleaner
# fix, rename the local `agents` package to avoid colliding with the
# installed `google.adk.agents` package.
APP_NAME = "agents"
USER_ID = "dispatcher_01"
SESSION_ID = "demo_session_01"

# ---------------------------------------------------------
# SEQUENTIAL AGENT: Planner -> Backhaul -> Fairness -> Summary
# ---------------------------------------------------------
route_workflow_agent = SequentialAgent(
    name="RouteWorkflowAgent",
    sub_agents=[
        route_planner_agent,
        backhaul_agent,
        fairness_agent,
        summary_agent,
    ],
)

session_service = InMemorySessionService()
# Use the synchronous helper to avoid awaiting the coroutine in a
# synchronous script context.
session_service.create_session_sync(
    app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
)
runner = Runner(
    agent=route_workflow_agent,
    app_name=APP_NAME,
    session_service=session_service,
)


def call_agent(query: str):
    content = types.Content(role="user", parts=[types.Part(text=query)])
    events = runner.run(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=content,
    )

    final_text = None
    for event in events:
        if event.is_final_response():
            if event.content and event.content.parts:
                final_text = event.content.parts[0].text

    print("\n=== FINAL HUMAN SUMMARY (from SummaryAgent) ===")
    print(final_text)

    # Also show fairness JSON from session if you want
    # Use the synchronous get_session to retrieve session state.
    sess = session_service.get_session_sync(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )
    state = sess.state if sess is not None else {}
    fairness_json = state.get("fairness_report")
    if fairness_json:
        print("\n=== Fairness Report JSON ===")
        try:
            print(json.dumps(json.loads(fairness_json), indent=2))
        except Exception:
            print(fairness_json)



demo_prompt = """
We have 2 drivers: John and Bob.
Destinations:
- 7878 140th Rd S, Wood River, NE 68883
- 214 20th St, Central City, NE 68826
- 3000 8th St E, Columbus, NE 68601
- 1414 Rd O, York, NE 68467
- 4225 E South St, Hastings, NE 68901
- 2103 Harvest Dr, Aurora, NE 68818
- 10868 189th St, Council Bluffs, IA 51503

John's Starting Point:
- 208 N Wheeler Ave, Grand Island, NE 68803

Bob's Starting Point:
- 7175 St.Paul Rd, Grand Island, NE 68801

Plan balanced routes for John and Bob, insert backhaul pickups near ADM / ethanol plants,
and summarize the day for Russ.
"""
call_agent(demo_prompt)
