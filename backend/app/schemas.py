from pydantic import BaseModel


class AgentRequest(BaseModel):
    text: str
    user_id: str
    
    
class AgentResult(BaseModel):
    id: str
    text: str
    source: str  # "langgraph" | "mock"
    toast: str | None = None
    
class AgentResponse(BaseModel):
    ok: bool
    result: AgentResult