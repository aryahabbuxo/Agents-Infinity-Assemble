"""
orchestrator.py

Autonomous Multi-Agent Customer Support Market Runner.
Includes:
  1. Per-Agent Instance Indexing (top-performing at top, low-performing at bottom)
  2. Brier Calibration Gap Penalty Engine (apply_penalty from instance_index.py)
  3. Non-LLM Requirement Coverage Vetting (evaluate_coverage from vetting.py)
  4. Dynamic Re-Bidding Loop (re-bids if coverage_score < 0.7, up to MAX_ITERATIONS = 3)
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

from instance_index import apply_penalty
from vetting import evaluate_coverage
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
        # RE-BIDDING LOOP CONFIGURATION
        # -----------------------------------------------------
        MAX_ITERATIONS = 3
        iteration = 1
        current_ticket_text = ticket["text"]
        accumulated_evidence = []
        last_result = None

        while iteration <= MAX_ITERATIONS:
            if iteration > 1:
                print_banner(f"RE-BIDDING ITERATION {iteration}/{MAX_ITERATIONS} FOR TICKET {ticket['ticket_id']}", "-")
                print(f"Remaining Asks Text: \"{current_ticket_text}\"")

            sub_ticket = dict(ticket)
            sub_ticket["text"] = current_ticket_text

            # -----------------------------------------------------
            # STAGE 1: Broadcast & Bidding Phase (uses per-agent InstanceIndex)
            # -----------------------------------------------------
            print_section(f"STAGE 1: BROADCAST & BIDDING MARKET (ITERATION {iteration})")
            bids = []

            # Billing Agent Bid
            b_bid = self.billing_agent.submit_bid(sub_ticket)
            bids.append(b_bid)

            # Technical Agent Bid
            t_bid = self.tech_agent.submit_bid(sub_ticket)
            bids.append(t_bid)

            # Retention Agent Bid
            r_bid = self.retention_agent.submit_bid(sub_ticket)
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
            lead_agent = self.agents[lead_agent_id]
            print(f"\n WINNER (Iteration {iteration}): [{lead_agent_id}] with bid score {winning_bid['final_bid']:.3f}!")

            # -----------------------------------------------------
            # STAGE 2: Lead Agent Ticket Handling & Diagnosis
            # -----------------------------------------------------
            print_section(f"STAGE 2: LEAD AGENT INVESTIGATION & DIAGNOSIS (ITERATION {iteration})")

            if lead_agent_id == "billing_agent":
                result = lead_agent.handle_ticket(
                    ticket=sub_ticket,
                    order_id=order_id,
                    counterpart_agent=self.tech_agent
                )
            elif lead_agent_id == "retention_agent":
                result = lead_agent.handle_ticket(
                    ticket=sub_ticket,
                    customer_id=customer_id,
                    counterpart_agent=self.billing_agent
                )
            else:
                # Technical Agent Lead
                fault_result = generate_fault_state(self.tech_env, sub_ticket["text"])
                result = lead_agent.solve(sub_ticket)
                result["ticket_id"] = sub_ticket["ticket_id"]
                result["lead_agent"] = lead_agent_id

            last_result = result
            accumulated_evidence.append(result)

            # -----------------------------------------------------
            # STAGE 3: Display Inter-Agent Negotiation Transcript
            # -----------------------------------------------------
            print_section(f"STAGE 3: P2P STRUCTURED NEGOTIATION TRANSCRIPT (ITERATION {iteration})")
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
                print("  No multi-agent negotiation was required for this iteration.")

            # -----------------------------------------------------
            # STAGE 4: Display Sandbox Actions & State Changes
            # -----------------------------------------------------
            print_section(f"STAGE 4: SANDBOX EXECUTION & STATE CHANGES (ITERATION {iteration})")
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

            collab_res = result.get("collaboration_result")
            if collab_res:
                c_agent = collab_res.get("agent_id", "collaborator_agent")
                print(f"\n  [{c_agent}] Collaborative Execution Result:")
                print(f"    Diagnosis/Statement: {collab_res.get('statement') or collab_res.get('result')}")

            # -----------------------------------------------------
            # STAGE 5: Requirement Coverage Vetting (vetting.py)
            # -----------------------------------------------------
            print_section(f"STAGE 5: REQUIREMENT COVERAGE VETTING & CHECKLIST (ITERATION {iteration})")
            
            # Combine evidence trail across all iterations for this ticket
            vetting_res = evaluate_coverage(ticket["text"], accumulated_evidence)
            cov_score = vetting_res["coverage_score"]

            print(f"  Coverage Score         : {cov_score:.4f} ({vetting_res['addressed_requirements']}/{vetting_res['total_requirements']} asks addressed)")
            print("  Clause Checklist       :")
            for item in vetting_res["clause_checklist"]:
                status_symbol = "[YES]" if item["addressed"] else "[ NO]"
                kw_info = f" (matched: {', '.join(item['matched_keywords'])})" if item["matched_keywords"] else ""
                print(f"    {status_symbol} Ask: \"{item['clause']}\"{kw_info}")

            # -----------------------------------------------------
            # STAGE 6: Calibration Penalty & Instance Indexing
            # -----------------------------------------------------
            print_section(f"STAGE 6: CALIBRATION PENALTY & INSTANCE INDEXING (ITERATION {iteration})")

            # Call isolated apply_penalty function in instance_index.py
            penalty_info = apply_penalty(
                raw_confidence=winning_bid["raw_confidence"],
                coverage_score=cov_score,
                agent=lead_agent
            )

            print(f"  Lead Agent ID          : {lead_agent_id}")
            print(f"  Claimed Raw Confidence : {winning_bid['raw_confidence']:.4f}")
            print(f"  Actual Coverage Score  : {cov_score:.4f}")
            print(f"  Calibration Gap        : {penalty_info['calibration_gap']:.4f}")
            if penalty_info["penalty"] > 0:
                print(f"  Overconfidence Penalty : -${penalty_info['penalty']:.2f}")
            else:
                print(f"  Calibration Penalty    : $0.00 (Accurate/Humble Bidding)")
            print(f"  Updated Agent Balance  : ${penalty_info['new_balance']:.2f}")

            # Record instance into Lead Agent's unique InstanceIndex
            lead_agent.instance_index.add_instance(
                ticket_id=ticket["ticket_id"],
                text=current_ticket_text,
                raw_confidence=winning_bid["raw_confidence"],
                coverage_score=cov_score
            )

            # Also record into Collaborator's instance index if collaborator participated
            if collab_res and "agent_id" in collab_res:
                c_agent_obj = self.agents.get(collab_res["agent_id"])
                if c_agent_obj and hasattr(c_agent_obj, "instance_index"):
                    c_agent_obj.instance_index.add_instance(
                        ticket_id=ticket["ticket_id"],
                        text=current_ticket_text,
                        raw_confidence=cov_score,
                        coverage_score=cov_score
                    )

            # Display Agent's Top & Bottom Indexed Instances
            indexed_insts = lead_agent.instance_index.get_indexed_instances()
            print(f"\n  [{lead_agent_id}] Unique Instance Index (Sorted Top-Performers -> Bottom-Performers):")
            for idx, inst in enumerate(indexed_insts, 1):
                rank_label = "TOP" if idx == 1 else ("BOTTOM" if idx == len(indexed_insts) else f"RANK #{idx}")
                print(f"    [{rank_label}] Ticket {inst['ticket_id']} | Coverage: {inst['coverage_score']} | Gap: {inst['gap']:+.4f} | Success: {inst['success']}")

            # -----------------------------------------------------
            # STAGE 7: Re-Bidding Stopping Decision (coverage_score < 0.7)
            # -----------------------------------------------------
            if cov_score >= 0.7:
                print_banner(f"TICKET {ticket['ticket_id']} PASSED VETTING (Coverage {cov_score:.2f} >= 0.7 threshold)", "*")
                break
            elif iteration < MAX_ITERATIONS and vetting_res["unaddressed_clauses"]:
                current_ticket_text = " ".join(vetting_res["unaddressed_clauses"])
                print(f"\n [RE-BID TRIGGERED] Coverage score {cov_score:.2f} < 0.7 threshold! Preparing re-bid iteration {iteration + 1}...")
                iteration += 1
            else:
                print_banner(f"TICKET {ticket['ticket_id']} STOPPED (Max iterations {MAX_ITERATIONS} reached)", "!")
                break

        statement = (last_result.get("final_statement") or last_result.get("customer_statement") or "Issue handled.") if last_result else "Completed."
        print(f"\nFinal Resolution Statement: \"{statement}\"\n")
        return last_result


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
    print_banner("AUTONOMOUS MULTI-AGENT MARKET DEMO (WITH INDEXING & VETTING RE-BIDDING)", "=")
    orchestrator = MarketOrchestrator()
    orchestrator.display_capabilities()

    for t in TICKETS:
        orchestrator.run_ticket(t)

    written = shared_state_log.dump()
    print(f"\n[SharedStateLog] Written {written} state-change event(s) to shared_state_log.json")

    # Export combined instance indexes for all agents to instance_indexes_all.json
    all_indexes = {
        agent_id: agent_obj.instance_index.get_indexed_instances()
        for agent_id, agent_obj in orchestrator.agents.items()
        if hasattr(agent_obj, "instance_index")
    }
    with open("instance_indexes_all.json", "w", encoding="utf-8") as f:
        json.dump(all_indexes, f, indent=2)
    print(f"[InstanceIndex] Exported per-agent instance indexes to instance_indexes_all.json")
    print_banner("ALL MARKET TICKETS PROCESSED & VETTED SUCCESSFULLY", "=")


if __name__ == "__main__":
    main()
