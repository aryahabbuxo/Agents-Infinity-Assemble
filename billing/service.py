"""
service.py

Exposes the Billing Agent as a small FastAPI service so the hackathon's
central auction/dispatch layer can call into it instead of importing this
as a Python module.

Run:
    pip install fastapi uvicorn
    uvicorn service:app --port 8000 --reload

Endpoints:
    POST /bid            -> {ticket_id, agent_id, raw_confidence, load_penalty,
                              urgency_weight, final_bid}
    POST /handle_ticket   -> full pipeline result (investigation, diagnosis,
                              execution_results, negotiation_transcript,
                              final_statement, state_before_after)
    GET  /capability      -> this agent's capability card (section 9)
"""

from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from billing.agent import BillingAgent
from billing.sandbox import BillingSandbox
from billing.capability import CAPABILITY_CARD

app = FastAPI(title="Billing Agent Service")

_sandbox = BillingSandbox()
_agent = BillingAgent(sandbox=_sandbox, current_load=0)


class Ticket(BaseModel):
    ticket_id: str
    text: str
    urgency_score: int = 0
    order_id: Optional[str] = None


class HandleTicketRequest(BaseModel):
    ticket: Ticket
    order_id: str


class NegotiationMessage(BaseModel):
    sender: str
    receiver: Optional[str] = None
    action: Optional[str] = None
    message_type: Optional[str] = None
    my_assigned_subtask: Optional[str] = None
    your_requested_subtask: Optional[str] = None
    my_subtask: Optional[str] = None
    requested_subtask: Optional[str] = None
    modified_scope: Optional[str] = None
    rationale: Optional[str] = None


class CollaborationRequest(BaseModel):
    ticket: Ticket
    order_id: str
    subtask: Optional[str] = None


@app.get("/capability")
def get_capability():
    return CAPABILITY_CARD


@app.post("/bid")
def submit_bid(ticket: Ticket):
    return _agent.submit_bid(ticket.dict())


@app.post("/negotiate")
def negotiate(message: NegotiationMessage):
    proposal = message.dict(exclude_none=True)
    if "action" not in proposal and "message_type" in proposal:
        proposal["action"] = proposal["message_type"]
    return _agent.respond_to_proposal(proposal)


@app.post("/collaborate")
def collaborate(req: CollaborationRequest):
    return _agent.handle_collaboration(
        ticket=req.ticket.dict(),
        order_id=req.order_id,
        subtask=req.subtask or "Execute requested billing task",
    )


@app.post("/handle_ticket")
def handle_ticket(req: HandleTicketRequest):
    try:
        return _agent.handle_ticket(req.ticket.dict(), order_id=req.order_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown order_id: {req.order_id}")


@app.post("/set_load")
def set_load(current_load: int):
    """Lets the external orchestrator update this agent's workload (section 8)."""
    _agent.current_load = current_load
    return {"agent_id": _agent.agent_id, "current_load": _agent.current_load}