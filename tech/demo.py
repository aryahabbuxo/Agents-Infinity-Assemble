import json

from environment import EcommerceEnvironment
from faultgen import generate_fault
from sandbox import TechnicalSandbox
from agent import TechnicalAgent


ticket = """I’m trying to place an order, but I can’t seem to complete what I’m trying to do. Everything on the site looks normal, but it’s not working the way I expected. Can you check what’s going on?"""


# --------------------------------------------------
# 1. Create fresh environment
# --------------------------------------------------

environment = EcommerceEnvironment()


# --------------------------------------------------
# 2. Generate hidden fault
# --------------------------------------------------

fault_result = generate_fault(
    ticket,
    environment
)


print("\n========== FAULTGEN ==========")

print(
    json.dumps(
        fault_result,
        indent=4
    )
)


# --------------------------------------------------
# 3. Create sandbox
# --------------------------------------------------

sandbox = TechnicalSandbox(
    environment
)


# --------------------------------------------------
# 4. Create Technical Agent
# --------------------------------------------------

agent = TechnicalAgent(
    sandbox
)


# --------------------------------------------------
# 5. Let the agent investigate + resolve
# --------------------------------------------------

print("\n========== TECHNICAL AGENT ==========")

result = agent.solve(
    ticket
)


# --------------------------------------------------
# 6. Final result
# --------------------------------------------------

print("\n========== FINAL RESULT ==========")

print(
    json.dumps(
        result,
        indent=4
    )
)


# --------------------------------------------------
# 7. Final environment state
# --------------------------------------------------

print("\n========== FINAL ENVIRONMENT ==========")

print(
    json.dumps(
        environment.get_state(),
        indent=4
    )
)