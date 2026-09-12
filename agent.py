"""
agent.py

The Billing Agent itself. Ties together:
  - bidding.py       -> self-assessment / final_bid
  - sandbox.py        -> investigate + act
  - negotiation.py    -> PROPOSE/COUNTER/ACCEPT/REJECT with other agents
  - capability.py      -> what this agent claims to handle
  - llm_client.py     -> real LLM calls, with rule-based fallback

Public entry point: BillingAgent.handle_ticket(ticket)
"""

import json
import re

from bidding import estimate_raw_confidence, compute_final_bid
from sandbox import BillingSandbox
from negotiation import make_propose, run_negotiation, MockTechnicalAgent
from capability import CAPABILITY_CARD
from llm_client import call_llm, LLMUnavailableError

# The ONLY tool names the LLM is allowed to choose from. Never execute a
# tool name that isn't in this set — this is what stops the model from
# inventing actions the sandbox doesn't actually support.
ALLOWED_ACTIONS = {
    "release_pending_refund",
    "flag_for_manual_review",
    "reissue_invoice",
    "confirm_refund_already_processed",
    "refund_duplicate_charge",
    "complete_partial_refund",
}

DIAGNOSE_PROMPT = """You are a billing specialist agent. Given this investigation of a customer order, diagnose the root cause and choose which tools to run.

RULES:
1. Only include an action that fixes an ACTUAL anomaly present in the investigation below. If a field already looks correct/healthy, do NOT run an action on it.
2. Pick the SMALLEST plan that fixes the real problem. Do not add extra actions just because a tool exists for a related field.
3. needs_collaboration is true ONLY when there is no billing anomaly at all and the issue is clearly outside billing (e.g. refund_status is already PROCESSED and nothing else looks wrong).
4. Never invent a tool name outside the allowed list.
5. If MORE THAN ONE real anomaly is present at once (e.g. duplicate_charge is true AND invoice_status is MISSING), include one action for EACH real anomaly, still following rule 1 (skip healthy fields).
6. If NONE of the known patterns match and nothing in the investigation looks wrong, return an empty plan: {{"diagnosis": "No clear billing anomaly found.", "plan": [], "needs_collaboration": false, "collaboration_target": null}}. Do not force an action just to have one.

WORKED EXAMPLES (follow this exact reasoning pattern):

Example 1 - refund_status is PENDING and days_since_request is high:
{{"diagnosis": "Refund stuck at gateway longer than expected.", "plan": ["release_pending_refund"], "needs_collaboration": false, "collaboration_target": null}}

Example 2 - refund_status is REJECTED with a reject_reason:
{{"diagnosis": "Refund auto-rejected due to <reject_reason>.", "plan": ["flag_for_manual_review"], "needs_collaboration": false, "collaboration_target": null}}

Example 3 - refund_status is PROCESSED and invoice/payment/duplicate all look normal (no real billing anomaly):
{{"diagnosis": "Refund already completed on the billing side; likely a technical/display issue.", "plan": ["confirm_refund_already_processed"], "needs_collaboration": true, "collaboration_target": "technical_agent"}}

Example 4 - duplicate_charge is true:
{{"diagnosis": "Customer was charged twice for the same order.", "plan": ["refund_duplicate_charge"], "needs_collaboration": false, "collaboration_target": null}}

Example 5 - invoice_status is MISSING, everything else normal:
{{"diagnosis": "Invoice was never generated for this order.", "plan": ["reissue_invoice"], "needs_collaboration": false, "collaboration_target": null}}

Example 6 - refund_status is PARTIAL:
{{"diagnosis": "Refund was only partially processed.", "plan": ["complete_partial_refund"], "needs_collaboration": false, "collaboration_target": null}}

Now diagnose this real case:

Investigation:
{investigation_json}

Allowed tool names (choose ONLY from this list):
{allowed_actions}

Respond with ONLY a JSON object, no other text, matching the exact shape shown in the examples above.
"""


class BillingAgent:
    def __init__(self, sandbox: BillingSandbox = None, current_load: int = 0, balance: float = 0.0):
        self.agent_id = "billing_agent"
        self.sandbox = sandbox or BillingSandbox()
        self.current_load = current_load      # external system tracks this, not the LLM
        self.balance = balance                # external system tracks this too
        self.capability_card = CAPABILITY_CARD

    # ---------- STEP 1: self-assessment / bid ----------
    def submit_bid(self, ticket: dict) -> dict:
        raw_confidence = estimate_raw_confidence(ticket["text"])
        bid_breakdown = compute_final_bid(
            raw_confidence=raw_confidence,
            current_load=self.current_load,
            urgency_score=ticket.get("urgency_score", 0),
        )
        return {"agent_id": self.agent_id, "ticket_id": ticket["ticket_id"], **bid_breakdown}

    # ---------- STEP 2: investigate the sandbox (only runs if this agent wins) ----------
    def investigate(self, order_id: str) -> dict:
        try:
            payment = self.sandbox.check_payment_status(order_id)
            refund = self.sandbox.check_refund_status(order_id)
            invoice = self.sandbox.check_invoice(order_id)
            duplicate = self.sandbox.check_duplicate_charge(order_id)
            return {"payment": payment, "refund": refund, "invoice": invoice, "duplicate": duplicate}
        except KeyError:
            # Unknown order_id — don't crash the pipeline, surface it as a
            # diagnosable "problem" the vetting layer / dashboard can see.
            return {"error": f"No billing record found for order_id={order_id}"}

    # ---------- STEP 3: diagnose root cause + decide plan ----------
    def _rule_based_diagnose(self, investigation: dict) -> dict:
        if "error" in investigation:
            return {
                "diagnosis": investigation["error"],
                "plan": [],
                "needs_collaboration": False,
            }

        refund_status = investigation["refund"]["refund_status"]
        days_waiting = investigation["refund"]["days_since_request"]
        invoice_status = investigation["invoice"]["invoice_status"]
        duplicate_charge = investigation["duplicate"]["duplicate_charge"]
        subscription_id = investigation["duplicate"]["subscription_id"]

        if duplicate_charge and subscription_id:
            return {
                "diagnosis": f"Subscription {subscription_id} was billed twice for the same cycle.",
                "plan": ["refund_duplicate_charge"],
                "needs_collaboration": False,
            }
        if duplicate_charge:
            return {
                "diagnosis": "Customer was charged twice for the same order.",
                "plan": ["refund_duplicate_charge"],
                "needs_collaboration": False,
            }
        if invoice_status == "MISSING":
            return {
                "diagnosis": "Invoice was never generated for this order.",
                "plan": ["reissue_invoice"],
                "needs_collaboration": False,
            }
        if refund_status == "PARTIAL":
            return {
                "diagnosis": "Refund was only partially processed.",
                "plan": ["complete_partial_refund"],
                "needs_collaboration": False,
            }
        if refund_status == "PENDING" and days_waiting >= 2:
            return {
                "diagnosis": "Refund stuck at gateway longer than expected.",
                "plan": ["release_pending_refund"],
                "needs_collaboration": False,
            }
        if refund_status == "REJECTED":
            return {
                "diagnosis": f"Refund auto-rejected ({investigation['refund']['reject_reason']}).",
                "plan": ["flag_for_manual_review"],
                "needs_collaboration": False,
                "fully_resolved": False,
            }
        if refund_status == "PROCESSED":
            return {
                "diagnosis": (
                    "Refund already completed on the billing side. The customer's "
                    "complaint about a missing order most likely points to a "
                    "dashboard/technical display issue, not a billing problem."
                ),
                "plan": ["confirm_refund_already_processed"],
                "needs_collaboration": True,
                "collaboration_target": "technical_agent",
            }
        return {
            "diagnosis": "No clear billing anomaly found.",
            "plan": [],
            "needs_collaboration": False,
        }

    def diagnose(self, investigation: dict) -> dict:
        """
        Tries an LLM-driven diagnosis first (given the investigation data,
        picking only from ALLOWED_ACTIONS), falls back to the deterministic
        rule-based diagnosis if the LLM is unavailable or returns something
        invalid (e.g. an invented tool name).
        """
        if "error" in investigation:
            return self._rule_based_diagnose(investigation)  # unknown order_id — skip the LLM entirely

        try:
            prompt = DIAGNOSE_PROMPT.format(
                investigation_json=json.dumps(investigation, indent=2),
                allowed_actions=", ".join(sorted(ALLOWED_ACTIONS)),
            )
            raw = call_llm(prompt)
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if not match:
                raise ValueError(f"No JSON object found in LLM output: {raw!r}")
            parsed = json.loads(match.group(0))

            plan = parsed.get("plan", [])
            if not isinstance(plan, list) or any(step not in ALLOWED_ACTIONS for step in plan):
                raise ValueError(f"LLM proposed an invalid plan: {plan!r}")

            return {
                "diagnosis": parsed.get("diagnosis", "LLM diagnosis (no explanation given)."),
                "plan": plan,
                "needs_collaboration": bool(parsed.get("needs_collaboration", False)),
                "collaboration_target": parsed.get("collaboration_target"),
            }
        except (LLMUnavailableError, ValueError, json.JSONDecodeError):
            return self._rule_based_diagnose(investigation)

    # ---------- STEP 4: execute the plan against the sandbox ----------
    def execute(self, order_id: str, plan: list[str], reject_reason: str = None) -> list[dict]:
        results = []
        for action in plan:
            if action not in ALLOWED_ACTIONS:
                continue  # safety net, should never trigger given diagnose() validation
            if action == "release_pending_refund":
                results.append(self.sandbox.release_pending_refund(order_id))
            elif action == "flag_for_manual_review":
                results.append(self.sandbox.flag_for_manual_review(order_id, reject_reason or "unspecified"))
            elif action == "confirm_refund_already_processed":
                results.append(self.sandbox.confirm_refund_already_processed(order_id))
            elif action == "reissue_invoice":
                results.append(self.sandbox.reissue_invoice(order_id))
            elif action == "refund_duplicate_charge":
                results.append(self.sandbox.refund_duplicate_charge(order_id))
            elif action == "complete_partial_refund":
                results.append(self.sandbox.complete_partial_refund(order_id))
        return results

    # ---------- STEP 5: negotiate with another agent if needed ----------
    def negotiate_collaboration(self, ticket: dict, diagnosis: dict, counterpart_agent=None) -> list[dict]:
        counterpart_agent = counterpart_agent or MockTechnicalAgent()
        proposal = make_propose(
            sender=self.agent_id,
            receiver=diagnosis["collaboration_target"],
            my_subtask="Confirm refund was processed correctly on the billing side.",
            requested_subtask="Investigate why the order/refund is not visible in the customer dashboard.",
            rationale=diagnosis["diagnosis"],
        )
        return run_negotiation(proposal, counterpart_agent)

    # ---------- STEP 6: produce the final conclusive statement (for vetting) ----------
    def produce_final_statement(self, ticket, diagnosis, execution_results, negotiation_transcript=None) -> str:
        parts = [f"Investigated order for ticket {ticket['ticket_id']}. {diagnosis['diagnosis']}"]
        if execution_results:
            parts.append(f"Actions taken: {[r for r in execution_results]}")
        if negotiation_transcript:
            outcome = negotiation_transcript[-1]["action"]
            parts.append(
                f"Requested help from {diagnosis.get('collaboration_target')} "
                f"for the technical portion (negotiation outcome: {outcome})."
            )
        return " ".join(parts)

    # ---------- Orchestration: run the whole billing-side pipeline for one ticket ----------
    def handle_ticket(self, ticket: dict, order_id: str, counterpart_agent=None) -> dict:
        investigation = self.investigate(order_id)
        diagnosis = self.diagnose(investigation)
        execution_results = self.execute(
            order_id,
            diagnosis["plan"],
            reject_reason=investigation.get("refund", {}).get("reject_reason"),
        )

        negotiation_transcript = None
        if diagnosis.get("needs_collaboration"):
            negotiation_transcript = self.negotiate_collaboration(ticket, diagnosis, counterpart_agent)

        final_statement = self.produce_final_statement(
            ticket, diagnosis, execution_results, negotiation_transcript
        )

        return {
            "ticket_id": ticket["ticket_id"],
            "order_id": order_id,
            "investigation": investigation,
            "diagnosis": diagnosis,
            "execution_results": execution_results,
            "negotiation_transcript": negotiation_transcript,
            "final_statement": final_statement,
            "state_before_after": self.sandbox.log[-len(execution_results):] if execution_results else [],
        }