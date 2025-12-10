from google.adk.agents.sequential_agent import SequentialAgent

from agents.route_planner import route_planner_agent
from agents.backhaul import backhaul_agent
from agents.fairness import fairness_agent
from agents.summary import summary_agent

# This is the main entrypoint ADK Web UI looks for
root_agent = SequentialAgent(
    name="RouteWorkflowAgent",
    sub_agents=[
        route_planner_agent,
        backhaul_agent,
        fairness_agent,
        summary_agent,
    ],
)
