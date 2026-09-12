from agent.emotion import analyze_emotion


tickets = [

    """
    I've contacted support four times and nobody has helped me.
    I'm extremely frustrated and honestly feel completely helpless.
    I'm done dealing with this company.
    """,

    """
    The service has been good overall. I just have a small question
    about my subscription.
    """,

    """
    I am seriously considering cancelling. I've had enough of these
    problems and I'm extremely angry about how this has been handled.
    """,
]


for i, ticket in enumerate(tickets, start=1):

    print("\n" + "=" * 60)
    print(f"EMOTION TEST {i}")
    print("=" * 60)

    result = analyze_emotion(ticket)

    print(result)