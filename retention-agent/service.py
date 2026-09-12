from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agent.retention_agent import RetentionAgent


app = FastAPI(
    title="Retention Agent",
    description="Autonomous customer retention support agent",
    version="1.0.0",
)

_agent = RetentionAgent()


class Ticket(BaseModel):
    ticket_id: str
    text: str
    urgency_score: int = 0
    order_id: str | None = None


class HandleTicketRequest(BaseModel):
    ticket: Ticket
    customer_id: str


class NegotiationMessage(BaseModel):
    sender: str
    receiver: str | None = None
    action: str
    my_assigned_subtask: str | None = None
    your_requested_subtask: str | None = None
    modified_scope: str | None = None
    rationale: str | None = None


class CollaborationRequest(BaseModel):
    ticket: Ticket
    customer_id: str
    subtask: str


class SetLoadRequest(BaseModel):
    current_load: int


@app.get("/")
def root():
    return {
        "agent": "Retention Agent",
        "agent_id": _agent.agent_id,
        "status": "running",
        "endpoints": {
            "health": "GET /health",
            "capability": "GET /capability",
            "bid": "POST /bid",
            "handle_ticket": "POST /handle_ticket",
            "negotiate": "POST /negotiate",
            "collaborate": "POST /collaborate",
            "set_load": "POST /set_load",
        },
    }


@app.get("/health")
def health():
    return {"status": "ok", "agent_id": _agent.agent_id}


@app.get("/capability")
def get_capability():
    return _agent.get_capabilities()


@app.post("/bid")
def submit_bid(ticket: Ticket):
    try:
        return _agent.submit_bid(ticket.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/handle_ticket")
def handle_ticket(request: HandleTicketRequest):
    try:
        ticket = request.ticket.model_dump()
        return _agent.handle_ticket(
            ticket=ticket,
            customer_id=request.customer_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/negotiate")
def negotiate(message: NegotiationMessage):
    try:
        proposal = message.model_dump(exclude_none=True)
        return _agent.respond_to_proposal(proposal)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/collaborate")
def collaborate(request: CollaborationRequest):
    try:
        return _agent.handle_collaboration(
            ticket=request.ticket.model_dump(),
            customer_id=request.customer_id,
            subtask=request.subtask,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/set_load")
def set_load(request: SetLoadRequest):
    return _agent.set_load(request.current_load)
