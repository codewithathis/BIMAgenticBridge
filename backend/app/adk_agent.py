"""Google ADK agent definition for Gen AI Academy Track 1 / Cloud Run."""

from __future__ import annotations

from google.adk.agents import Agent

from app.services.tool_loop import SYSTEM_PROMPT
from app.tools.room_query import query_room_data_tool

root_agent = Agent(
    name="bim_agentic_bridge",
    model="gemini-1.5-flash",
    description=(
        "Customer-facing BIM agent for room, door, window, and level questions "
        "grounded in Revit-extracted model data."
    ),
    instruction=SYSTEM_PROMPT,
    tools=[query_room_data_tool],
)
