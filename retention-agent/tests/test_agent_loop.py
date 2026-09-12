from agent.agent_loop import RetentionAgentLoop


loop = RetentionAgentLoop()

ticket = """
Customer ID: C001

I have been a customer for three years and I've had several problems
recently. Nobody seems to care and I'm seriously thinking about
cancelling my subscription.
"""

result = loop.run(ticket)

print("\nRETURNED RESULT:")
print(result)