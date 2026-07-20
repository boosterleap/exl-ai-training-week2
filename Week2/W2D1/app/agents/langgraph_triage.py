"""LangGraph Day 1 triage agent shape (study only)."""

from __future__ import annotations

from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from .. import config
from ..models import TriageDecision
from ..tools import insurance


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


def build_tools() -> list:
    return [
        insurance.fnol_lookup,
        insurance.claim_lookup,
        insurance.policy_lookup,
    ]


def build_graph(llm):
    """Wire a simple ReAct-style loop: model <-> tools -> structured decision."""
    tools = build_tools()
    model = llm.bind_tools(tools)

    def call_model(state: AgentState):
        return {"messages": [model.invoke(state["messages"])]}

    graph = StateGraph(AgentState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", ToolNode(tools))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")
    return graph.compile()


def run_triage(graph, email_id: str) -> TriageDecision:
    """Study helper: run the loop then ask for a TriageDecision."""
    prompt = (
        f"Triage FNOL email {email_id}. "
        f"Use tools. Stay within {config.MAX_TURNS} turns."
    )
    result = graph.invoke({"messages": [("user", prompt)]})
    # In demos, structured output is applied on the final assistant turn.
    last = result["messages"][-1]
    return TriageDecision.model_validate_json(last.content)
