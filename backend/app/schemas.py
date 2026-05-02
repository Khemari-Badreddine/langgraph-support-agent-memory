from pydantic import BaseModel


class AgentRequest(BaseModel):
    text: str
    user_id: str | None = None
    session_id: str | None = None


class AgentResult(BaseModel):
    id: str
    text: str
    source: str = "langgraph"
    toast: str | None = None


class AgentResponse(BaseModel):
    ok: bool = True
    result: AgentResult
