"""
dispatcher.py

Exposes MarketOrchestrator over HTTP so customer tickets (pre-loaded or user-typed)
can be enqueued, executed through the bid -> vet -> penalty -> re-bid market loop,
and inspected step-by-step in the Agent Call Trace Dashboard.

Run:
    pip install fastapi uvicorn
    uvicorn dispatcher:app --port 8000 --reload
"""

import itertools
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from orchestrator import MarketOrchestrator
from shared_data import TICKETS, ORDERS, CUSTOMERS

app = FastAPI(title="Multi-Agent Market Dispatcher")

class InjectedTicket(BaseModel):
    ticket_text: str
    urgency_score: int = 50
    order_id: Optional[str] = None
    customer_id: Optional[str] = None
    title: Optional[str] = None
    category: Optional[str] = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for dev flexibility
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = MarketOrchestrator()
ticket_counter = itertools.count(100)

# -----------------------------------------------------------------------------
# SMART ORDER/CUSTOMER AUTO-DETECTION
# -----------------------------------------------------------------------------
# Maps ticket text keywords to the correct order_id and customer_id from shared_data
# so the sandbox investigation runs against the right records.

KEYWORD_ORDER_MAP = [
    # (keywords_in_ticket_text, order_id, customer_id)
    (["refund", "pending", "hasn't shown up", "2 days", "payment"],                      "O-1001", "C002"),
    (["rejected", "bank", "invalid"],                                                     "O-1002", "C003"),
    (["visible", "orders section", "profile dashboard", "return", "no longer visible"],   "O-1003", "C001"),
    (["invoice", "never generated", "receipt", "missing invoice"],                        "O-1004", "C004"),
    (["duplicate", "charged twice", "twice", "same order"],                               "O-1005", "C001"),
    (["subscription", "billed twice", "same cycle"],                                      "O-1006", "C002"),
    (["partial", "partially processed"],                                                  "O-1007", "C003"),
    (["locked", "cannot log in", "login", "account is locked"],                           "O-1004", "C004"),
    (["cancel", "cancellation", "leaving", "3 years", "subscription"],                    "O-1002", "C003"),
]

def auto_detect_order_customer(ticket_text: str) -> tuple:
    """
    Scans ticket text for known keywords and returns the best-matching
    (order_id, customer_id) pair. Falls back to O-1001, C001 if no match.
    """
    text_lower = ticket_text.lower()
    best_match = None
    best_score = 0

    for keywords, order_id, customer_id in KEYWORD_ORDER_MAP:
        score = sum(1 for kw in keywords if kw.lower() in text_lower)
        if score > best_score:
            best_score = score
            best_match = (order_id, customer_id)

    if best_match and best_score >= 1:
        return best_match
    return ("O-1001", "C001")


# -----------------------------------------------------------------------------
# IN-MEMORY STATE & QUEUE MANAGEMENT
# -----------------------------------------------------------------------------
# Ticket structure: { ticket_id, text, urgency_score, order_id, customer_id, title, category, status, is_rebid }
ticket_queue = []
executed_tickets = []
agent_trace_logs = []

def _execute_single_ticket(ticket: dict) -> dict:
    """Helper to run a ticket through MarketOrchestrator and handle re-bids & logging."""
    ticket["status"] = "EXECUTING"
    
    result = orchestrator.run_ticket(
        ticket,
        order_id=ticket.get("order_id", "O-1001"),
        customer_id=ticket.get("customer_id", "C001"),
    )
    
    ticket["status"] = "COMPLETED"
    executed_tickets.append({
        "ticket": ticket,
        "result": result,
        "executed_at": time.time(),
    })

    # Log step-by-step agent calls and actions into trace history
    trace_steps = result.get("trace_steps", [])
    for step in trace_steps:
        agent_trace_logs.append({
            "timestamp": time.strftime("%H:%M:%S"),
            "ticket_id": ticket["ticket_id"],
            "ticket_text": ticket["text"],
            "is_rebid": ticket.get("is_rebid", False),
            "iteration": step.get("iteration", 1),
            "bids": step.get("bids", []),
            "winning_bid": step.get("winning_bid", {}),
            "winner": step.get("lead_agent_id") or result.get("lead_agent") or "billing_agent",
            "diagnosis": step.get("diagnosis"),
            "negotiation_transcript": step.get("negotiation_transcript", []),
            "state_before_after": step.get("state_before_after", []),
            "execution_results": step.get("execution_results", []),
            "vetting": step.get("vetting", {}),
            "penalty_info": step.get("penalty_info", {}),
            "indexed_instances": step.get("indexed_instances", []),
            "rebound_triggered": step.get("rebound_triggered", False),
            "rebound_subticket": step.get("rebound_subticket"),
        })

    # Re-bid subtickets enter the queue for subsequent execution
    rebid_subtickets = result.get("rebid_subtickets", [])
    for rebid_t in rebid_subtickets:
        rebid_item = {
            "ticket_id": rebid_t["ticket_id"],
            "text": rebid_t["text"],
            "urgency_score": rebid_t.get("urgency_score", 70),
            "order_id": rebid_t.get("order_id", ticket.get("order_id", "O-1001")),
            "customer_id": rebid_t.get("customer_id", ticket.get("customer_id", "C001")),
            "title": f"Re-Bid Iteration #{rebid_t.get('rebid_iteration', 2)}: {rebid_t['text'][:40]}",
            "category": ticket.get("category", "re-bid"),
            "status": "QUEUED",
            "is_rebid": True,
            "parent_ticket_id": ticket["ticket_id"],
        }
        ticket_queue.append(rebid_item)

    lead_agent_id = result.get("lead_agent", "unknown_agent")
    lead_agent = orchestrator.agents.get(lead_agent_id)
    indexed = []
    balance = None
    if lead_agent is not None and hasattr(lead_agent, "instance_index"):
        indexed = lead_agent.instance_index.get_indexed_instances()
        balance = getattr(lead_agent, "balance", None)

    return {
        "ticket_id": ticket["ticket_id"],
        "ticket_text": ticket["text"],
        "title": ticket.get("title", ticket["text"][:60]),
        "category": ticket.get("category"),
        "winner": lead_agent_id,
        "final_statement": result.get("final_statement"),
        "diagnosis": result.get("diagnosis"),
        "negotiation_transcript": result.get("negotiation_transcript", []),
        "state_before_after": result.get("state_before_after", []),
        "execution_results": result.get("execution_results") or [],
        "vetting": trace_steps[-1].get("vetting") if trace_steps else {},
        "penalty_info": trace_steps[-1].get("penalty_info") if trace_steps else {},
        "bids": trace_steps[-1].get("bids") if trace_steps else [],
        "trace_steps": trace_steps,
        "instance_index": indexed[:5],
        "agent_balance": balance,
        "rebid_enqueued": len(rebid_subtickets) > 0,
        "rebid_subtickets": rebid_subtickets,
        "remaining_queue_length": len(ticket_queue),
    }


def _get_full_trace_payload(exec_result=None):
    agent_balances = {
        agent_id: getattr(agent_obj, "balance", 0.0)
        for agent_id, agent_obj in orchestrator.agents.items()
    }
    all_instance_indexes = {
        agent_id: agent_obj.instance_index.get_indexed_instances()
        for agent_id, agent_obj in orchestrator.agents.items()
        if hasattr(agent_obj, "instance_index")
    }
    return {
        "execution_result": exec_result,
        "trace_logs": agent_trace_logs,
        "agent_balances": agent_balances,
        "instance_indexes": all_instance_indexes,
        "pending_queue": ticket_queue,
        "executed_tickets": executed_tickets,
        "executed_tickets_summary": [
            {
                "ticket_id": item["ticket"]["ticket_id"],
                "title": item["ticket"].get("title"),
                "ticket_text": item["ticket"].get("text", ""),
                "winner": item["result"].get("lead_agent"),
                "final_statement": item["result"].get("final_statement"),
            }
            for item in executed_tickets
        ],
    }


def initialize_default_queue():
    global ticket_queue, executed_tickets, agent_trace_logs
    ticket_queue.clear()
    executed_tickets.clear()
    agent_trace_logs.clear()

    # Pre-populate initial test tickets
    t1_text = "My refund hasn't shown up yet, it's been 2 days, please check the payment."
    auto_o1, auto_c1 = auto_detect_order_customer(t1_text)
    t1 = {
        "ticket_id": "T-QUEUE-101",
        "text": t1_text,
        "urgency_score": 40,
        "order_id": auto_o1,
        "customer_id": auto_c1,
        "title": "Pending Refund Request",
        "category": "Billing",
        "status": "QUEUED",
        "is_rebid": False
    }

    t2_text = "I cannot log into my account at all! It keeps saying my account is locked."
    auto_o2, auto_c2 = auto_detect_order_customer(t2_text)
    t2 = {
        "ticket_id": "T-QUEUE-102",
        "text": t2_text,
        "urgency_score": 65,
        "order_id": auto_o2,
        "customer_id": auto_c2,
        "title": "Account Locked Login Issue",
        "category": "Technical",
        "status": "QUEUED",
        "is_rebid": False
    }

    # Execute T1 on startup so trace logs & executed history exist immediately
    _execute_single_ticket(t1)
    # T2 remains in pending queue
    ticket_queue.append(t2)

# Populate initial queue on startup
#initialize_default_queue()


@app.get("/queue")
def get_queue():
    """Returns current state of ticket queue, executed tickets, and trace count."""
    return {
        "pending_queue": ticket_queue,
        "executed_tickets": executed_tickets,
        "total_queued": len(ticket_queue),
        "total_executed": len(executed_tickets),
        "total_trace_events": len(agent_trace_logs),
    }


@app.post("/execute_next")
def execute_next():
    """Pops the next ticket from the queue and runs it, returning full updated trace state."""
    if not ticket_queue:
        raise HTTPException(status_code=400, detail="Queue is empty.")
    next_ticket = ticket_queue.pop(0)
    exec_res = _execute_single_ticket(next_ticket)
    return _get_full_trace_payload(exec_res)


@app.post("/execute_queue")
def execute_queue():
    """Runs all tickets currently in the queue until empty and returns full trace payload."""
    results = []
    while ticket_queue:
        t = ticket_queue.pop(0)
        res = _execute_single_ticket(t)
        results.append(res)
    payload = _get_full_trace_payload()
    payload["executed_count"] = len(results)
    payload["results"] = results
    return payload


@app.post("/enqueue_ticket")
def enqueue_ticket(payload: InjectedTicket):
    """
    Enqueues a user-entered ticket into the pending queue without immediate execution.
    """
    ticket_text = (payload.ticket_text or "").strip()
    if not ticket_text:
        raise HTTPException(status_code=422, detail="ticket_text cannot be empty.")

    auto_order, auto_customer = auto_detect_order_customer(ticket_text)
    order_id = payload.order_id or auto_order
    customer_id = payload.customer_id or auto_customer

    ticket_id = f"T-USER-{next(ticket_counter)}"
    ticket = {
        "ticket_id": ticket_id,
        "text": ticket_text,
        "urgency_score": payload.urgency_score,
        "order_id": order_id,
        "customer_id": customer_id,
        "title": payload.title or ticket_id,
        "category": payload.category or "Custom",
        "status": "QUEUED",
        "is_rebid": False,
    }
    ticket_queue.append(ticket)
    return {"status": "enqueued", "ticket": ticket, "queue_length": len(ticket_queue)}


@app.post("/inject_ticket")
def inject_ticket(payload: InjectedTicket):
    """
    Enqueues a user-entered ticket into the queue and executes it immediately,
    handling any re-bids by enqueueing them for subsequent queue processing.
    Uses smart auto-detection for order_id and customer_id when not explicitly provided.
    """
    ticket_text = (payload.ticket_text or "").strip()
    if not ticket_text:
        raise HTTPException(status_code=422, detail="ticket_text cannot be empty.")

    # Smart auto-detect order/customer from ticket text if not explicitly provided
    auto_order, auto_customer = auto_detect_order_customer(ticket_text)
    order_id = payload.order_id or auto_order
    customer_id = payload.customer_id or auto_customer

    ticket_id = f"T-USER-{next(ticket_counter)}"
    ticket = {
        "ticket_id": ticket_id,
        "text": ticket_text,
        "urgency_score": payload.urgency_score,
        "order_id": order_id,
        "customer_id": customer_id,
        "title": payload.title or ticket_id,
        "category": payload.category or "Custom",
        "status": "QUEUED",
        "is_rebid": False,
    }

    # Execute immediately and enqueue any re-bids created
    return _execute_single_ticket(ticket)


@app.post("/inject_and_trace")
def inject_and_trace(payload: InjectedTicket):
    """
    Injects a ticket, executes it, and returns both the execution result
    AND the full updated trace logs + agent state in a single response.
    This eliminates the race condition where the frontend polls /agent_trace
    before the trace data from the just-injected ticket is written.
    """
    exec_result = inject_ticket(payload)

    # Gather current trace state
    agent_balances = {
        agent_id: getattr(agent_obj, "balance", 0.0)
        for agent_id, agent_obj in orchestrator.agents.items()
    }
    all_instance_indexes = {
        agent_id: agent_obj.instance_index.get_indexed_instances()
        for agent_id, agent_obj in orchestrator.agents.items()
        if hasattr(agent_obj, "instance_index")
    }

    return {
        "execution_result": exec_result,
        "trace_logs": agent_trace_logs,
        "agent_balances": agent_balances,
        "instance_indexes": all_instance_indexes,
        "pending_queue": ticket_queue,
        "executed_tickets_summary": [
            {
                "ticket_id": item["ticket"]["ticket_id"],
                "title": item["ticket"].get("title"),
                "ticket_text": item["ticket"].get("text", ""),
                "winner": item["result"].get("lead_agent"),
                "final_statement": item["result"].get("final_statement"),
            }
            for item in executed_tickets
        ],
    }


@app.get("/agent_trace")
def get_agent_trace():
    """
    Returns the step-by-step agent calls, auction bids, P2P negotiations,
    sandbox executions, coverage vetting checklists, penalties, and instance indexes.
    """
    agent_balances = {
        agent_id: getattr(agent_obj, "balance", 0.0)
        for agent_id, agent_obj in orchestrator.agents.items()
    }
    
    all_instance_indexes = {
        agent_id: agent_obj.instance_index.get_indexed_instances()
        for agent_id, agent_obj in orchestrator.agents.items()
        if hasattr(agent_obj, "instance_index")
    }

    return {
        "trace_logs": agent_trace_logs,
        "agent_balances": agent_balances,
        "instance_indexes": all_instance_indexes,
        "pending_queue": ticket_queue,
        "executed_tickets_summary": [
            {
                "ticket_id": item["ticket"]["ticket_id"],
                "title": item["ticket"].get("title"),
                "ticket_text": item["ticket"].get("text", ""),
                "winner": item["result"].get("lead_agent"),
                "final_statement": item["result"].get("final_statement"),
            }
            for item in executed_tickets
        ],
    }


# -----------------------------------------------------------------------------
# TEST TICKETS ENDPOINT
# Pre-built ticket texts that exercise all three agent types and collaboration.
# -----------------------------------------------------------------------------

TEST_TICKETS = [
    {
        "label": "Billing: Pending Refund (billing_agent wins, no collab)",
        "ticket_text": "My refund hasn't shown up yet, it's been 2 days, please check the payment.",
        "expected_winner": "billing_agent",
        "collaboration": False,
        "urgency_score": 40,
    },
    {
        "label": "Technical: Account Locked (technical_agent wins, no collab)",
        "ticket_text": "I cannot log into my account at all! It keeps saying my account is locked. I have tried multiple times but nothing works. Please unlock my account.",
        "expected_winner": "technical_agent",
        "collaboration": False,
        "urgency_score": 60,
    },
    {
        "label": "Retention: Cancel Subscription (retention_agent wins, billing collab)",
        "ticket_text": "I have been a customer for 3 years and I've had so many issues recently. Nobody helps me. I want to cancel my subscription immediately!",
        "expected_winner": "retention_agent",
        "collaboration": True,
        "urgency_score": 85,
    },
    {
        "label": "Multi-Domain: Refund + Dashboard (billing_agent wins, technical collab)",
        "ticket_text": "I had an item marked for return and refund however it's no longer visible in my orders section in my profile dashboard. I want my money transferred back to me immediately. I am losing my patience, this issue hasn't been addressed since 2 days.",
        "expected_winner": "billing_agent",
        "collaboration": True,
        "urgency_score": 72,
    },
    {
        "label": "Billing: Duplicate Charge (billing_agent wins, no collab)",
        "ticket_text": "I was charged twice for the same order. Please refund the duplicate charge immediately.",
        "expected_winner": "billing_agent",
        "collaboration": False,
        "urgency_score": 65,
    },
    {
        "label": "Billing: Missing Invoice (billing_agent wins, no collab)",
        "ticket_text": "My invoice was never generated for my order. I need a receipt for my records and tax purposes.",
        "expected_winner": "billing_agent",
        "collaboration": False,
        "urgency_score": 35,
    },
]


@app.get("/test_tickets")
def get_test_tickets():
    """Returns pre-built test ticket texts the user can copy-paste to exercise all agent types."""
    return {"test_tickets": TEST_TICKETS}