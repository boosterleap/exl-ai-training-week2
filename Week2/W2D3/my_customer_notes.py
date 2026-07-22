"""Day 3 PM, Topic 01 variation A -- episodic memory: one note per customer
"talk", persisted per thread_id so it survives across separate processes.

Reuses Day 2 Topic 06's checkpoint pattern (W2D2/hitl_demo.py): a
SqliteSaver-backed graph, invoked once per call with a thread_id-scoped
config. LangGraph accumulates the "notes" list across invocations for the
same thread_id via the operator.add reducer -- a second call for the same
thread_id appends, it doesn't overwrite.

Run it:
    uv run python W2D3/my_customer_notes.py jennifer-garcia "Talked to Jennifer Garcia about claim CLM-424063."
"""

from __future__ import annotations

import operator
import sys
from datetime import date
from pathlib import Path
from typing import Annotated, TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

DB_PATH = Path(__file__).parent / "outputs" / "customer_sessions.sqlite"


class SessionState(TypedDict):
    new_note: str
    notes: Annotated[list[str], operator.add]


def record_note(state: SessionState) -> dict:
    entry = f"[{date.today().isoformat()}] {state['new_note']}"
    print(f"[record_note] {entry}")
    return {"notes": [entry]}


def build_graph(checkpointer):
    graph = StateGraph(SessionState)
    graph.add_node("record_note", record_note)
    graph.add_edge(START, "record_note")
    graph.add_edge("record_note", END)
    return graph.compile(checkpointer=checkpointer)


def add_note(thread_id: str, note: str) -> list[str]:
    """Runs the graph once for thread_id, then the process ends -- no server, no loop."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SqliteSaver.from_conn_string(str(DB_PATH)) as checkpointer:
        app = build_graph(checkpointer)
        config = {"configurable": {"thread_id": thread_id}}
        result = app.invoke({"new_note": note}, config=config)
        return result["notes"]


def main() -> None:
    if len(sys.argv) < 3:
        print('Usage: python W2D3/my_customer_notes.py <thread_id> "<note>"')
        sys.exit(1)
    thread_id, note = sys.argv[1], sys.argv[2]
    notes = add_note(thread_id, note)
    print(f"\nAll notes on file for thread_id={thread_id!r}:")
    for n in notes:
        print(f"  {n}")


if __name__ == "__main__":
    main()
