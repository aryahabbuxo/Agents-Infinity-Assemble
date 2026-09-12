"""
orchestrator.py

Autonomous Multi-Agent Customer Support Market Runner.
Demonstrates:
  1. Capability Sharing (Section 9)
  2. Simultaneous Ticket Broadcast & Bidding (Section 6 & 8)
  3. Lead Agent Selection (Section 6)
  4. Structured P2P Speech Act Negotiation (Section 10)
  5. Multi-Agent Sandbox Execution & State Changes (Section 12 & 14)
  6. Real-time Action & Inter-Agent Communication Logging
"""

import json
import sys
import importlib.util
from pathlib import Path

ROOT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT_DIR))

from billing.agent import BillingAgent
from billing.sandbox import BillingSandbox

from tech.agent import TechnicalAgent
from tech.sandbox import TechnicalSandbox
from tech.environment import EcommerceEnvironment

retention_dir = ROOT_DIR / "retention-agent"
if str(retention_dir) not in sys.path:
    sys.path.insert(0, str(retention_dir))

retention_spec = importlib.util.spec_from_file_location(
    "retention_agent_mod",
    str(retention_dir / "agent" / "retention_agent.py")
)
retention_mod = importlib.util.module_from_spec(retention_spec)
sys.modules["retention_agent_mod"] = retention_mod
retention_spec.loader.exec_module(retention_mod)
RetentionAgent = retention_mod.RetentionAgent

from sandbox.state import RetentionSandbox


from shared_data import TICKETS, shared_state_log  # noqa: E402


def print_banner(title: str, symbol: str = "="):
    width = 75
    print("\n" + symbol * width)
    print(f" {title.center(width - 2)} ")
    print(symbol * width)


def print_section(title: str):
    print(f"\n--- {title} ---")


class MarketOrchestrator:
    def __init__(self):
        # 1. Initialize sandboxes for all three domains
        self.billing_sandbox = BillingSandbox()
        self.tech_env = EcommerceEnvironment()
        self.tech_sandbox = TechnicalSandbox(self.tech_env)
        self.retention_sandbox = RetentionSandbox()

        # 2. Initialize the three autonomous agents
        self.billing_agent = BillingAgent(sandbox=self.billing_sandbox, current_load=0)
        self.tech_agent = TechnicalAgent(sandbox=self.tech_sandbox)
        self.retention_agent = RetentionAgent(sandbox=self.retention_sandbox, current_load=0)

        self.agents = {
            "billing_agent": self.billing_agent,
            "technical_agent": self.tech_agent,
            "retention_agent": self.retention_agent,
        }

    def display_capabilities(self):
        print_banner("1. AGENT CAPABILITY BROADCAST (BEFORE TICKETS)")
        for agent_id, agent in self.agents.items():
            if hasattr(agent, "capability_card"):
                card = agent.capability_card
            elif hasattr(agent, "get_capabilities"):
                card = agent.get_capabilities()
            else:
                card = {}
            
            print(f"\n[{card.get('display_name', agent_id).upper()}] (ID: {agent_id})")
            print(f"  Handles        : {', '.join(card.get('handles', []))}")
            print(f"  Does Not Handle: {', '.join(card.get('does_not_handle', []))}")
            print(f"  Best Suited For: {card.get('best_suited_for', '')}")

    def run_ticket(self, ticket: dict, order_id: str = None, customer_id: str = None):
        order_id = order_id or ticket.get("order_id", "O-1001")
        customer_id = customer_id or ticket.get("customer_id", "C001")

        # Set active ticket context for sandboxes
        self.billing_sandbox.current_ticket_id = ticket["ticket_id"]
        self.tech_sandbox.current_ticket_id = ticket["ticket_id"]
        self.retention_sandbox.current_ticket_id = ticket["ticket_id"]

        # Reset technical environment to current ticket's customer context
        self.tech_env.set_customer(customer_id)

        print_banner(f"TICKET {ticket['ticket_id']}: {ticket['text'][:60]}...")
        print(f"Ticket ID     : {ticket['ticket_id']}")
        print(f"Urgency Score : {ticket.get('urgency_score', 0)}")
        print(f"Full Wording  : \"{ticket['text']}\"")

        # -----------------------------------------------------
        # STEP 1: Broadcast & Bidding Phase
        # -----------------------------------------------------
        print_section("STAGE 1: BROADCAST & BIDDING MARKET")
        bids = []

        # Billing Agent Bid
        b_bid = self.billing_agent.submit_bid(ticket)
        bids.append(b_bid)

        # Technical Agent Bid
        from tech.bidding import submit_bid as tech_submit_bid
        t_bid = tech_submit_bid(ticket["text"], current_load=0, urgency_score=ticket.get("urgency_score", 0), ticket_id=ticket["ticket_id"])
        bids.append(t_bid)

        # Retention Agent Bid
        r_bid = self.retention_agent.submit_bid(ticket)
        bids.append(r_bid)

        # Display Bids Comparison Table
        print("\n  {:^18} | {:^14} | {:^12} | {:^14} | {:^10}".format(
            "Agent", "Raw Confidence", "Load Penalty", "Urgency Weight", "Final Bid"
        ))
        print("  " + "-" * 75)
        for b in bids:
            print("  {:18} | {:^14.3f} | {:^12.3f} | {:^14.3f} | {:^10.3f}".format(
                b["agent_id"],
                b["raw_confidence"],
                b["load_penalty"],
                b["urgency_weight"],
                b["final_bid"],
            ))

        # Determine Winner
        winning_bid = max(bids, key=lambda x: x["final_bid"])
        lead_agent_id = winning_bid["agent_id"]
        print(f"\n WINNER: [{lead_agent_id}] with highest bid score {winning_bid['final_bid']:.3f}!")

        # -----------------------------------------------------
        # STEP 2: Lead Agent Ticket Handling & Diagnosis
        # -----------------------------------------------------
        print_section("STAGE 2: LEAD AGENT INVESTIGATION & DIAGNOSIS")
        lead_agent = self.agents[lead_agent_id]

        if lead_agent_id == "billing_agent":
            result = lead_agent.handle_ticket(
                ticket=ticket,
                order_id=order_id,
                counterpart_agent=self.tech_agent
            )
        elif lead_agent_id == "retention_agent":
            result = lead_agent.handle_ticket(
                ticket=ticket,
                customer_id=customer_id,
                counterpart_agent=self.billing_agent
            )
        else:
            # Technical Agent Lead
            fault_result = generate_fault_state(self.tech_env, ticket["text"])
            result = lead_agent.solve(ticket)
            result["ticket_id"] = ticket["ticket_id"]
            result["lead_agent"] = lead_agent_id

        # -----------------------------------------------------
        # STEP 3: Display Inter-Agent Negotiation Transcript
        # -----------------------------------------------------
        print_section("STAGE 3: P2P STRUCTURED NEGOTIATION TRANSCRIPT")
        transcript = result.get("negotiation_transcript")
        if transcript:
            for turn, msg in enumerate(transcript, 1):
                action = msg.get("action") or msg.get("message_type")
                sender = msg.get("sender")
                receiver = msg.get("receiver", "all")
                print(f"  Round {turn}: [{sender}] -> [{receiver}] : Action = {action}")
                if "my_assigned_subtask" in msg or "my_subtask" in msg:
                    subtask = msg.get("my_assigned_subtask") or msg.get("my_subtask")
                    print(f"           My Assigned Subtask  : {subtask}")
                if "your_requested_subtask" in msg or "requested_subtask" in msg:
                    req = msg.get("your_requested_subtask") or msg.get("requested_subtask")
                    print(f"           Requested Subtask    : {req}")
                if "modified_scope" in msg:
                    print(f"           Modified Scope       : {msg.get('modified_scope')}")
                if "rationale" in msg and msg.get("rationale"):
                    print(f"           Rationale            : {msg.get('rationale')}")
        else:
            print("  No multi-agent negotiation was required for this ticket.")

        # -----------------------------------------------------
        # STEP 4: Display Sandbox Actions & State Changes
        # -----------------------------------------------------
        print_section("STAGE 4: SANDBOX EXECUTION & STATE CHANGES")
        
        # Lead agent state changes
        lead_changes = result.get("state_before_after") or []
        if lead_changes:
            print(f"\n  [{lead_agent_id}] Sandbox Changes:")
            for change in lead_changes:
                if isinstance(change, dict) and "action" in change:
                    print(f"    Action: {change['action']}")
                    print(f"      Before: {change.get('before')}")
                    print(f"      After : {change.get('after')}")
                else:
                    print(f"    Change: {change}")
        else:
            actions_taken = result.get("execution_results") or result.get("actions_taken") or []
            print(f"\n  [{lead_agent_id}] Actions Executed: {actions_taken}")

        # Collaborator agent state changes
        collab_res = result.get("collaboration_result")
        if collab_res:
            c_agent = collab_res.get("agent_id", "collaborator_agent")
            print(f"\n  [{c_agent}] Collaborative Execution Result:")
            print(f"    Diagnosis/Statement: {collab_res.get('statement') or collab_res.get('result')}")
            collab_changes = collab_res.get("state_before_after") or []
            for c_change in collab_changes:
                print(f"    Collaborator Action: {c_change}")

        # -----------------------------------------------------
        # STEP 5: Final Conclusive Statement
        # -----------------------------------------------------
        print_section("STAGE 5: FINAL CUSTOMER RESOLUTION STATEMENT")
        statement = result.get("final_statement") or result.get("customer_statement") or "Issue handled."
        print(f"\n  \"{statement}\"\n")
        return result


def generate_fault_state(env, ticket_text: str):
    text = ticket_text.lower()
    if "dashboard" in text or "disappeared" in text or "visible" in text:
        env.state["dashboard"]["status"] = "ERROR"
        env.state["dashboard"]["error_code"] = 500
        for o_id in env.state["orders"]:
            env.state["orders"][o_id]["visible"] = False
            env.state["orders"][o_id]["sync_status"] = "FAILED"
    if "locked" in text or "account" in text:
        env.state["customer"]["account_status"] = "LOCKED"
    return env.get_state()


def main():
    print_banner("AUTONOMOUS MULTI-AGENT MARKET DEMO", "=")
    orchestrator = MarketOrchestrator()
    orchestrator.display_capabilities()

    for t in TICKETS:
        orchestrator.run_ticket(t)

    written = shared_state_log.dump()
    print(f"\n[SharedStateLog] Written {written} state-change event(s) to shared_state_log.json")
    print_banner("ALL TICKETS SOLVED SUCCESSFULLY", "=")


if __name__ == "__main__":
    main()
