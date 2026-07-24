"""CrewAI scaffold: two agents + one task each, wired into a Crew.

Construction only — .kickoff() is intentionally not called.
"""

from crewai import Agent, Task, Crew, Process

intake_specialist = Agent(
    role="Intake Specialist",
    goal=(
        "Read an inbound insurance claim email and extract the claim_id/policy_id "
        "and the customer's request, flagging anything missing before it moves "
        "downstream."
    ),
    backstory=(
        "A claims operations veteran who has triaged thousands of inbound emails. "
        "Knows the intake schema cold and never lets an ungrounded assumption pass "
        "through to the next stage."
    ),
    allow_delegation=False,
    verbose=True,
)

policy_researcher = Agent(
    role="Policy Researcher",
    goal=(
        "Given a claim_id/policy_id, look up the matching claim record and the "
        "governing policy document, and determine exactly what coverage terms "
        "apply, citing the source document."
    ),
    backstory=(
        "A meticulous policy analyst who never states a coverage conclusion "
        "without a citation to the specific claims record or policy clause "
        "that supports it."
    ),
    allow_delegation=False,
    verbose=True,
)

intake_task = Task(
    description=(
        "Given the raw text of an inbound customer email, identify the claim_id "
        "or policy_id referenced, summarize the customer's request in one or two "
        "sentences, and note any information required to resolve the request that "
        "is missing from the email."
    ),
    expected_output=(
        "A short structured summary: claim_id/policy_id, customer request, and a "
        "list of any missing information."
    ),
    agent=intake_specialist,
)

policy_research_task = Task(
    description=(
        "Using the claim_id/policy_id identified during intake, look up the claim "
        "record and the applicable policy document, then determine whether the "
        "customer's request is covered. Every statement about coverage must cite "
        "the specific record or policy clause it comes from."
    ),
    expected_output=(
        "A grounded coverage determination with citations to the claim record and "
        "policy document, or an explicit note that escalation is required if the "
        "tool results don't cover the request."
    ),
    agent=policy_researcher,
    context=[intake_task],
)

crew = Crew(
    agents=[intake_specialist, policy_researcher],
    tasks=[intake_task, policy_research_task],
    process=Process.sequential,
    verbose=True,
)

if __name__ == "__main__":
    print("Crew scaffold built successfully.")
    print(f"Agents ({len(crew.agents)}):")
    for agent in crew.agents:
        print(f"  - role={agent.role!r} allow_delegation={agent.allow_delegation}")

    print(f"Tasks ({len(crew.tasks)}):")
    for task in crew.tasks:
        print(f"  - agent={task.agent.role!r} description={task.description[:60]!r}...")

    print(f"Process: {crew.process}")
    print("kickoff() was not called — construction-only scaffold.")
