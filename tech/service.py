from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

from environment import EcommerceEnvironment
from faultgen import generate_fault
from sandbox import TechnicalSandbox
from agent import TechnicalAgent

from bidding import submit_bid, share_capability
from negotiation import TechnicalNegotiationHandler


app = FastAPI(title="Technical Support Agent")


# --------------------------------------------------
# Shared environment and agent
# --------------------------------------------------

environment = EcommerceEnvironment()
sandbox = TechnicalSandbox(environment)
agent = TechnicalAgent(sandbox=sandbox)

current_load = 0

negotiation_handler = TechnicalNegotiationHandler()


# --------------------------------------------------
# Request models
# --------------------------------------------------

class Ticket(BaseModel):
    ticket_id: str
    text: str
    urgency_score: int = 0
    current_load: int = 0


class HandleTicketRequest(BaseModel):
    ticket: Ticket


class NegotiationRequest(BaseModel):
    action: Optional[str] = None
    message_type: Optional[str] = None

    sender: str
    receiver: Optional[str] = None

    my_assigned_subtask: Optional[str] = None
    your_requested_subtask: Optional[str] = None
    my_subtask: Optional[str] = None
    requested_subtask: Optional[str] = None
    rationale: Optional[str] = None
    modified_scope: Optional[str] = None


class CollaborationRequest(BaseModel):
    ticket: Ticket
    order_id: Optional[str] = None
    subtask: Optional[str] = None


class LoadRequest(BaseModel):
    current_load: int


# --------------------------------------------------
# Health check
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "agent": "technical_agent",
        "status": "running"
    }


# --------------------------------------------------
# Capability endpoint
# --------------------------------------------------

@app.get("/capability")
def capability():
    return share_capability()


# --------------------------------------------------
# Bidding endpoint
# --------------------------------------------------

@app.post("/bid")
def bid(request: Ticket):
    global current_load

    current_load = request.current_load

    return submit_bid(
        ticket=request.text,
        current_load=request.current_load,
        urgency_score=request.urgency_score,
        ticket_id=request.ticket_id
    )


# --------------------------------------------------
# Negotiation endpoint
# --------------------------------------------------

@app.post("/negotiate")
def negotiate(request: NegotiationRequest):
    message = request.model_dump(exclude_none=True)

    action = message.get("action") or message.get("message_type")

    if action == "PROPOSE":
        return negotiation_handler.handle_proposal(message)

    elif action == "COUNTER":
        return negotiation_handler.handle_counter(message)

    elif action == "ACCEPT":
        return {
            "action": "ACCEPT",
            "message_type": "ACCEPT",
            "sender": "technical_agent",
            "receiver": message.get("sender"),
            "status": "received",
            "rationale": "Acceptance received."
        }

    elif action == "REJECT":
        return {
            "action": "REJECT",
            "message_type": "REJECT",
            "sender": "technical_agent",
            "receiver": message.get("sender"),
            "status": "received",
            "rationale": "Rejection received."
        }

    else:
        return {
            "action": "REJECT",
            "message_type": "REJECT",
            "sender": "technical_agent",
            "receiver": message.get("sender"),
            "status": "rejected",
            "rationale": "Unknown negotiation message type."
        }


# --------------------------------------------------
# Collaboration endpoint
# --------------------------------------------------

@app.post("/collaborate")
def collaborate(request: CollaborationRequest):
    return agent.handle_collaboration(
        ticket=request.ticket.model_dump(),
        subtask=request.subtask or "Technical support subtask"
    )


# --------------------------------------------------
# Handle ticket endpoint
# --------------------------------------------------

@app.post("/handle_ticket")
def handle_ticket(request: HandleTicketRequest):
    ticket = request.ticket

    fault_result = generate_fault(environment)

    result = agent.solve(ticket.text)

    return {
        "agent": "technical_agent",
        "ticket": ticket.model_dump(),
        "fault_result": fault_result,
        "result": result,
        "environment": environment.get_state()
    }


# --------------------------------------------------
# Set agent load
# --------------------------------------------------

@app.post("/set_load")
def set_load(request: LoadRequest):
    global current_load

    current_load = max(0, request.current_load)

    return {
        "agent": "technical_agent",
        "current_load": current_load
    }