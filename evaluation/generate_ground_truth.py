#!/usr/bin/env python3
"""
Emit an empty ground-truth template for evaluation/evaluate_models.py.

Workflow:
  1. Record video or export frames.
  2. Annotate in CVAT / Label Studio / LabelImg (slot polygons + plate strings).
  3. Map exports into the ``frames`` structure below (frame index or image basename → slots + plate).

  python -m evaluation.generate_ground_truth --output my_gt.json --num-frames 300
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="ground_truth_template.json")
    p.add_argument("--num-frames", type=int, default=10, help="Number of placeholder frame keys")
    args = p.parse_args()

    frames = {}
    for i in range(args.num_frames):
        frames[str(i)] = {
            "slots": [{"id": 0, "status": "free"}, {"id": 1, "status": "free"}],
            "plate": "",
            "notes": "Replace with real labels; status is free|occupied|reserved",
        }

    doc = {
        "_comment": "Frame keys must match evaluate_models frame order (0,1,2,…) or image basenames.",
        "frames": frames,
    }
    Path(args.output).write_text(json.dumps(doc, indent=2), encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
