"""Optional real CNN path for vehicle Re-ID (torchvision ResNet18)."""
import numpy as np
import pytest

pytest.importorskip("torch")
pytest.importorskip("torchvision")

from edge.identity_engine import IdentityEngine


def test_simulated_identity_default():
    eng = IdentityEngine(use_simulated=True)
    out = eng.extract_identity(None, vehicle_id_seed=3)
    assert len(out["embedding"]) == 512
    assert out["license_plate"]


def test_torch_embedding_from_crop():
    eng = IdentityEngine(use_simulated=False)
    crop = np.random.randint(0, 255, (72, 96, 3), dtype=np.uint8)
    out = eng.extract_identity(crop, vehicle_id_seed=0)
    assert len(out["embedding"]) == 512
    assert out["license_plate"] in ("UNREAD",) or isinstance(out["license_plate"], str)
