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

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agent import BillingAgent
from sandbox import BillingSandbox
from capability import CAPABILITY_CARD

app = FastAPI(title="Billing Agent Service")

# Single shared sandbox + agent instance for this process.
# current_load would normally be updated by the external orchestrator
# as tickets are assigned/completed — see master doc section 8.
_sandbox = BillingSandbox()
_agent = BillingAgent(sandbox=_sandbox, current_load=0)


class Ticket(BaseModel):
    ticket_id: str
    text: str
    urgency_score: int = 0


class HandleTicketRequest(BaseModel):
    ticket: Ticket
    order_id: str


@app.get("/capability")
def get_capability():
    return CAPABILITY_CARD


@app.post("/bid")
def submit_bid(ticket: Ticket):
    return _agent.submit_bid(ticket.dict())


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