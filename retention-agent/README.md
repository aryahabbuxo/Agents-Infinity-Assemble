# Retention Agent

An autonomous, emotion-aware **Customer Retention Agent** designed to operate as one of three agents in a decentralized multi-agent customer support market.

The Retention Agent focuses on understanding **customer dissatisfaction, churn risk, cancellation intent, and emotional state**, while collaborating with specialized agents such as the Billing Agent when a ticket spans multiple domains.

---

## 1. Overview

The Retention Agent is responsible for:

* Understanding the customer's emotional state
* Estimating churn risk
* Identifying retention-related signals
* Investigating customer/account state through sandbox tools
* Diagnosing the customer's retention situation
* Assessing its confidence/capability for a ticket
* Incorporating emotional signals into bidding
* Negotiating with other agents when collaboration is required
* Delegating billing-specific work to the Billing Agent
* Executing allowed retention actions through its sandbox
* Verifying state changes
* Producing an evidence-backed final response

The agent is designed to follow the project's autonomous multi-agent architecture rather than simply answering tickets directly.

---

# 2. Architecture

```text
                    CUSTOMER TICKET
                          |
                          v
                 +-------------------+
                 |  Retention Agent  |
                 +-------------------+
                          |
             +------------+------------+
             |            |            |
             v            v            v
        Emotion       Investigation   Bidding
        Analysis          |             |
             |            v             |
             |         Diagnosis        |
             |            |             |
             +------------+-------------+
                          |
                          v
                    Action Planning
                          |
                 +--------+--------+
                 |                 |
                 v                 v
          Retention Sandbox   Billing Agent
                 |                 |
                 v                 v
             State Change     Collaboration
                 |                 |
                 +--------+--------+
                          |
                          v
                     Verification
                          |
                          v
                    Final Statement
```

---

# 3. Repository Structure

```text
retention-agent/
│
├── main.py
│
├── agent/
│   ├── __init__.py
│   ├── retention_agent.py
│   ├── prompts.py
│   ├── schemas.py
│   ├── tool_dispatcher.py
│   ├── interface.py
│   ├── emotion.py
│   └── bidding.py
│
├── sandbox/
│   ├── __init__.py
│   ├── state.py
│   └── tools.py
│
├── tests/
│   ├── test_agent.py
│   ├── test_sandbox.py
│   ├── test_scenarios.py
│   ├── test_interface.py
│   ├── test_emotion.py
│   └── test_bidding.py
│
├── data/
│   └── customers.json
│
├── requirements.txt
│
└── README.md
```

`agent_loop.py` was removed because it duplicated logic that is now handled by `RetentionAgent`.

`RetentionAgent` is the current source of truth for the agent workflow.

---

# 4. Emotion-Aware Retention

One of the main differentiators of this agent is its dedicated emotional-intelligence component.

The emotion engine uses an Ollama-hosted LLM to analyze the customer's message.

It identifies:

* Primary emotion
* Emotion intensity
* Frustration level
* Helplessness level
* Churn risk
* Explicit cancellation request
* Retention signals

Supported emotional states include:

* Anger
* Frustration
* Irritation
* Helplessness
* Disappointment
* Anxiety
* Betrayal
* Sadness
* Confusion
* Urgency-related distress
* Calmness

### Example

For:

```text
"I have been charged for this month even though I tried to cancel.
I am extremely frustrated and seriously considering leaving."
```

the emotion engine can produce:

```json
{
    "primary_emotion": "frustration",
    "emotion_intensity": 1.0,
    "frustration_level": 1.0,
    "helplessness_level": 0.0,
    "churn_risk": 0.8,
    "explicit_cancellation_request": false,
    "retention_signals": [
        "attempted_cancellation",
        "considering_leaving"
    ]
}
```

The system deliberately does **not** generate `urgency_score`.

Urgency is supplied separately by the ticket/system.

---

# 5. Emotion Analysis Pipeline

```text
Customer Message
       |
       v
Emotion Prompt
       |
       v
Ollama / LLM
       |
       v
Raw Response
       |
       v
JSON Extraction
       |
       v
Validation
       |
       v
Structured Emotion Analysis
```

The emotion module validates numerical values to ensure they remain between `0` and `1`.

If the LLM request fails or produces invalid JSON, the system falls back to a safe default emotion result rather than crashing the entire agent.

---

# 6. Customer Investigation

The Retention Agent does not directly modify customer state.

Instead, it investigates customers through sandbox tools.

Available investigation capabilities include:

### Customer profile

```text
get_customer_profile()
```

Retrieves relevant customer information such as:

* Name
* Subscription
* Subscription status
* Months as customer
* Recent complaints
* Satisfaction score
* Cancellation status
* Loyalty points
* Retention-offer availability

### Cancellation status

```text
check_cancellation_status()
```

Checks whether the customer has requested cancellation and the current subscription state.

### Retention offer

```text
check_retention_offer()
```

Checks whether a retention offer is available.

---

# 7. Diagnosis

After emotion analysis and investigation, the agent combines both sources of information.

The diagnosis contains:

```text
Customer State
Emotional State
Cancellation State
Retention Offer State
Retention Assessment
```

The retention assessment includes:

* Churn risk
* Frustration
* Helplessness
* Explicit cancellation intent

This means retention decisions are not based solely on account data.

For example:

```text
Low satisfaction
       +
High frustration
       +
High churn risk
       +
Repeated complaints
       =
High-priority retention situation
```

---

# 8. Retention Actions

The Retention Agent operates through controlled sandbox tools.

It does not directly mutate the underlying customer dictionary.

## Apply retention offer

```text
apply_retention_offer()
```

This:

* Checks whether the customer exists
* Checks whether a retention offer is available
* Records the state before the action
* Disables the offer
* Increases satisfaction score
* Saves the updated state
* Records the state after the action

Example:

```text
Before:
satisfaction_score = 32
retention_offer_available = true

After:
satisfaction_score = 52
retention_offer_available = false
```

---

## Cancel subscription

```text
cancel_subscription()
```

This action:

* Requires cancellation to have been requested
* Checks whether the subscription is already cancelled
* Records the previous state
* Changes the subscription status
* Saves the state
* Records evidence of the change

The agent therefore cannot arbitrarily cancel a customer's subscription.

The sandbox enforces the allowed operation.

---

# 9. Sandbox Evidence

The Retention sandbox maintains an action log.

Each successful state-changing action records evidence containing:

```text
customer_id
action
before
after
```

The sandbox exposes:

```text
record_action()
get_action_log()
```

This provides observable evidence of what the agent actually did.

This is important for the project's later vetting layer because the system can distinguish between:

```text
Agent said it did something
```

and:

```text
Agent actually changed sandbox state
```

---

# 10. Bidding

The Retention Agent participates in the project's agent marketplace.

It independently assesses its capability/confidence for a ticket.

The project's bidding formula is:

```python
load_penalty = min(current_load * 0.15, 0.6)

urgency_weight = 1 + (urgency_score / 100) * 0.3

final_bid = raw_confidence * (1 - load_penalty) * urgency_weight
```

The Retention Agent's emotional analysis influences its confidence assessment.

For example, a ticket containing strong churn signals and customer dissatisfaction is particularly relevant to the Retention Agent.

Urgency remains an external ticket input and is **not generated by the emotion engine**.

---

# 11. Billing Collaboration

Retention tickets can span multiple domains.

For example:

```text
"I was charged even though I tried to cancel and now I'm thinking of leaving."
```

This contains both:

* Retention concerns
* Billing concerns

The Retention Agent can therefore collaborate with the Billing Agent.

The current integration uses:

```text
Retention Agent
       |
       | PROPOSE
       v
Billing Agent
       |
       | ACCEPT
       v
Billing Collaboration
```

The negotiation supports:

```text
PROPOSE
COUNTER
ACCEPT
REJECT
```

and is limited to a maximum of three negotiation turns.

---

# 12. Collaboration Negotiation

Retention proposes a division of responsibility.

Example:

```json
{
    "sender": "retention_agent",
    "receiver": "billing_agent",
    "action": "PROPOSE",
    "my_assigned_subtask":
        "Assess the customer's dissatisfaction, churn risk, and cancellation/retention needs.",
    "your_requested_subtask":
        "Investigate and resolve the billing-related portion of the customer's issue.",
    "rationale":
        "The ticket needs Billing expertise."
}
```

Billing can accept the proposal.

Example:

```json
{
    "sender": "billing_agent",
    "action": "ACCEPT"
}
```

Once accepted, Retention sends the Billing-specific task to Billing's collaboration endpoint.

---

# 13. Billing Agent Integration

Billing runs independently and exposes:

```text
POST /negotiate
POST /collaborate
```

Retention communicates with it through HTTP.

Default Billing endpoint:

```text
http://127.0.0.1:8000
```

Retention runs separately on:

```text
http://127.0.0.1:8001
```

The collaboration flow is:

```text
Retention
    |
    | POST /negotiate
    v
Billing
    |
    | ACCEPT
    v
Retention
    |
    | POST /collaborate
    v
Billing
    |
    v
Billing Sandbox
    |
    v
State Change
    |
    v
Billing Result
```

---

# 14. Verified Billing Collaboration

The Billing sandbox contains multiple hidden scenarios.

Example:

```text
O-1001
```

represents a refund stuck at the payment gateway:

```text
payment_status = REFUND_INITIATED
refund_status = PENDING
```

Billing investigates the order and can execute:

```text
release_pending_refund()
```

which changes:

```text
PENDING
   ↓
PROCESSED
```

The Billing collaboration response includes:

```text
investigation
diagnosis
execution_results
state_before_after
```

This successfully demonstrates real cross-agent collaboration and observable sandbox state change.

---

# 15. Important Sandbox Boundary

The Retention Agent does not directly edit:

```text
customers
```

Instead:

```text
Retention Agent
       |
       v
Retention Tools
       |
       v
Retention Sandbox
       |
       v
Customer State
```

Likewise, Billing owns its own sandbox:

```text
Billing Agent
       |
       v
Billing Tools / Sandbox
       |
       v
Billing State
```

This keeps agent reasoning separate from system state.

---

# 16. Full Retention Workflow

The main ticket-processing workflow is approximately:

```text
1. Receive ticket
        |
2. Analyze customer emotion
        |
3. Investigate customer
        |
4. Diagnose situation
        |
5. Assess capability / plan response
        |
6. Determine required actions
        |
7. Detect need for Billing collaboration
        |
8. Negotiate with Billing
        |
9. Execute Retention-side actions
        |
10. Execute Billing collaboration
        |
11. Verify state changes
        |
12. Generate final statement
        |
13. Return structured result
```

---

# 17. API

The Retention service exposes a ticket-handling endpoint.

### Handle Ticket

```text
POST /handle_ticket
```

The request contains:

```json
{
    "ticket": {
        "ticket_id": "T001",
        "text": "Customer complaint...",
        "urgency_score": 80,
        "order_id": "O-1001"
    },
    "customer_id": "C003"
}
```

The response can contain:

```json
{
    "ticket_id": "T001",
    "customer_id": "C003",
    "emotion_analysis": {},
    "investigation": {},
    "diagnosis": {},
    "execution_results": [],
    "verification": {},
    "negotiation_transcript": [],
    "collaboration_result": {},
    "state_before_after": [],
    "final_statement": "..."
}
```

---

# 18. Collaboration Response

When Retention collaborates with Billing, the response includes:

```text
collaboration_result
```

which contains the result returned by Billing.

This allows the final ticket result to expose:

* Billing investigation
* Billing diagnosis
* Billing execution
* Billing state changes

rather than hiding the collaboration internally.

---

# 19. Error Handling

The agent includes defensive handling for several failure cases.

### LLM failure

If emotion analysis fails:

```text
emotion = unknown
```

with safe default numerical values.

### Missing customer

Sandbox tools return an error rather than mutating nonexistent state.

### Invalid retention action

The sandbox rejects actions that violate customer state.

### Already cancelled subscription

The agent receives:

```text
Subscription is already cancelled.
```

instead of attempting another cancellation.

### Missing Billing order

Billing returns:

```text
Unknown order_id
```

rather than silently executing an action.

### Failed collaboration

The Retention Agent records the collaboration failure in:

```text
collaboration_result
```

instead of crashing the complete ticket workflow.

---

# 20. Current Agent-to-Agent Demonstration

A successful Billing collaboration has been verified independently.

For Billing order:

```text
O-1001
```

the Billing Agent produced:

```text
Diagnosis:
Refund stuck at gateway longer than expected.

Action:
release_pending_refund

State:
PENDING → PROCESSED
```

This confirms that the collaboration endpoint is not merely passing messages; it can trigger an actual state-changing operation inside the Billing sandbox.

---

# 21. Design Principles

The Retention Agent follows these principles:

### Emotion-aware

Customer emotion is treated as a first-class signal.

### Autonomous

The agent investigates, reasons, plans, collaborates, and acts without requiring a hardcoded response for every ticket.

### Tool-mediated execution

Agents do not directly mutate sandbox state.

### Specialized collaboration

Retention handles retention-related reasoning while Billing handles billing-specific investigation and actions.

### Observable execution

Actions generate before/after evidence.

### Independent agents

Each agent owns its own capabilities, reasoning, and sandbox.

### Modular architecture

The agent is designed so the marketplace, vetting, and economy layers can be connected later.

---

# 22. Current Scope

### Implemented

* [x] Retention Agent
* [x] Emotion analysis
* [x] Frustration detection
* [x] Helplessness detection
* [x] Churn-risk assessment
* [x] Cancellation detection
* [x] Retention signals
* [x] Customer investigation
* [x] Retention diagnosis
* [x] Retention bidding
* [x] Controlled sandbox tools
* [x] Retention state-changing actions
* [x] Action evidence logging
* [x] Billing negotiation
* [x] Billing collaboration
* [x] Cross-agent HTTP communication
* [x] Billing sandbox execution
* [x] Before/after state evidence
* [x] Collaboration result returned by Retention

### Not yet implemented

The following are intentionally outside the current Retention Agent scope:

* [ ] Full three-agent market orchestration
* [ ] Auction/market coordinator
* [ ] Final vetting layer
* [ ] Cosine-similarity scoring
* [ ] LLM judge
* [ ] Economy/payout system
* [ ] Dashboard integration
* [ ] Full Technical Agent integration

These can be added once the three individual agents and their collaboration flows are stable.

---

# 23. Running the Agent

The Retention Agent uses Ollama for local LLM inference.

Default Ollama endpoint:

```text
http://localhost:11434/api/chat
```

Default model:

```text
llama3.1
```

Retention service:

```text
http://127.0.0.1:8001
```

Billing service:

```text
http://127.0.0.1:8000
```

Both services must be running for cross-agent collaboration.

---

# 24. Example End-to-End Scenario

### Customer

```text
"I have been charged for this month even though I tried to cancel.
I am extremely frustrated and seriously considering leaving."
```

### Retention identifies

```text
Emotion:
frustration

Intensity:
1.0

Frustration:
1.0

Churn risk:
0.8

Retention signals:
attempted_cancellation
considering_leaving
```

### Retention investigates

```text
Customer profile
Cancellation status
Retention offer
```

### Retention diagnoses

```text
High dissatisfaction
High churn risk
Cancellation-related issue
Billing involvement required
```

### Retention negotiates

```text
Retention → Billing
PROPOSE
```

Billing:

```text
ACCEPT
```

### Billing investigates

```text
Order: O-1001

Refund:
PENDING
```

### Billing acts

```text
release_pending_refund()
```

### Sandbox evidence

```text
Before:
refund_status = PENDING

After:
refund_status = PROCESSED
```

### Final system result

The ticket now contains evidence from both agents, allowing the system to demonstrate:

```text
Emotion Understanding
        +
Autonomous Diagnosis
        +
Agent Negotiation
        +
Specialized Billing Execution
        +
Observable Sandbox State Change
```

---

# 25. Project Vision

The Retention Agent is intended to be more than a conventional customer-support chatbot.

Its role in the larger system is:

```text
Understand the customer
        ↓
Understand the customer's emotional state
        ↓
Assess retention risk
        ↓
Determine its own capability
        ↓
Compete for / receive relevant work
        ↓
Collaborate with specialized agents
        ↓
Take controlled actions
        ↓
Produce observable evidence
        ↓
Help retain the customer
```

The key differentiator is the combination of **emotion-aware reasoning, autonomous decision-making, multi-agent collaboration, and sandbox-grounded execution**.
