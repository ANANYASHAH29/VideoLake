"""Standalone experiment script for baseline comparison.

Usage (from repo root):
    python -m research.run_experiment --video-id 1 --compression 0.5
"""
import argparse
import asyncio
import httpx
from research.baselines import baselines
from research.evaluation import evaluate


async def main(video_id: int, compression: float, base_url: str = "http://localhost:8000"):
    async with httpx.AsyncClient() as client:
        # fetch all scenes for the video
        resp = await client.get(f"{base_url}/api/segmentation/scenes/{video_id}")
        resp.raise_for_status()
        scenes = resp.json()

    if not scenes:
        print(f"No scenes found for video {video_id}")
        return

    scene_map = {s["id"]: s for s in scenes}
    results = {}

    for name, fn in [
        ("full", baselines.baseline_full),
        ("random", baselines.baseline_random),
        ("quality", baselines.baseline_quality_only),
        ("dedup", baselines.baseline_dedup_only),
        ("proposed", baselines.baseline_utility),
    ]:
        selected, elapsed = evaluate.timed(fn, scenes, compression)
        metrics = evaluate.compute_metrics(selected, scenes, scene_map)
        metrics["processing_time_sec"] = elapsed
        results[name] = metrics

    print(f"Video {video_id} @ compression={compression}")
    for name, metrics in results.items():
        print(f"\n{name}:")
        for k, v in metrics.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LakeVideo baseline experiment")
    parser.add_argument("--video-id", type=int, required=True)
    parser.add_argument("--compression", type=float, default=0.5)
    parser.add_argument("--base-url", default="http://localhost:8000")
    args = parser.parse_args()
    asyncio.run(main(args.video_id, args.compression, args.base_url))
