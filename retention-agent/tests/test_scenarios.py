from agent.agent_loop import RetentionAgentLoop
from sandbox.state import RetentionSandbox


def run_scenario(customer_id, ticket):

    print("\n" + "=" * 60)
    print(f"TESTING CUSTOMER: {customer_id}")
    print("=" * 60)

    # Create a fresh loop/sandbox
    loop = RetentionAgentLoop()

    # Run the agent
    result = loop.run(ticket)

    print("\nFINAL RESULT:")
    print(result)

    # Read the final sandbox state
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