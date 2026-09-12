from agent.retention_agent import RetentionAgent

agent = RetentionAgent()

ticket = """
Customer ID: C001

I have been a customer for three years and I've had several problems
recently. Nobody seems to care and I'm seriously thinking about
cancelling my subscription.
"""

response = agent.ask_llm(ticket)

print("\nLLM RESPONSE:")
print(response)