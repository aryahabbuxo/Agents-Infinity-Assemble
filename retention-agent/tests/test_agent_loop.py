from agent.retention_agent import RetentionAgent

agent = RetentionAgent()

ticket = {
    "ticket_id": "T001",
    "text": """
Customer ID: C001

I have been a customer for three years and I've had several problems
recently. Nobody seems to care and I'm seriously thinking about
cancelling my subscription.
""",
    "urgency_score": 50,
}

result = agent.handle_ticket(ticket, customer_id="C001")

print("\nRETURNED RESULT:")
print(result)