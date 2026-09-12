from pydantic import BaseModel
from typing import Optional


class AgentAction(BaseModel):
    action: str
    customer_id: str
    reason: Optional[str] = None