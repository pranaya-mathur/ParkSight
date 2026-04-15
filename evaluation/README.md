# Evaluation & pilot benchmarks

## Quick eval (no labels)

From repo root, with a short clip:

```bash
python -m evaluation.evaluate_models --video path/to/clip.mp4 --dry-run --max-frames 120 --output eval_results.json
```

Adds `--night-augment` to run a second pass with synthetic low-light.

## With ground truth

1. Generate a template:

   ```bash
   python -m evaluation.generate_ground_truth --output my_gt.json --num-frames 500
   ```

2. Fill `frames["<index>"]` with `slots` (list of `{id, status}`) and optional `plate` string.

3. Run:

   ```bash
   python -m evaluation.evaluate_models --video clip.mp4 --gt my_gt.json --output eval_results.json
   ```

## Pytest

- Full unit suite: `pytest tests/ -q`
- Slow / model-heavy checks: `pytest tests/ -m evaluation -q`

## Pilot thresholds (suggested baselines)

Tune to your facility after calibration:

| Metric | Target (internal test set) |
|--------|------------------------------|
| Mean slot status accuracy | ≥ 0.90 |
| Mean ALPR char accuracy (Levenshtein-based) | ≥ 0.85 |
| Mean FPS (edge-class CPU) | ≥ 8–15 depending on YOLO size |
| Borderline IOA slots per frame (0.4–0.6) | Trend down after calibration |
