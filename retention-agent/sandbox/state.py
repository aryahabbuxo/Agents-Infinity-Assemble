import json
from pathlib import Path


class RetentionSandbox:

    def __init__(self, data_file="data/customers.json"):
        self.data_file = Path(data_file)
        self.customers = self._load_data()

        # Stores evidence of state-changing actions.
        # This is useful for later vetting/audit.
        self.action_log = []

    def _load_data(self):
        with open(self.data_file, "r") as file:
            return json.load(file)

    def get_customer(self, customer_id):
        return self.customers.get(customer_id)

    def save(self):
        with open(self.data_file, "w") as file:
            json.dump(
                self.customers,
                file,
                indent=2
            )

    def record_action(self, evidence):
        """Record observable evidence of a sandbox state change."""
        self.action_log.append(evidence)

    def get_action_log(self):
        """Return all recorded sandbox actions."""
        return self.action_log.copy()