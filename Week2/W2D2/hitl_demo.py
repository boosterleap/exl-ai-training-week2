"""Human-in-the-loop demo: LangGraph pauses a payout approval for a human.

Node 1 "propose" prints the proposed action and calls `interrupt(...)`, which
suspends the whole graph run and persists it via the SqliteSaver checkpointer.
Node 2 "execute" is only reachable once `pending_approval` has been cleared --
enforced both by a conditional edge and, defensively, inside the node itself.
"""

from pathlib import Path
from typing import Optional, TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

DB_PATH = Path(__file__).parent / "outputs" / "hitl_demo.sqlite"


class ApprovalState(TypedDict):

    
    claim_id: str
    amount: float
    pending_approval: bool
    approved: Optional[bool]
    executed: bool


def propose(state: ApprovalState) -> dict:
    print(
        f"\n[propose] Proposed action: approve ${state['amount']:.2f} "
        f"payout for {state['claim_id']}"
    )
    decision = interrupt(
        {
            "question": (
                f"Approve ${state['amount']:.2f} payout for "
                f"{state['claim_id']}? (y/n)"
            ),
            "claim_id": state["claim_id"],
            "amount": state["amount"],
        }
    )
    approved = str(decision).strip().lower() == "y"
    return {"pending_approval": False, "approved": approved}


def route_after_propose(state: ApprovalState) -> str:
    # Defensive guard: node 2 must never run while a human decision is
    # still outstanding. Once the interrupt is resumed, propose() has
    # already cleared the flag before this router sees the state.
    if state["pending_approval"]:
        return END
    return "execute"


def execute(state: ApprovalState) -> dict:
    if not state["approved"]:
        print(f"[execute] Approval declined for {state['claim_id']}; payout NOT executed.")
        return {"executed": False}
    print(f"[execute] Approved. Executing ${state['amount']:.2f} payout for {state['claim_id']}.")
    return {"executed": True}


def build_graph(checkpointer):
    graph = StateGraph(ApprovalState)
    graph.add_node("propose", propose)
    graph.add_node("execute", execute)
    graph.add_edge(START, "propose")
    graph.add_conditional_edges(
        "propose", route_after_propose, {"execute": "execute", END: END}
    )
    graph.add_edge("execute", END)
    return graph.compile(checkpointer=checkpointer)


def run(claim_id: str, amount: float) -> dict:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SqliteSaver.from_conn_string(str(DB_PATH)) as checkpointer:
        app = build_graph(checkpointer)
        config = {"configurable": {"thread_id": claim_id}}

        result = app.invoke(
            {
                "claim_id": claim_id,
                "amount": amount,
                "pending_approval": True,
                "approved": None,
                "executed": False,
            },
            config=config,
        )

        while "__interrupt__" in result:
            question = result["__interrupt__"][0].value["question"]
            answer = input(f"{question} ").strip().lower()
            while answer not in ("y", "n"):
                answer = input("Please answer y or n: ").strip().lower()
            result = app.invoke(Command(resume=answer), config=config)

        print(f"\nFinal state: {result}")
        return result


if __name__ == "__main__":
    run("CLM-424063", 500.0)
