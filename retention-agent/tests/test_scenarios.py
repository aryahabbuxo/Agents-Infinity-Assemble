from agent.retention_agent import RetentionAgent
from sandbox.state import RetentionSandbox


def run_scenario(customer_id, ticket_text):

    print("\n" + "=" * 60)
    print(f"TESTING CUSTOMER: {customer_id}")
    print("=" * 60)

    agent = RetentionAgent()
    ticket = {
        "ticket_id": f"T-{customer_id}",
        "text": ticket_text,
        "urgency_score": 60,
    }

    result = agent.handle_ticket(ticket, customer_id=customer_id)

    print("\nFINAL RESULT:")
    print(result)

    sandbox = RetentionSandbox()
    customer = sandbox.get_customer(customer_id)

    print("\nFINAL SANDBOX STATE:")
    print(customer)

    return result, customer



# ---------------------------------------------------------
# TEST 1: CUSTOMER IS ONLY CONSIDERING CANCELLATION
# ---------------------------------------------------------

ticket_1 = """
Customer ID: C001

I have been a customer for three years and I've had several
problems recently. Nobody seems to care and I'm seriously
thinking about cancelling my subscription.
"""

run_scenario("C001", ticket_1)


# ---------------------------------------------------------
# TEST 2: EXPLICIT CANCELLATION REQUEST
# ---------------------------------------------------------

ticket_2 = """
Customer ID: C003

I have had too many problems with my subscription.
I want to cancel my subscription.
"""

run_scenario("C003", ticket_2)