import json
import requests
from instance_index import InstanceIndex

try:
    from tech.bidding import TECHNICAL_CAPABILITY_CARD, submit_bid as tech_submit_bid
    from tech.negotiation import TechnicalNegotiationHandler
except ImportError:
    from bidding import TECHNICAL_CAPABILITY_CARD, submit_bid as tech_submit_bid
    from negotiation import TechnicalNegotiationHandler



OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen2.5:7b"


MAX_STEPS = 10


class TechnicalAgent:

    def __init__(self, sandbox, current_load: int = 0, balance: float = 0.0):

        self.agent_id = "technical_agent"
        self.sandbox = sandbox
        self.current_load = current_load
        self.balance = balance
        self.capability_card = TECHNICAL_CAPABILITY_CARD
        self.instance_index = InstanceIndex(agent_id=self.agent_id)
        self.system_prompt = """
            You are the Technical Support Agent for a fictional e-commerce company.

            ROLE
            Investigate and resolve technical problems involving:
            - account access, authentication, sessions
            - dashboard
            - orders, order visibility, synchronization
            - cart
            - search
            - checkout
            - notifications
            - technical service health

            Do NOT handle:
            - payments, refunds, invoices, billing, subscription charges
            - compensation or retention offers

            CORE PRINCIPLE
            The customer ticket describes the customer's EXPERIENCE, not the
            underlying cause.

            Do not assume the cause from the ticket.
            Use the sandbox to determine what is actually happening.

            INVESTIGATION
            - Start with the most relevant diagnostic tool for the reported symptom.
            - Use the minimum observations needed to form a reasonable hypothesis.
            - Do not inspect unrelated systems or every available tool.
            - Expand the investigation only when evidence suggests another
            subsystem may be involved.
            - Do not perform an action without evidence supporting the repair.

            IDENTIFIERS
            - Never invent, guess, or extrapolate identifiers.
            - For order problems, list_orders provides the ONLY valid order IDs
            unless the customer explicitly provides an order ID.
            - If list_orders returns ORDER1001 and ORDER1002, ORDER1003 does not exist
            unless another sandbox result explicitly provides it.
            - If an identifier is not known, do not call a tool requiring that identifier.
            - If an identifier lookup fails, do not retry the same guessed identifier.

            ACTIONS AND VERIFICATION
            - Perform an ACTION only when sufficient evidence supports the repair.
            - After every successful ACTION, perform a separate OBSERVE using an
            appropriate diagnostic or verification tool.
            - An ACTION result showing success is not itself verification.
            - Verification must confirm that the intended sandbox state is now correct.
            - If an ACTION fails, do not repeat the same ACTION with the same arguments.
            Reassess the evidence and choose another diagnostic step if appropriate.
            - NEVER report "resolved" unless the final verification confirms the
            intended state is correct.
            - If the problem cannot be resolved, FINISH with an appropriate
            non-resolved status and explain why.

            DECISION TYPES
            OBSERVE: gather information.
            ACTION: perform a supported technical repair.
            FINISH: investigation and verification are complete.

            OUTPUT
            Return ONLY valid JSON.

            OBSERVE:
            {
                "type": "OBSERVE",
                "tool": "tool_name",
                "arguments": {}
            }

            ACTION:
            {
                "type": "ACTION",
                "tool": "tool_name",
                "arguments": {}
            }
        """

    def submit_bid(self, ticket: dict) -> dict:
        bid = tech_submit_bid(
            ticket["text"] if isinstance(ticket, dict) else str(ticket),
            current_load=self.current_load,
            urgency_score=ticket.get("urgency_score", 0) if isinstance(ticket, dict) else 0,
            ticket_id=ticket.get("ticket_id", "T000") if isinstance(ticket, dict) else "T000",
            instance_index=self.instance_index
        )
        return bid
        self.system_prompt = """
            You are the Technical Support Agent for a fictional e-commerce company.

            ROLE
            Investigate and resolve technical problems involving:
            - account access, authentication, sessions
            - dashboard
            - orders, order visibility, synchronization
            - cart
            - search
            - checkout
            - notifications
            - technical service health

            Do NOT handle:
            - payments, refunds, invoices, billing, subscription charges
            - compensation or retention offers

            CORE PRINCIPLE
            The customer ticket describes the customer's EXPERIENCE, not the
            underlying cause.

            Do not assume the cause from the ticket.
            Use the sandbox to determine what is actually happening.

            INVESTIGATION
            - Start with the most relevant diagnostic tool for the reported symptom.
            - Use the minimum observations needed to form a reasonable hypothesis.
            - Do not inspect unrelated systems or every available tool.
            - Expand the investigation only when evidence suggests another
            subsystem may be involved.
            - Do not perform an action without evidence supporting the repair.

            IDENTIFIERS
            - Never invent, guess, or extrapolate identifiers.
            - For order problems, list_orders provides the ONLY valid order IDs
            unless the customer explicitly provides an order ID.
            - If list_orders returns ORDER1001 and ORDER1002, ORDER1003 does not exist
            unless another sandbox result explicitly provides it.
            - If an identifier is not known, do not call a tool requiring that identifier.
            - If an identifier lookup fails, do not retry the same guessed identifier.

            ACTIONS AND VERIFICATION
            - Perform an ACTION only when sufficient evidence supports the repair.
            - After every successful ACTION, perform a separate OBSERVE using an
            appropriate diagnostic or verification tool.
            - An ACTION result showing success is not itself verification.
            - Verification must confirm that the intended sandbox state is now correct.
            - If an ACTION fails, do not repeat the same ACTION with the same arguments.
            Reassess the evidence and choose another diagnostic step if appropriate.
            - NEVER report "resolved" unless the final verification confirms the
            intended state is correct.
            - If the problem cannot be resolved, FINISH with an appropriate
            non-resolved status and explain why.

            DECISION TYPES
            OBSERVE: gather information.
            ACTION: perform a supported technical repair.
            FINISH: investigation and verification are complete.

            OUTPUT
            Return ONLY valid JSON.

            OBSERVE:
            {
                "type": "OBSERVE",
                "tool": "tool_name",
                "arguments": {}
            }

            ACTION:
            {
                "type": "ACTION",
                "tool": "tool_name",
                "arguments": {}
            }

            FINISH:
            {
                "type": "FINISH",
                "status": "resolved",
                "actions_taken": [],
                "verification": {},
                "customer_statement": "..."
            }

            HARD CONSTRAINTS
            - Never invent tool names.
            - Never invent tool results.
            - Never invent identifiers.
            - Use only information returned by the sandbox or provided by the customer.
            """

    def get_capabilities(self):
        return self.capability_card

    def respond_to_proposal(self, proposal: dict) -> dict:
        handler = TechnicalNegotiationHandler()
        action = proposal.get("action") or proposal.get("message_type")
        sender = proposal.get("sender", "peer_agent")
        print(f"[{self.agent_id}] Received proposal from {sender}: {proposal}")
        if action == "PROPOSE":
            res = handler.handle_proposal(proposal)
        elif action == "COUNTER":
            res = handler.handle_counter(proposal)
        elif action == "ACCEPT":
            res = {"action": "ACCEPT", "message_type": "ACCEPT", "sender": self.agent_id, "receiver": sender}
        else:
            res = {"action": "REJECT", "message_type": "REJECT", "sender": self.agent_id, "receiver": sender, "rationale": "Unsupported proposal action."}

        act_res = res.get("action") or res.get("message_type")
        if act_res == "ACCEPT":
            print(f"[{self.agent_id}] ACCEPTED proposal from {sender}")
        else:
            print(f"[{self.agent_id}] REJECTED/COUNTERED proposal from {sender}")
        return res

    def ask_qwen(self, messages):

        payload = {
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.1
            }
        }

        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=3
        )

        response.raise_for_status()

        data = response.json()

        return json.loads(
            data["message"]["content"]
        )


    # --------------------------------------------------
    # Available sandbox tools
    # --------------------------------------------------

    def get_tools(self):

        return {
            "check_account": {
                "type": "OBSERVE",
                "description": "Check account status and session status.",
                "arguments": {}
            },

            "list_orders": {
                "type": "OBSERVE",
                "description": "List available customer orders and their basic visibility/status information.",
                "arguments": {}
            },

            "check_order": {
                "type": "OBSERVE",
                "description": "Inspect a specific order.",
                "arguments": {
                    "order_id": "string"
                }
            },

            "check_dashboard": {
                "type": "OBSERVE",
                "description": "Check dashboard health and error state.",
                "arguments": {}
            },

            "check_cart": {
                "type": "OBSERVE",
                "description": "Check cart status and synchronization.",
                "arguments": {}
            },

            "check_search": {
                "type": "OBSERVE",
                "description": "Check search and search index health.",
                "arguments": {}
            },

            "check_checkout": {
                "type": "OBSERVE",
                "description": "Check checkout and checkout session state.",
                "arguments": {}
            },

            "check_notifications": {
                "type": "OBSERVE",
                "description": "Check notification system status.",
                "arguments": {}
            },

            "check_service_health": {
                "type": "OBSERVE",
                "description": "Check health of backend services.",
                "arguments": {}
            },

            "unlock_account": {
                "type": "ACTION",
                "description": "Unlock a locked customer account.",
                "arguments": {}
            },

            "reset_session": {
                "type": "ACTION",
                "description": "Reset an expired customer session.",
                "arguments": {}
            },

            "resync_orders": {
                "type": "ACTION",
                "description": "Resynchronize a specific order.",
                "arguments": {
                    "order_id": "string"
                }
            },

            "restore_dashboard": {
                "type": "ACTION",
                "description": "Restore a failed dashboard.",
                "arguments": {}
            },

            "refresh_cart": {
                "type": "ACTION",
                "description": "Refresh cart synchronization.",
                "arguments": {}
            },

            "rebuild_search_index": {
                "type": "ACTION",
                "description": "Rebuild the search index.",
                "arguments": {}
            },

            "reset_checkout_session": {
                "type": "ACTION",
                "description": "Reset a failed checkout session.",
                "arguments": {}
            },

            "restore_notifications": {
                "type": "ACTION",
                "description": "Restore notification service.",
                "arguments": {}
            },

            "verify_order": {
                "type": "OBSERVE",
                "description": "Verify that a specific order is visible and synchronized correctly after a repair.",
                "arguments": {
                    "order_id": "string"
                }
            },

            "verify_account": {
                "type": "OBSERVE",
                "description": "Verify that the customer account and session are active.",
                "arguments": {}
            },

            "verify_dashboard": {
                "type": "OBSERVE",
                "description": "Verify that the dashboard is healthy.",
                "arguments": {}
            }
        }


    # --------------------------------------------------
    # Execute sandbox tool
    # --------------------------------------------------

    def execute_tool(self, tool_name, arguments):

        allowed_tools = self.get_tools()

        if tool_name not in allowed_tools:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' is not available."
            }

        tool = getattr(
            self.sandbox,
            tool_name,
            None
        )

        if tool is None:
            return {
                "success": False,
                "error": f"Sandbox does not implement '{tool_name}'."
            }

        try:

            return tool(**arguments)

        except Exception as e:

            return {
                "success": False,
                "error": str(e)
            }


    # --------------------------------------------------
    # Main agent loop
    # --------------------------------------------------

    

    def _rule_based_solve(self, ticket_text: str) -> dict:
        text = ticket_text.lower()
        actions_taken = []
        observations = []

        if any(w in text for w in ["login", "locked", "account", "password", "session"]):
            obs = self.execute_tool("check_account", {})
            observations.append({"type": "OBSERVE", "tool": "check_account", "result": obs})
            if obs.get("account_status") == "LOCKED":
                act = self.execute_tool("unlock_account", {})
                actions_taken.append("unlock_account")
                observations.append({"type": "ACTION", "tool": "unlock_account", "result": act})
            if obs.get("session_status") == "EXPIRED":
                act = self.execute_tool("reset_session", {})
                actions_taken.append("reset_session")
                observations.append({"type": "ACTION", "tool": "reset_session", "result": act})

        if any(w in text for w in ["dashboard", "page not loading", "disappeared", "missing", "error", "working"]):
            obs = self.execute_tool("check_dashboard", {})
            observations.append({"type": "OBSERVE", "tool": "check_dashboard", "result": obs})
            if obs.get("status") in ["ERROR", "FAILED"]:
                act = self.execute_tool("restore_dashboard", {})
                actions_taken.append("restore_dashboard")
                observations.append({"type": "ACTION", "tool": "restore_dashboard", "result": act})

        resynced_order_ids = []
        if any(w in text for w in ["order", "orders", "sync"]):
            orders_obs = self.execute_tool("list_orders", {})
            observations.append({"type": "OBSERVE", "tool": "list_orders", "result": orders_obs})
            # list_orders returns a list of dicts; convert to {order_id: info} for iteration
            orders_raw = orders_obs.get("orders", [])
            if isinstance(orders_raw, list):
                orders = {o["order_id"]: o for o in orders_raw}
            else:
                orders = orders_raw  # fallback: already a dict
            for order_id, order_info in orders.items():
                if order_info.get("sync_status") in ["FAILED", "DESYNCED", "ERROR"] or not order_info.get("visible"):
                    act = self.execute_tool("resync_orders", {"order_id": order_id})
                    actions_taken.append(f"resync_orders({order_id})")
                    resynced_order_ids.append(order_id)
                    observations.append({"type": "ACTION", "tool": "resync_orders", "arguments": {"order_id": order_id}, "result": act})

        verification = {}
        if "restore_dashboard" in actions_taken:
            verification["dashboard"] = self.execute_tool("verify_dashboard", {})
        if resynced_order_ids:
            # Verify the first order that was actually resynced (not a hardcoded ID)
            verification["order"] = self.execute_tool("verify_order", {"order_id": resynced_order_ids[0]})
        if "unlock_account" in actions_taken or "reset_session" in actions_taken:
            verification["account"] = self.execute_tool("verify_account", {})

        status = "resolved" if actions_taken else "completed"
        statement = f"Technical investigation completed. Actions taken: {actions_taken if actions_taken else 'No technical repair required.'}"

        return {
            "status": status,
            "actions_taken": actions_taken,
            "verification": verification,
            "customer_statement": statement,
            "observations": observations
        }

    def handle_collaboration(self, ticket, order_id=None, subtask="", **kwargs):
        ticket_text = ticket.get("text", str(ticket)) if isinstance(ticket, dict) else str(ticket)
        print(f"[{self.agent_id}] Handling collaboration subtask: '{subtask}'")
        res = self.solve(ticket)
        return {
            "success": True,
            "agent_id": self.agent_id,
            "subtask": subtask,
            "result": res
        }

    def solve(self, ticket):
        ticket_text = ticket["text"] if isinstance(ticket, dict) else str(ticket)
        if isinstance(ticket, dict) and "ticket_id" in ticket:
            self.sandbox.current_ticket_id = ticket["ticket_id"]

        messages = [
            {
                "role": "system",
                "content": self.system_prompt
            },
            {
                "role": "user",
                "content": (
                    "Customer ticket:\n"
                    + ticket_text
                    + "\n\n"
                    + "Available sandbox tools:\n"
                    + json.dumps(
                        self.get_tools(),
                        indent=2
                    )
                )
            }
        ]

        actions_taken = []
        observations = []

        for step in range(MAX_STEPS):

            try:

                decision = self.ask_qwen(
                    messages
                )

            except Exception as e:
                print(f"[{self.agent_id}] LLM unavailable ({e}). Using rule-based fallback.")
                return self._rule_based_solve(ticket_text)

            print(
                f"\n[Agent Step {step + 1}]"
            )

            print(
                json.dumps(
                    decision,
                    indent=2
                )
            )


            decision_type = decision.get(
                "type"
            )


            # ------------------------------------------
            # FINISH
            # ------------------------------------------

            if decision_type == "FINISH":

                return {
                    "status": decision.get(
                        "status",
                        "completed"
                    ),

                    "actions_taken":
                        decision.get(
                            "actions_taken",
                            actions_taken
                        ),

                    "verification":
                        decision.get(
                            "verification",
                            {}
                        ),

                    "customer_statement":
                        decision.get(
                            "customer_statement",
                            ""
                        ),

                    "observations":
                        observations
                }


            # ------------------------------------------
            # OBSERVE / ACTION
            # ------------------------------------------

            if decision_type not in {
                "OBSERVE",
                "ACTION"
            }:

                tool_result = {
                    "success": False,
                    "error":
                        "Invalid decision type."
                }

            else:

                tool_name = decision.get(
                    "tool"
                )

                arguments = decision.get(
                    "arguments",
                    {}
                )

                tool_result = self.execute_tool(
                    tool_name,
                    arguments
                )

                if decision_type == "ACTION":

                    actions_taken.append(
                        tool_name
                    )

                observations.append({
                    "step": step + 1,
                    "type": decision_type,
                    "tool": tool_name,
                    "arguments": arguments,
                    "result": tool_result
                })


            print(
                "[Sandbox Result]"
            )

            print(
                json.dumps(
                    tool_result,
                    indent=2
                )
            )


            # Give Qwen the result of its decision.
            messages.append({
                "role": "assistant",
                "content": json.dumps(
                    decision
                )
            })

            messages.append({
                "role": "user",
                "content": (
                    "Sandbox result:\n"
                    + json.dumps(
                        tool_result,
                        indent=2
                    )
                    + "\n\n"
                    "Continue investigating or resolving "
                    "the ticket. Remember to verify actions "
                    "before finishing."
                )
            })


        # --------------------------------------------------
        # Safety stop
        # --------------------------------------------------

        return {
            "status": "incomplete",
            "actions_taken": actions_taken,
            "verification": {},
            "customer_statement":
                "I could not complete the technical investigation within the allowed steps.",
            "observations": observations
        }