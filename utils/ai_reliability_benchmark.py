"""Provider-free benchmark for the bounded adaptive batching policy."""

from __future__ import annotations

from typing import Iterable


def _simulate_batch(size: int, failure_threshold: int, depth: int, max_depth: int) -> dict:
    if size <= failure_threshold:
        return {"calls": 1, "truncations": 0, "completed": size}
    if depth >= max_depth or size <= 1:
        return {"calls": 1, "truncations": 1, "completed": 0}
    left = size // 2
    right = size - left
    first = _simulate_batch(left, failure_threshold, depth + 1, max_depth)
    second = _simulate_batch(right, failure_threshold, depth + 1, max_depth)
    return {
        "calls": 1 + first["calls"] + second["calls"],
        "truncations": 1 + first["truncations"] + second["truncations"],
        "completed": first["completed"] + second["completed"],
    }


def simulate_reliability_policy(
    card_counts: Iterable[int] = (5, 10, 20, 30),
    *,
    batch_size: int = 10,
    failure_threshold: int = 6,
    max_recovery_depth: int = 2,
) -> dict:
    """Measure completion when a deterministic provider truncates large calls."""
    scenarios = []
    for count in card_counts:
        count = max(0, int(count))
        groups = [
            min(batch_size, count - offset)
            for offset in range(0, count, batch_size)
        ]
        runs = [
            _simulate_batch(size, failure_threshold, 0, max_recovery_depth)
            for size in groups
        ]
        calls = sum(run["calls"] for run in runs)
        completed = sum(run["completed"] for run in runs)
        truncations = sum(run["truncations"] for run in runs)
        scenarios.append({
            "requested_cards": count,
            "batch_size": batch_size,
            "provider_calls": calls,
            "retry_calls": max(0, calls - len(groups)),
            "truncations": truncations,
            "completed_cards": completed,
            "complete_card_rate": round(completed / count, 4) if count else 1.0,
            "success": completed == count,
            "average_cards_per_request": round(completed / calls, 3) if calls else 0.0,
            "output_tokens": None,
            "cost_usd": None,
            "latency_seconds": None,
        })
    return {
        "version": 1,
        "benchmark_type": "provider_free_simulation",
        "failure_model": f"truncate when request has more than {failure_threshold} cards",
        "max_recovery_depth": max_recovery_depth,
        "resource_metrics": "not measured without a real provider call",
        "scenarios": scenarios,
    }


__all__ = ["simulate_reliability_policy"]
