from typing import TypedDict


# ── Graph state ───────────────────────────────────────────────────────────────
class AgentState(TypedDict):
    messages: list[dict]
    user_id: str
    session_id: str
    intent: str  # set by triage: billing | tech | order | general
    specialist: str  # human-readable name for the frontend badge
    trace: list[dict]  # list of {step, detail} for the frontend trace panel
