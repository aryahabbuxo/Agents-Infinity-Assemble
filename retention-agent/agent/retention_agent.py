import json
import requests

from agent.prompts import RETENTION_SYSTEM_PROMPT
from agent.interface import RetentionAgentInterface
from agent.emotion import analyze_emotion
from agent.bidding import estimate_raw_confidence, compute_final_bid

from agent.tool_dispatcher import ToolDispatcher
from sandbox.state import RetentionSandbox
from sandbox.tools import RetentionTools

class RemoteBillingAgent:

    agent_id = "billing_agent"

    def __init__(
        self,
        url="http://127.0.0.1:8000/negotiate",
        timeout=10,
    ):
        self.url = url
        self.collaborate_url = url.rsplit("/negotiate", 1)[0] + "/collaborate"
        self.timeout = timeout

    def respond_to_proposal(self, proposal):

        try:
            response = requests.post(
                self.url,
                json=proposal,
                timeout=self.timeout,
            )

            response.raise_for_status()

            data = response.json()

            if data.get("action") not in {
                "PROPOSE",
                "COUNTER",
                "ACCEPT",
                "REJECT",
            }:
                raise ValueError(
                    f"Invalid negotiation action: {data.get('action')}"
                )

            return data

        except (requests.RequestException, ValueError) as exc:

            return {
                "sender": self.agent_id,
                "action": "REJECT",
                "rationale": f"Billing communication failed: {exc}",
            }

class RetentionAgent:

    def __init__(
        self,
        model="llama3.1",
        current_load=0,
        balance=0.0,
        sandbox=None
    ):

        self.agent_id = "retention_agent"

        self.model = model
        self.url = "http://localhost:11434/api/chat"

        self.current_load = current_load
        self.balance = balance

        # ---------------------------------------------------------
        # Capability
        # ---------------------------------------------------------

        self.interface = RetentionAgentInterface()
        self.capability_card = self.interface.get_capabilities()

        # ---------------------------------------------------------
        # Sandbox + controlled tools
        # ---------------------------------------------------------

        self.sandbox = sandbox or RetentionSandbox()
        self.tools = RetentionTools(self.sandbox)
        self.dispatcher = ToolDispatcher(self.tools)

        # ---------------------------------------------------------
        # Conversation state
        # ---------------------------------------------------------

        self.messages = [
            {
                "role": "system",
                "content": RETENTION_SYSTEM_PROMPT
            }
        ]

    # =========================================================
    # CAPABILITY
    # =========================================================

    def get_capabilities(self):

        return self.capability_card

    # =========================================================
    # EMOTION
    # =========================================================

    def analyze_emotion(self, ticket_text):

        return analyze_emotion(
            ticket_text=ticket_text
        )

    # =========================================================
    # BIDDING
    # =========================================================

    def submit_bid(self, ticket):

        ticket_id = ticket["ticket_id"]
        ticket_text = ticket["text"]

        # Emotion affects Retention's confidence.
        # It does NOT generate urgency.
        emotion = self.analyze_emotion(ticket_text)

        raw_confidence = estimate_raw_confidence(
            ticket_text=ticket_text,
            emotion_analysis=emotion
        )

        # Urgency is supplied by the market/system.
        urgency_score = ticket.get(
            "urgency_score",
            0
        )

        bid_breakdown = compute_final_bid(
            raw_confidence=raw_confidence,
            current_load=self.current_load,
            urgency_score=urgency_score
        )

        return {
            "agent_id": self.agent_id,
            "ticket_id": ticket_id,
            **bid_breakdown,
            "emotion_analysis": emotion
        }

    # =========================================================
    # INVESTIGATION
    # =========================================================

    def investigate(self, customer_id):

        profile = self.dispatcher.execute(
            "get_customer_profile",
            customer_id
        )

        cancellation = self.dispatcher.execute(
            "check_cancellation_status",
            customer_id
        )

        offer = self.dispatcher.execute(
            "check_retention_offer",
            customer_id
        )

        return {
            "customer_profile": profile,
            "cancellation_status": cancellation,
            "retention_offer": offer
        }

    # =========================================================
    # DIAGNOSIS
    # =========================================================

    def diagnose(
        self,
        ticket_text,
        investigation,
        emotion_analysis
    ):

        profile_result = investigation.get(
            "customer_profile",
            {}
        )

        profile = profile_result.get(
            "profile",
            {}
        )

        cancellation = investigation.get(
            "cancellation_status",
            {}
        )

        offer = investigation.get(
            "retention_offer",
            {}
        )

        return {
            "customer_state": {
                "subscription": profile.get("subscription"),
                "subscription_status": profile.get(
                    "subscription_status"
                ),
                "months_as_customer": profile.get(
                    "months_as_customer"
                ),
                "complaints_last_30_days": profile.get(
                    "complaints_last_30_days"
                ),
                "satisfaction_score": profile.get(
                    "satisfaction_score"
                ),
                "loyalty_points": profile.get(
                    "loyalty_points"
                )
            },

            "emotional_state": emotion_analysis,

            "cancellation": {
                "requested": cancellation.get(
                    "cancellation_requested",
                    False
                ),
                "subscription_status": cancellation.get(
                    "subscription_status"
                )
            },

            "retention_offer": {
                "available": offer.get(
                    "offer_available",
                    False
                )
            },

            "retention_assessment": {
                "churn_risk": emotion_analysis.get(
                    "churn_risk",
                    0
                ),
                "frustration": emotion_analysis.get(
                    "frustration_level",
                    0
                ),
                "helplessness": emotion_analysis.get(
                    "helplessness_level",
                    0
                ),
                "explicit_cancellation": emotion_analysis.get(
                    "explicit_cancellation_request",
                    False
                )
            }
        }

    # =========================================================
    # EXECUTION
    # =========================================================

    def execute(
        self,
        customer_id,
        plan
    ):

        actions = plan.get(
            "actions",
            []
        )

        execution_results = []

        for action in actions:

            # -------------------------------------------------
            # Retention offer
            # -------------------------------------------------

            if action == "apply_retention_offer":

                # Check the latest sandbox state before mutation.
                offer_check = self.dispatcher.execute(
                    "check_retention_offer",
                    customer_id
                )

                if (
                    offer_check.get("success") is not True
                    or offer_check.get("offer_available") is not True
                ):

                    execution_results.append({
                        "action": action,
                        "result": {
                            "success": False,
                            "error": (
                                "Retention offer cannot be applied "
                                "because no offer is currently available."
                            )
                        }
                    })

                    continue

                result = self.dispatcher.execute(
                    "apply_retention_offer",
                    customer_id
                )

            # -------------------------------------------------
            # Cancellation
            # -------------------------------------------------

            elif action == "cancel_subscription":

                # Verify explicit cancellation before mutation.
                cancellation_check = self.dispatcher.execute(
                    "check_cancellation_status",
                    customer_id
                )

                if (
                    cancellation_check.get("success") is not True
                    or cancellation_check.get(
                        "cancellation_requested"
                    ) is not True
                ):

                    execution_results.append({
                        "action": action,
                        "result": {
                            "success": False,
                            "error": (
                                "Cancellation blocked because the "
                                "customer has not explicitly requested "
                                "cancellation."
                            )
                        }
                    })

                    continue

                result = self.dispatcher.execute(
                    "cancel_subscription",
                    customer_id
                )

            # -------------------------------------------------
            # Unknown action
            # -------------------------------------------------

            else:

                result = {
                    "success": False,
                    "error": (
                        f"Unknown retention action: {action}"
                    )
                }

            execution_results.append({
                "action": action,
                "result": result
            })

        return execution_results

    # =========================================================
    # VERIFICATION
    # =========================================================

    def verify_execution(
        self,
        customer_id,
        execution_results
    ):

        successful_actions = [
            item["action"]
            for item in execution_results
            if item.get("result", {}).get("success") is True
        ]

        if not successful_actions:
            return {
                "verified": False,
                "reason": "No state-changing action succeeded."
            }

        # Always inspect the resulting sandbox state after
        # a successful state-changing action.
        profile_result = self.dispatcher.execute(
            "get_customer_profile",
            customer_id
        )

        return {
            "verified": profile_result.get("success") is True,
            "customer_profile": profile_result,
            "successful_actions": successful_actions
        }

    # =========================================================
    # FINAL STATEMENT
    # =========================================================

    def produce_final_statement(
        self,
        diagnosis,
        execution_results,
        verification
    ):

        successful_actions = [
            item["action"]
            for item in execution_results
            if item.get("result", {}).get("success") is True
        ]

        # -----------------------------------------------------
        # Successful cancellation
        # -----------------------------------------------------

        if "cancel_subscription" in successful_actions:

            return (
                "Your subscription has been cancelled successfully."
            )

        # -----------------------------------------------------
        # Successful retention offer
        # -----------------------------------------------------

        if "apply_retention_offer" in successful_actions:

            return (
                "A retention offer has been successfully applied "
                "to your subscription."
            )

        # -----------------------------------------------------
        # Already cancelled
        # -----------------------------------------------------

        cancellation = diagnosis.get(
            "cancellation",
            {}
        )

        if cancellation.get(
            "subscription_status"
        ) == "cancelled":

            return (
                "The customer's subscription is already cancelled."
            )

        # -----------------------------------------------------
        # Explicit cancellation requested but not executed
        # -----------------------------------------------------

        if cancellation.get(
            "requested"
        ) is True:

            return (
                "The customer has explicitly requested cancellation, "
                "but no cancellation state change was performed."
            )

        # -----------------------------------------------------
        # No action
        # -----------------------------------------------------

        offer = diagnosis.get(
            "retention_offer",
            {}
        )

        if offer.get("available") is False:

            return (
                "No subscription changes were made. "
                "No retention offer is currently available."
            )

        return (
            "No retention action was successfully performed."
        )

    # =========================================================
    # NEGOTIATION
    # =========================================================

    def needs_billing_collaboration(self, ticket_text):
        """
        Determine whether the ticket contains a billing-related issue
        that requires Billing Agent expertise.
        """
        billing_keywords = [
            "charged",
            "charge",
            "billing",
            "bill",
            "payment",
            "paid",
            "invoice",
            "refund",
            "refunded",
            "transaction",
            "payment failed",
            "wrong amount",
            "incorrect amount",
            "overcharged",
            "subscription fee",
            "price",
            "cost",
            "money",
        ]

        text = ticket_text.lower()

        return any(keyword in text for keyword in billing_keywords)

    def negotiate_collaboration(
        self,
        counterpart_agent=None,
        proposal=None,
    ):
        """Run real Billing <-> Retention negotiation over HTTP."""
        counterpart_agent = counterpart_agent or RemoteBillingAgent()

        if proposal is None:
            proposal = {
                "sender": self.agent_id,
                "receiver": "billing_agent",
                "action": "PROPOSE",
                "my_assigned_subtask": (
                    "Assess the customer's dissatisfaction, churn risk, "
                    "and cancellation/retention needs."
                ),
                "your_requested_subtask": (
                    "Investigate and resolve the billing-related portion "
                    "of the customer's issue."
                ),
                "rationale": "The ticket contains a billing-related issue that also affects retention.",
            }

        transcript = [proposal]
        current = proposal

        # Maximum 3 negotiation turns, as required by the project protocol.
        for _ in range(3):
            response = counterpart_agent.respond_to_proposal(current)
            transcript.append(response)

            action = response.get("action")
            if action in {"ACCEPT", "REJECT"}:
                break

            if action != "COUNTER":
                transcript.append({
                    "sender": self.agent_id,
                    "action": "REJECT",
                    "rationale": "Invalid negotiation response.",
                })
                break

            current = response

        return transcript

    def respond_to_proposal(self, proposal):
        """Respond to a Billing proposal received over HTTP."""
        if proposal.get("receiver") != self.agent_id:
            return {
                "sender": self.agent_id,
                "action": "REJECT",
                "rationale": "This proposal is not addressed to Retention Agent.",
            }

        if proposal.get("action") != "PROPOSE":
            return {
                "sender": self.agent_id,
                "action": "REJECT",
                "rationale": "Retention expects a PROPOSE message to start negotiation.",
            }

        requested = proposal.get("your_requested_subtask")
        if not requested:
            return {
                "sender": self.agent_id,
                "action": "REJECT",
                "rationale": "No Retention subtask was requested.",
            }

        return {
            "sender": self.agent_id,
            "action": "ACCEPT",
        }
    def execute_collaboration(
        self,
        ticket,
        diagnosis,
        counterpart_agent=None,
    ):
        """Negotiate with Billing and, after ACCEPT, call Billing /collaborate."""

        counterpart = counterpart_agent or RemoteBillingAgent()

        proposal = {
            "sender": self.agent_id,
            "receiver": "billing_agent",
            "action": "PROPOSE",
            "my_assigned_subtask": (
                "Assess the customer's dissatisfaction, churn risk, "
                "and cancellation/retention needs."
            ),
            "your_requested_subtask": (
                "Investigate and resolve the billing-related portion "
                "of the customer's issue."
            ),
            "rationale": diagnosis.get(
                "diagnosis",
                "The ticket needs Billing expertise."
            ),
        }

        transcript = self.negotiate_collaboration(
            counterpart_agent=counterpart,
            proposal=proposal,
        )

        # If negotiation failed or Billing did not ACCEPT,
        # do not attempt collaboration.
        if not transcript or transcript[-1].get("action") != "ACCEPT":
            return {
                "negotiation_transcript": transcript,
                "collaboration_result": None,
            }

        subtask = transcript[0].get(
            "your_requested_subtask",
            ""
        )

        # Billing requires an order_id to investigate the billing issue.
        order_id = ticket.get("order_id")

        if not order_id:
            return {
                "negotiation_transcript": transcript,
                "collaboration_result": {
                    "success": False,
                    "error": (
                        "Billing collaboration requires an order_id, "
                        "but none was provided in the ticket."
                    ),
                },
            }

        try:
            response = requests.post(
                counterpart.collaborate_url,
                json={
                    "ticket": ticket,
                    "order_id": order_id,
                    "subtask": subtask,
                },
                timeout=30,
            )

            response.raise_for_status()
            result = response.json()

        except requests.RequestException as exc:
            result = {
                "success": False,
                "error": f"Billing collaboration failed: {exc}",
            }

        return {
            "negotiation_transcript": transcript,
            "collaboration_result": result,
        }
    # =========================================================
    # FULL TICKET PIPELINE
    # =========================================================

    def handle_ticket(
        self,
        ticket,
        customer_id,
        counterpart_agent=None
    ):

        ticket_id = ticket["ticket_id"]
        ticket_text = ticket["text"]

        # =====================================================
        # 1. EMOTION
        # =====================================================

        emotion_analysis = self.analyze_emotion(
            ticket_text
        )

        # =====================================================
        # 2. INVESTIGATION
        # =====================================================

        investigation = self.investigate(
            customer_id
        )

        # =====================================================
        # 3. DIAGNOSIS
        # =====================================================

        diagnosis = self.diagnose(
            ticket_text=ticket_text,
            investigation=investigation,
            emotion_analysis=emotion_analysis
        )

        # =====================================================
        # 4. LLM DECISION
        # =====================================================

        planning_prompt = f"""
You are the Retention Agent in an autonomous customer-support
system.

Your job is to determine whether a valid retention-related
sandbox action should be performed.

CUSTOMER TICKET:
{ticket_text}

CUSTOMER ID:
{customer_id}

EMOTIONAL ASSESSMENT:
{json.dumps(emotion_analysis, indent=2)}

INVESTIGATION:
{json.dumps(investigation, indent=2)}

DIAGNOSIS:
{json.dumps(diagnosis, indent=2)}

AVAILABLE ACTIONS:

1. apply_retention_offer
2. cancel_subscription

DECISION RULES:

- Customer emotion MUST be considered when evaluating dissatisfaction,
  churn risk, and retention opportunity.
- Emotion does not override sandbox state.
- Emotion does not itself authorize cancellation.
- "I am thinking about cancelling" is NOT an explicit cancellation.
- "I want to cancel" or "Please cancel my subscription" IS explicit.
- Cancellation requires cancellation_requested=true in the sandbox.
- If cancellation is explicitly requested, cancellation takes
  precedence over a retention offer.
- A retention offer can only be applied when
  retention_offer_available=true.
- Never invent an offer.
- Never invent an action.
- Never claim an action happened before execution.
- If no valid action is appropriate, return an empty actions list.

Return JSON ONLY:

{{
    "actions": []
}}

or:

{{
    "actions": [
        "apply_retention_offer"
    ]
}}

or:

{{
    "actions": [
        "cancel_subscription"
    ]
}}
"""

        plan_response = self.ask_llm(
            planning_prompt
        )

        try:

            plan = self._parse_json(
                plan_response
            )

        except ValueError:

            plan = {
                "actions": []
            }

        # =====================================================
        # 5. EXECUTION
        # =====================================================

        execution_results = self.execute(
            customer_id=customer_id,
            plan=plan
        )

        # =====================================================
        # 6. VERIFICATION
        # =====================================================

        verification = self.verify_execution(
            customer_id=customer_id,
            execution_results=execution_results
        )

        # =====================================================
        # 7. NEGOTIATION / COLLABORATION
        # =====================================================

        negotiation_transcript = []
        collaboration_result = None

        # =====================================================
        # 7. NEGOTIATION / COLLABORATION
        # =====================================================

        if counterpart_agent is None and self.needs_billing_collaboration(ticket_text):
            counterpart_agent = RemoteBillingAgent()

        if counterpart_agent is not None:
            negotiation_result = self.execute_collaboration(
                ticket=ticket,
                diagnosis=diagnosis,
                counterpart_agent=counterpart_agent,
            )

            negotiation_transcript = negotiation_result.get(
                "negotiation_transcript", []
            )

            collaboration_result = negotiation_result.get(
                "collaboration_result"
            )
            negotiation_transcript = negotiation_result.get(
                "negotiation_transcript", []
            )
            collaboration_result = negotiation_result.get(
                "collaboration_result"
            )

        # =====================================================
        # 8. FINAL STATEMENT
        # =====================================================

        final_statement = self.produce_final_statement(
            diagnosis=diagnosis,
            execution_results=execution_results,
            verification=verification
        )

        # =====================================================
        # 9. FINAL RESULT
        # =====================================================

        state_before_after = []

        for item in execution_results:

            result = item.get("result", {})

            evidence = result.get(
                "state_before_after"
            )

            if evidence:
                state_before_after.append(
                    evidence
                )

        return {
            "ticket_id": ticket_id,
            "customer_id": customer_id,

            "emotion_analysis": emotion_analysis,

            "investigation": investigation,

            "diagnosis": diagnosis,

            "execution_results": execution_results,

            "verification": verification,

            "negotiation_transcript": negotiation_transcript,

            "collaboration_result": collaboration_result,

            "state_before_after": state_before_after,

            "final_statement": final_statement
        }
    # =========================================================
    # JSON PARSER
    # =========================================================

    @staticmethod
    def _parse_json(response):

        try:
            return json.loads(response)

        except json.JSONDecodeError as exc:

            raise ValueError(
                "LLM returned invalid JSON."
            ) from exc

    # =========================================================
    # LLM
    # =========================================================

    def ask_llm(self, user_message):

        self.messages.append(
            {
                "role": "user",
                "content": user_message
            }
        )

        response = requests.post(
            self.url,
            json={
                "model": self.model,
                "messages": self.messages,
                "stream": False
            },
            timeout=120
        )

        response.raise_for_status()

        data = response.json()

        assistant_message = data["message"]["content"]

        self.messages.append(
            {
                "role": "assistant",
                "content": assistant_message
            }
        )

        return assistant_message

    # =========================================================
    # LOAD MANAGEMENT
    # =========================================================

    def set_load(self, load):

        self.current_load = load

        return {
            "agent_id": self.agent_id,
            "current_load": self.current_load
        }

    def handle_collaboration(
        self,
        ticket,
        customer_id,
        subtask,
    ):
        """Execute only Retention's agreed portion of a joint ticket."""
        emotion = self.analyze_emotion(ticket["text"])
        investigation = self.investigate(customer_id)

        diagnosis = self.diagnose(
            ticket_text=ticket["text"],
            investigation=investigation,
            emotion_analysis=emotion,
        )

        # Reuse the same safe planning/execution rules as the lead pipeline.
        planning_prompt = f"""
You are the Retention Agent acting as a collaborator.

Execute only the Retention portion of this agreed subtask:
{subtask}

CUSTOMER TICKET:
{ticket["text"]}

EMOTIONAL ASSESSMENT:
{json.dumps(emotion, indent=2)}

INVESTIGATION:
{json.dumps(investigation, indent=2)}

Only choose these Retention actions:
- apply_retention_offer
- cancel_subscription

Rules:
- Emotion informs dissatisfaction and churn assessment.
- Emotion does not authorize cancellation.
- Cancellation requires cancellation_requested=true.
- A retention offer requires retention_offer_available=true.
- Never invent an action or state change.
- Return JSON only.

{{"actions": []}}
"""

        try:
            plan = self._parse_json(self.ask_llm(planning_prompt))
        except ValueError:
            plan = {"actions": []}

        execution_results = self.execute(
            customer_id=customer_id,
            plan=plan,
        )

        verification = self.verify_execution(
            customer_id=customer_id,
            execution_results=execution_results,
        )

        return {
            "agent_id": self.agent_id,
            "role": "collaborator",
            "subtask": subtask,
            "emotion_analysis": emotion,
            "investigation": investigation,
            "diagnosis": diagnosis,
            "execution_results": execution_results,
            "verification": verification,
        }
