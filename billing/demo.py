"""
demo.py

Run this file to see the Billing Agent's full pipeline end-to-end:
  bid -> investigate -> diagnose -> execute -> (maybe negotiate) -> final statement

    python3 demo.py

Works with zero external dependencies: if no LLM backend is running,
bidding.py and agent.py automatically fall back to their rule-based logic.
"""

import json
from billing.agent import BillingAgent
from billing.sandbox import BillingSandbox

TICKETS = [
    {
        "ticket_id": "T-A",
        "order_id": "O-1001",
        "urgency_score": 40,
        "text": "My refund hasn't shown up yet, it's been 2 days, please check the payment.",
    },
    {
        "ticket_id": "T-B",
        "order_id": "O-1002",
        "urgency_score": 55,
        "text": "I was charged and refund never came through, my bank account details might be wrong.",
    },
    {
        # The exact worked example from the master context, section 20.
        "ticket_id": "T007",
        "order_id": "O-1003",
        "urgency_score": 72,
        "text": (
            "I had an item marked for return and refund however it's no longer visible "
            "in my orders section in my profile dashboard. I want my money transferred "
            "back to me immediately. I am losing my patience, this issue hasn't been "
            "addressed since 2 days."
        ),
    },
    {
        "ticket_id": "T-D",
        "order_id": "O-1004",
        "urgency_score": 20,
        "text": "I never received an invoice/receipt for my last order, can you resend it?",
    },
    {
        "ticket_id": "T-E",
        "order_id": "O-1005",
        "urgency_score": 65,
        "text": "I think I was charged twice for the same order, please check and refund the extra charge.",
    },
    {
        "ticket_id": "T-F",
        "order_id": "O-1006",
        "urgency_score": 50,
        "text": "My subscription was billed twice this month, that can't be right.",
    },
    {
        "ticket_id": "T-G",
        "order_id": "O-1007",
        "urgency_score": 80,
        "text": "I only got part of my refund back, where is the rest of my money? It's been 5 days!",
    },
]


def run():
    sandbox = BillingSandbox()
    agent = BillingAgent(sandbox=sandbox, current_load=1)  # pretend agent already has 1 active ticket

    for ticket in TICKETS:
        print("=" * 70)
        print(f"TICKET {ticket['ticket_id']}: {ticket['text']}")
        print("-" * 70)

        bid = agent.submit_bid(ticket)
        print("BID BREAKDOWN:", json.dumps(bid, indent=2))

        # In the real system, the market compares this bid against Technical
        # and Retention's bids, and the highest becomes Lead. Here we just
        # assume Billing won, so we can test the rest of the pipeline.
        result = agent.handle_ticket(ticket, order_id=ticket["order_id"])

        print("\nDIAGNOSIS:", result["diagnosis"]["diagnosis"])
        print("STATE CHANGES (before -> after):")
        for change in result["state_before_after"]:
            print(f"  {change['action']}: {change['before']} -> {change['after']}")

        if result["negotiation_transcript"]:
            print("\nNEGOTIATION TRANSCRIPT:")
            for msg in result["negotiation_transcript"]:
                print(" ", msg)

        print("\nFINAL STATEMENT:", result["final_statement"])
        print()


if __name__ == "__main__":
    run()