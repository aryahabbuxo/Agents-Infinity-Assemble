from agent.retention_agent import RetentionAgent


agent = RetentionAgent(current_load=1)


ticket = {
    "ticket_id": "T001",
    "text": (
        "I've been a customer for three years and I've had several "
        "problems recently. Nobody seems to care and I'm seriously "
        "thinking about cancelling my subscription."
    ),
    "urgency_score": 72
}


result = agent.submit_bid(ticket)

print("\nRETENTION BID:")
print(result)