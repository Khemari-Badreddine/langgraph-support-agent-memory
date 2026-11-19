from pydantic import BaseModel


class AgentRequest(BaseModel):
    text: str
    user_id: str
    session_id: str


class TraceStep(BaseModel):
    step: str               # triage | billing | tech | order | general | memory
    detail: str
    memories_updated: bool = False


class AgentResult(BaseModel):
    id: str
    text: str
    intent: str             # billing | tech | order | general
    specialist: str         # "Billing Agent" etc — shown in routing badge
    trace: list[TraceStep]  # shown in expandable trace panel
    memories_updated: bool = False


class AgentResponse(BaseModel):
    ok: bool
    result: AgentResult