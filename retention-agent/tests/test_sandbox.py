from sandbox.state import RetentionSandbox
from sandbox.tools import RetentionTools


sandbox = RetentionSandbox()
tools = RetentionTools(sandbox)

print("\nCUSTOMER PROFILE")
print(tools.get_customer_profile("C001"))

print("\nCANCELLATION STATUS")
print(tools.check_cancellation_status("C001"))

print("\nRETENTION OFFER")
print(tools.check_retention_offer("C001"))

print("\nAPPLYING OFFER")
print(tools.apply_retention_offer("C001"))

print("\nCUSTOMER AFTER ACTION")
print(tools.get_customer_profile("C001"))