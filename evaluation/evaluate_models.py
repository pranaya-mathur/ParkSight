#!/usr/bin/env python3
"""
Pilot-readiness evaluation: YOLO + slot engine + optional ONNX identity/plate.

Run from repository root:

  python -m evaluation.evaluate_models --video path/to.mp4 --gt path/to/gt.json --output eval_results.json

Ground truth JSON format::

  {
    "frames": {
      "0": {"slots": [{"id": 0, "status": "free"}], "plate": "京A12345"},
      "1": { ... }
    }
  }

Frame keys are string indices in order (0,1,2,…) matching read order from video,
or basenames when using --frames-dir.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

import numpy as np

# Repo root on path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.metrics import (
    collect_ioa_values,
    detection_class_histogram,
    flag_borderline_ioa,
    plate_metrics,
    slot_status_accuracy,
    two_wheeler_ratio,
    weighted_system_score,
)
from edge.cv_inference import CVInference
from edge.onnx_identity import OnnxIdentityRuntime
from edge.slot_engine import SlotEngine


def load_gt(path: str) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def iter_video_frames(path: str) -> Iterator[Tuple[int, np.ndarray]]:
    import cv2

    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {path}")
    i = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        yield i, frame
        i += 1
    cap.release()


def iter_dir_frames(path: str) -> Iterator[Tuple[str, np.ndarray]]:
    import cv2

    p = Path(path)
    exts = {".jpg", ".jpeg", ".png", ".bmp"}
    files = sorted([x for x in p.iterdir() if x.suffix.lower() in exts])
    for f in files:
        img = cv2.imread(str(f))
        if img is not None:
            yield f.name, img


def augment_low_light(img: np.ndarray, beta: int = -60, alpha: float = 1.2) -> np.ndarray:
    """Simulate darker scene (night-style) for robustness sweeps."""
    import cv2

    adj = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)
    return adj


def main() -> None:
    parser = argparse.ArgumentParser(description="ParkSight model / stack evaluation")
    parser.add_argument("--video", default="", help="Path to .mp4 / .avi / …")
    parser.add_argument("--frames-dir", default="", help="Folder of frame images (sorted)")
    parser.add_argument("--gt", default="", help="Ground truth JSON (see module docstring)")
    parser.add_argument("--output", default="eval_results.json", help="Write aggregate JSON here")
    parser.add_argument(
        "--slot-config",
        default=str(ROOT / "edge" / "configs" / "kaggle_config.json"),
        help="Slot geometry JSON for SlotEngine.from_config",
    )
    parser.add_argument("--dry-run", action="store_true", help="No GT: report FPS + detection histogram only")
    parser.add_argument("--night-augment", action="store_true", help="Run second pass with low-light augmentation")
    parser.add_argument("--max-frames", type=int, default=0, help="Stop after N frames (0 = all)")
    args = parser.parse_args()

    if not args.video and not args.frames_dir:
        parser.error("Provide --video or --frames-dir")

    gt_data: Optional[Dict[str, Any]] = None
    if args.gt:
        gt_data = load_gt(args.gt)
        if "frames" not in gt_data:
            raise SystemExit("GT JSON must contain top-level 'frames' object")

    cv_infer = CVInference()
    slot_engine: SlotEngine
    sc_path = args.slot_config
    if os.path.isfile(sc_path):
        slot_engine = SlotEngine.from_config(sc_path)
    else:
        slot_engine = SlotEngine()

    onnx_id = OnnxIdentityRuntime()

    slot_accs: List[float] = []
    plate_char_accs: List[float] = []
    plate_full: List[float] = []
    fps_list: List[float] = []
    borderline_counts: List[int] = []
    tw_ratio_list: List[float] = []
    reid_stub: List[float] = []  # placeholder until cross-frame Re-ID eval wired

    def run_pass(aug_fn=None):
        if args.video:
            gen = iter_video_frames(args.video)
            key_mode = "index"
        else:
            gen = iter_dir_frames(args.frames_dir)
            key_mode = "name"

        for idx, (fid, frame_bgr) in enumerate(gen):
            if args.max_frames and idx >= args.max_frames:
                break
            if aug_fn is not None:
                frame_bgr = aug_fn(frame_bgr)

            t0 = time.perf_counter()
            dets = cv_infer.run_inference({"data": frame_bgr})
            occ = slot_engine.update_occupancy(dets)
            ioa_pairs = collect_ioa_values(slot_engine, dets)
            borderline_counts.append(len(flag_borderline_ioa(ioa_pairs)))
            hist = detection_class_histogram(dets)
            tw_ratio_list.append(two_wheeler_ratio(hist))

            # Optional plate read on largest car-like bbox
            plate_pred = ""
            for d in sorted(dets, key=lambda x: -(x["bbox"][2] - x["bbox"][0]) * (x["bbox"][3] - x["bbox"][1])):
                if str(d.get("label", "")).lower() not in ("car", "truck", "bus"):
                    continue
                x1, y1, x2, y2 = [int(round(v)) for v in d["bbox"]]
                h, w = frame_bgr.shape[:2]
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)
                if x2 - x1 < 32 or y2 - y1 < 32:
                    continue
                crop = frame_bgr[y1:y2, x1:x2]
                if onnx_id.lpr_available():
                    plate_pred = onnx_id.read_plate(crop)
                break

            dt = time.perf_counter() - t0
            fps_list.append(1.0 / max(dt, 1e-6))

            fk = str(fid) if key_mode == "index" else str(fid)
            fr = gt_data.get("frames", {}).get(fk) if gt_data is not None else None
            if fr:
                gt_slots = fr.get("slots") or []
                slot_accs.append(slot_status_accuracy(occ, gt_slots))
                pm = plate_metrics(plate_pred, fr.get("plate") or "")
                plate_char_accs.append(pm["char_accuracy_approx"])
                plate_full.append(pm["full_plate_match"])
                reid_stub.append(1.0)  # slot for future mAP

    def mean(xs: List[float]) -> float:
        return float(np.mean(xs)) if xs else 0.0

    run_pass(None)
    if not fps_list:
        print(json.dumps({"error": "no_frames_processed", "hint": "check video path or frames-dir"}, indent=2))
        sys.exit(1)

    summary: Dict[str, Any] = {
        "frames_evaluated": len(fps_list),
        "mean_fps": mean(fps_list),
        "mean_slot_accuracy": mean(slot_accs),
        "mean_alpr_char_accuracy": mean(plate_char_accs),
        "mean_full_plate_match": mean(plate_full),
        "mean_two_wheeler_ratio": mean(tw_ratio_list),
        "mean_borderline_ioa_slots": mean([float(x) for x in borderline_counts]),
        "weighted_score_stub": weighted_system_score(
            mean(slot_accs) or 0.0,
            mean(plate_char_accs) or 0.0,
            mean(reid_stub) or 0.0,
        ),
        "dry_run": args.dry_run or not bool(args.gt),
    }

    if args.night_augment:
        slot_accs.clear()
        plate_char_accs.clear()
        plate_full.clear()
        fps_list.clear()
        borderline_counts.clear()
        tw_ratio_list.clear()
        reid_stub.clear()
        run_pass(augment_low_light)
        summary["night_augment"] = {
            "frames_evaluated": len(fps_list),
            "mean_fps": mean(fps_list),
            "mean_slot_accuracy": mean(slot_accs),
            "mean_alpr_char_accuracy": mean(plate_char_accs),
            "mean_borderline_ioa_slots": mean([float(x) for x in borderline_counts]),
        }

    out_path = Path(args.output)
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
