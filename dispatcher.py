"""
dispatcher.py

Exposes MarketOrchestrator over HTTP so a REAL, freely-typed customer
ticket can be submitted and run through the actual bid -> vet -> penalty
-> re-bid loop in orchestrator.py — no hardcoded tickets, no fixed
title/category/amount shape.

Place this file at the repo root, next to orchestrator.py.

Run:
    pip install fastapi uvicorn
    uvicorn dispatcher:app --port 8000 --reload
"""

import itertools

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from orchestrator import MarketOrchestrator

app = FastAPI(title="Multi-Agent Market Dispatcher")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = MarketOrchestrator()
ticket_counter = itertools.count(1)


class InjectedTicket(BaseModel):
    """
    ticket_text is the ONLY required field — a user can type any raw
    ticket text and submit nothing else. Everything below is optional
    metadata with sensible defaults, not a rigid form structure.
    """
    ticket_text: str
    urgency_score: int = 50
    order_id: str | None = None
    customer_id: str | None = None
    title: str | None = None
    category: str | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/capabilities")
def get_capabilities():
    """Real capability_card data straight from each live agent instance."""
    out = {}
    for agent_id, agent in orchestrator.agents.items():
        card = getattr(agent, "capability_card", None)
        if card is None and hasattr(agent, "get_capabilities"):
            card = agent.get_capabilities()
        out[agent_id] = card or {}
    return out


@app.post("/inject_ticket")
def inject_ticket(payload: InjectedTicket):
    """
    Runs a genuinely user-typed ticket through the real multi-round
    bid -> vet -> penalty -> re-bid loop in orchestrator.run_ticket().
    """
    ticket_text = (payload.ticket_text or "").strip()
    if not ticket_text:
        raise HTTPException(status_code=422, detail="ticket_text cannot be empty.")

    ticket_id = f"T-USER-{next(ticket_counter)}"
    ticket = {
        "ticket_id": ticket_id,
        "text": ticket_text,
        "urgency_score": payload.urgency_score,
        "order_id": payload.order_id or "O-1001",
        "customer_id": payload.customer_id or "C001",
    }

    result = orchestrator.run_ticket(
        ticket,
        order_id=ticket["order_id"],
        customer_id=ticket["customer_id"],
    )

    lead_agent_id = result.get("lead_agent", "unknown_agent")
    lead_agent = orchestrator.agents.get(lead_agent_id)

    indexed = []
    balance = None
    if lead_agent is not None and hasattr(lead_agent, "instance_index"):
        indexed = lead_agent.instance_index.get_indexed_instances()
        balance = getattr(lead_agent, "balance", None)

    return {
        "ticket_id": ticket_id,
        "ticket_text": ticket_text,
        "title": payload.title or ticket_text[:60],
        "category": payload.category,
        "winner": lead_agent_id,
        "final_statement": result.get("final_statement") or result.get("customer_statement"),
        "diagnosis": result.get("diagnosis"),
        "negotiation_transcript": result.get("negotiation_transcript", []),
        "state_before_after": result.get("state_before_after", []),
        "execution_results": result.get("execution_results") or result.get("actions_taken") or [],
        "instance_index": indexed[:5],
        "agent_balance": balance,
    }