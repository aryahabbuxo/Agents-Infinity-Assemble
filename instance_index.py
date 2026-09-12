"""
instance_index.py

Unique Per-Agent Instance Index & Brier Calibration Gap Penalty Engine.

1. Instance Index:
   - Unique to each agent instance.
   - Stores performance history of resolved/attempted tickets.
   - Keeps top-performing instances (high coverage score, low calibration gap) at the TOP,
     and poorly-performing instances at the BOTTOM.
   - Allows agents to naturally iterate through past instances to adjust bidding confidence.

2. Calibration Penalty (apply_penalty):
   - Calculates the mismatch (calibration gap) between claimed raw_confidence and actual coverage_score.
   - Overconfidence (gap > 0) -> penalty applied to agent balance.
   - Humble / Accurate (gap <= 0) -> no penalty, small honesty reward.
   - Balance mutation happens inside this function.
"""

import time
import os
import json


class InstanceIndex:
    def __init__(self, agent_id: str, storage_dir: str = "."):
        self.agent_id = agent_id
        self.storage_file = os.path.join(storage_dir, f"instance_index_{agent_id}.json")
        # List of dicts: {"ticket_id", "text", "raw_confidence", "coverage_score", "gap", "success", "timestamp"}
        self.instances = []
        self._load()

    def _load(self):
        """Loads instances from disk if file exists."""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    self.instances = json.load(f)
                self._reindex(save=False)
            except Exception:
                self.instances = []

    def save(self):
        """Saves current instances state to JSON on disk."""
        try:
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump(self.instances, f, indent=2)
        except Exception as e:
            print(f"[InstanceIndex] Error saving to {self.storage_file}: {e}")

    def add_instance(self, ticket_id: str, text: str, raw_confidence: float, coverage_score: float) -> dict:
        gap = raw_confidence - coverage_score
        is_success = coverage_score >= 0.7

        entry = {
            "ticket_id": ticket_id,
            "text": text,
            "raw_confidence": round(raw_confidence, 4),
            "coverage_score": round(coverage_score, 4),
            "gap": round(gap, 4),
            "success": is_success,
            "timestamp": time.time(),
        }

        self.instances.append(entry)
        self._reindex(save=True)
        return entry

    def _reindex(self, save: bool = True):
        """
        Sort instances so top-performing instances are at the TOP (index 0)
        and poorly-performing instances are at the BOTTOM.
        Primary sort key: coverage_score (descending)
        Secondary sort key: gap (ascending, smaller overconfidence gap is better)
        """
        self.instances.sort(key=lambda x: (-x["coverage_score"], x["gap"]))
        if save:
            self.save()

    def get_indexed_instances(self) -> list:
        """Returns instances ordered from top (best) to bottom (worst)."""
        return self.instances

    def get_adjusted_confidence(self, base_confidence: float, ticket_text: str) -> float:
        """
        Adjust raw_confidence by reading through top/bottom instances.
        If past performance shows overconfidence (large positive gaps), tone down confidence.
        If past performance on similar tickets was strong, maintain/boost confidence.
        """
        if not self.instances:
            return round(base_confidence, 4)

        # Calculate historical average calibration gap
        gaps = [inst["gap"] for inst in self.instances]
        avg_gap = sum(gaps) / len(gaps)

        # Overconfidence penalty adjustment: if agent is historically overconfident (avg_gap > 0),
        # reduce base confidence by proportional factor.
        if avg_gap > 0.1:
            penalty_factor = min(0.35, avg_gap * 0.5)
            adjusted = base_confidence * (1.0 - penalty_factor)
        elif avg_gap < -0.1:
            # Underconfident / humble agent historically -> small boost up to +0.05
            adjusted = min(0.97, base_confidence + 0.05)
        else:
            adjusted = base_confidence

        return round(max(0.05, min(0.97, adjusted)), 4)


def apply_penalty(raw_confidence: float, coverage_score: float, agent: object = None) -> dict:
    """
    Penalizes the calibration gap: gap = raw_confidence - coverage_score

    Large positive gap (e.g. bid 90% confident, scored 30% coverage) -> genuine overconfidence -> penalty.
    Small or negative gap (e.g. bid 40% confident, scored 70% coverage) -> humble/accurate -> zero penalty, small honesty reward.

    Mutates agent balance if agent object provided.
    Orchestrator ONLY calls this function and logs the returned dict.
    """
    gap = raw_confidence - coverage_score

    if gap > 0:
        # Overconfidence penalty proportional to gap squared
        penalty = round(15.0 * (gap ** 2), 2)
    else:
        penalty = 0.0

    net_change = -penalty

    if agent is not None and hasattr(agent, "balance"):
        agent.balance = round(agent.balance + net_change, 2)
        new_balance = agent.balance
        agent_id = getattr(agent, "agent_id", str(agent))
    else:
        new_balance = 0.0
        agent_id = getattr(agent, "agent_id", "unknown") if agent else "unknown"

    return {
        "agent_id": agent_id,
        "raw_confidence": round(raw_confidence, 4),
        "coverage_score": round(coverage_score, 4),
        "calibration_gap": round(gap, 4),
        "penalty": penalty,
        "net_change": net_change,
        "new_balance": new_balance,
    }
