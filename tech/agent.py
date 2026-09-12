import json
import requests


OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen2.5:7b"


MAX_STEPS = 10


class TechnicalAgent:

    def __init__(self, sandbox):

        self.sandbox = sandbox

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
            timeout=300
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

    

    def solve(self, ticket):

        messages = [
            {
                "role": "system",
                "content": self.system_prompt
            },
            {
                "role": "user",
                "content": (
                    "Customer ticket:\n"
                    + ticket
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

                return {
                    "status": "error",
                    "actions_taken": actions_taken,
                    "verification": {},
                    "customer_statement":
                        "I was unable to complete the technical investigation.",
                    "error": str(e)
                }

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