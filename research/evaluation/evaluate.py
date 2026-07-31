"""Evaluation utilities for LakeVideo research baselines."""
import time
import numpy as np
from typing import Dict, List, Any


def compute_metrics(
    selected_ids: List[int],
    scenes: List[Dict[str, Any]],
    scene_map: Dict[int, Dict[str, Any]],
) -> Dict[str, Any]:
    if not selected_ids or not scenes:
        return {}

    selected = [scene_map[sid] for sid in selected_ids if sid in scene_map]
    top_utility = sorted(scenes, key=lambda x: x.get("utility", 0.0), reverse=True)[
        : max(1, int(0.2 * len(scenes)))
    ]
    top_ids = {s["id"] for s in top_utility}

    return {
        "data_reduction": 1.0 - len(selected) / len(scenes),
        "selected": len(selected),
        "avg_utility": float(np.mean([s.get("utility", 0.0) for s in selected])),
        "diversity_retention": float(np.mean([s.get("diversity", 0.0) for s in selected])),
        "novelty_retention": float(np.mean([s.get("novelty", 0.0) for s in selected])),
        "retrieval_recall": len(top_ids.intersection(set(selected_ids))) / len(top_ids)
        if top_ids
        else 0.0,
    }


def timed(fn, *args, **kwargs):
    start = time.perf_counter()
    result = fn(*args, **kwargs)
    elapsed = time.perf_counter() - start
    return result, elapsed
