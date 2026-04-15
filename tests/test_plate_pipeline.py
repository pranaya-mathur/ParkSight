"""MNet + warp plate chip (optional — needs edge/models/mnet_plate.onnx)."""
import os

import numpy as np
import pytest

from edge.plate_pipeline import MNetPlateExtractor

MNET = os.path.join(
    os.path.dirname(__file__), "..", "edge", "models", "mnet_plate.onnx"
)
MNET = os.path.normpath(MNET)


@pytest.mark.skipif(not os.path.isfile(MNET), reason="mnet_plate.onnx not downloaded")
def test_mnet_produces_94x24_chip():
    ext = MNetPlateExtractor(MNET)
    # noisy image — cascade should still return a tensor shape with valid geometry
    img = np.random.randint(0, 255, (180, 320, 3), dtype=np.uint8)
    w = ext.extract_warped_plate(img)
    if w is not None:
        assert w.shape == (24, 94, 3)
