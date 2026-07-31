"""Baseline selection strategies for the LakeVideo research prototype."""
import random
from typing import List, Dict, Any


def baseline_full(scenes: List[Dict[str, Any]]) -> List[int]:
    """Use the entire scene list."""
    return [s["id"] for s in scenes]


def baseline_random(scenes: List[Dict[str, Any]], compression: float = 0.5) -> List[int]:
    """Randomly sample a fraction of scenes."""
    target = max(1, int(len(scenes) * (1 - compression)))
    return [s["id"] for s in random.sample(scenes, target)]


def baseline_quality_only(scenes: List[Dict[str, Any]], compression: float = 0.5) -> List[int]:
    """Select the highest visual-quality scenes."""
    target = max(1, int(len(scenes) * (1 - compression)))
    ranked = sorted(scenes, key=lambda x: x.get("visual_quality", 0.0), reverse=True)
    return [s["id"] for s in ranked[:target]]


def baseline_dedup_only(scenes: List[Dict[str, Any]], compression: float = 0.5) -> List[int]:
    """Pick one representative per cluster and fill the rest randomly."""
    clusters: Dict[Any, List[Dict[str, Any]]] = {}
    for s in scenes:
        clusters.setdefault(s.get("cluster_id"), []).append(s)

    chosen = [max(group, key=lambda x: x.get("utility", 0.0)).get("id") for group in clusters.values() if group]
    target = max(len(chosen), int(len(scenes) * (1 - compression)))
    remaining = [s["id"] for s in scenes if s["id"] not in chosen]
    if remaining and len(chosen) < target:
        chosen.extend(random.sample(remaining, min(target - len(chosen), len(remaining))))
    return chosen


def baseline_utility(scenes: List[Dict[str, Any]], compression: float = 0.5) -> List[int]:
    """Select the highest utility scenes (with duplicates handled by upstream optimizer)."""
    target = max(1, int(len(scenes) * (1 - compression)))
    ranked = sorted(scenes, key=lambda x: x.get("utility", 0.0), reverse=True)
    return [s["id"] for s in ranked[:target]]
