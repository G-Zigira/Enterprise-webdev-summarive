"""
cleaning_log.py
===============
Task 1 – Data Processing & Cleaning
Tracks all exclusion reasons and counts for the technical report.

Usage:
    from pipeline.cleaning_log import CleaningLog
    log = CleaningLog()
    log.record("duplicates_removed", 1234, "Exact duplicate rows")
    log.print_summary()
    log.to_csv("data/cleaning_log.csv")
"""

import csv
import json
from datetime import datetime
from pathlib import Path


class CleaningLog:
    """
    Immutable append-only log of data cleaning decisions.

    Each entry records:
        step        — short machine-readable key
        count       — number of records affected
        description — human-readable explanation
        timestamp   — ISO 8601 wall-clock time
    """

    def __init__(self):
        self._entries: list[dict] = []
        self._start = datetime.now()

    def record(self, step: str, count: int, description: str) -> None:
        """Append one cleaning step to the log."""
        self._entries.append({
            "step":        step,
            "count":       count,
            "description": description,
            "timestamp":   datetime.now().isoformat(timespec="seconds"),
        })

    def print_summary(self) -> None:
        """Print a formatted summary table to stdout."""
        elapsed = (datetime.now() - self._start).total_seconds()
        print(f"\n{'─'*62}")
        print(f"  CLEANING LOG  ({len(self._entries)} steps, {elapsed:.1f}s elapsed)")
        print(f"{'─'*62}")
        print(f"  {'STEP':<30}  {'COUNT':>10}  DESCRIPTION")
        print(f"{'─'*62}")
        for e in self._entries:
            flag = "  " if e["count"] == 0 else "⚠ " if e["count"] > 1000 else "  "
            print(f"  {flag}{e['step']:<28}  {e['count']:>10,}  {e['description']}")
        print(f"{'─'*62}\n")

    def to_csv(self, path: str | Path) -> None:
        """Export the log to a CSV file for the technical report."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["step","count","description","timestamp"])
            writer.writeheader()
            writer.writerows(self._entries)
        print(f"[cleaning_log] Saved to {path}")

    def to_json(self, path: str | Path) -> None:
        """Export the log to JSON."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._entries, f, indent=2)
        print(f"[cleaning_log] Saved to {path}")

    def get(self, step: str) -> int | None:
        """Retrieve the count for a specific step key."""
        for e in self._entries:
            if e["step"] == step:
                return e["count"]
        return None

    def __len__(self) -> int:
        return len(self._entries)

    def __repr__(self) -> str:
        return f"CleaningLog(steps={len(self._entries)})"
