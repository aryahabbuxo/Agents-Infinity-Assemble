from copy import deepcopy
import sys
from pathlib import Path


def _add_root_to_path():
    root = Path(__file__).parent.parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


_add_root_to_path()
from shared_data import CUSTOMERS, shared_state_log  # noqa: E402


class RetentionSandbox:

    def __init__(self, data_file=None):
        self.customers = deepcopy(CUSTOMERS)

        # Stores evidence of state-changing actions.
        # This is useful for later vetting/audit.
        self.action_log = []

    def get_customer(self, customer_id):
        return self.customers.get(customer_id)

    def save(self):
        # In-memory sandbox state; changes persist in self.customers for the run
        pass

    def record_action(self, evidence):
        """Record observable evidence of a sandbox state change."""
        self.action_log.append(evidence)

    def get_action_log(self):
        """Return all recorded sandbox actions."""
        return self.action_log.copy()