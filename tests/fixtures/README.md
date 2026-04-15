# Test fixtures

## `sample_gt.json`

Minimal ground-truth example for `evaluation/evaluate_models.py` (two frames, toy labels).

## Optional image frames

For `@pytest.mark.evaluation` image tests, add small `.png` files here (e.g. `frame_000.png`).  
If absent, tests use synthetic numpy frames from `conftest` fixtures.
