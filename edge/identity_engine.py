"""
ALPR & Re-ID backends (priority):

1. ONNX (recommended): OSNet vehicle Re-ID + ``mnet_plate.onnx`` (detect + warp) + ``lprnet.onnx`` in ``edge/models/`` (see ``download_models.py``).
2. Torch: ResNet18 + optional EasyOCR.
3. Simulated: deterministic demo vectors.

Env:
  PARKSIGHT_IDENTITY_MODE=auto|onnx|torch|simulated
    auto (default): ONNX if ``vehicle_reid_osnet.onnx`` exists, else simulated.
    onnx: ONNX only (falls back to simulated if files missing / errors).
    torch: torchvision ResNet18 (+ ALPR_EASYOCR=1 for EasyOCR).
  PARKSIGHT_IDENTITY_IMAGENET=1 — pretrained ResNet18 (torch path only).
  ALPR_EASYOCR=1 — enable EasyOCR (torch path).
"""
from __future__ import annotations

import hashlib
import logging
import os
from typing import List, Optional

import numpy as np

from .onnx_identity import OnnxIdentityRuntime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("identity-engine")

_MODE = os.getenv("PARKSIGHT_IDENTITY_MODE", "auto").lower().strip()
_USE_EASYOCR = os.getenv("ALPR_EASYOCR", "").lower() in ("1", "true", "yes")
_USE_IMAGENET = os.getenv("PARKSIGHT_IDENTITY_IMAGENET", "").lower() in ("1", "true", "yes")


class IdentityEngine:
    _resnet = None
    _easyocr_reader = None

    def __init__(self, use_simulated: Optional[bool] = None):
        self._onnx = OnnxIdentityRuntime()
        if use_simulated is True:
            self._backend = "simulated"
        elif use_simulated is False:
            self._backend = "onnx" if self._onnx.reid_available() else "torch"
        elif _MODE == "simulated":
            self._backend = "simulated"
        elif _MODE == "torch":
            self._backend = "torch"
        elif _MODE == "onnx":
            self._backend = "onnx"
        else:  # auto
            self._backend = "onnx" if self._onnx.reid_available() else "simulated"

        logger.info("IdentityEngine backend: %s", self._backend)

    @classmethod
    def _get_resnet(cls):
        if cls._resnet is not None:
            return cls._resnet
        import torch
        from torchvision import models, transforms

        if _USE_IMAGENET:
            m = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
        else:
            m = models.resnet18(weights=None)
        m.eval()
        m.fc = torch.nn.Identity()
        cls._resnet = (
            m,
            transforms.Compose(
                [
                    transforms.ToPILImage(),
                    transforms.Resize((224, 224)),
                    transforms.ToTensor(),
                    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
                ]
            ),
        )
        logger.info("Loaded torchvision ResNet18 for Re-ID embeddings")
        return cls._resnet

    @classmethod
    def _get_easyocr(cls):
        if cls._easyocr_reader is False:
            return None
        if cls._easyocr_reader is not None:
            return cls._easyocr_reader
        try:
            import easyocr

            cls._easyocr_reader = easyocr.Reader(["en"], gpu=False, verbose=False)
            logger.info("EasyOCR loaded for plate reading")
        except Exception as e:
            logger.warning("EasyOCR unavailable (%s)", e)
            cls._easyocr_reader = False
            return None
        return cls._easyocr_reader

    def _embedding_torch(self, crop_bgr: np.ndarray) -> List[float]:
        import torch

        if crop_bgr.dtype != np.uint8:
            crop_bgr = np.clip(crop_bgr, 0, 255).astype(np.uint8)
        h, w = crop_bgr.shape[:2]
        if h < 8 or w < 8:
            raise ValueError("crop too small")
        rgb = crop_bgr[:, :, ::-1].copy()
        model, tfm = self._get_resnet()
        t = tfm(rgb).unsqueeze(0)
        with torch.no_grad():
            vec = model(t).squeeze(0)
        vec = vec / (vec.norm(p=2) + 1e-9)
        return vec.cpu().numpy().astype(float).tolist()

    def _plate_easyocr(self, crop_bgr: np.ndarray) -> str:
        if not _USE_EASYOCR:
            return "UNREAD"
        reader = self._get_easyocr()
        if reader is None:
            return "UNREAD"
        try:
            results = reader.readtext(crop_bgr, detail=1, paragraph=False)
            if not results:
                return "UNREAD"
            texts = sorted(results, key=lambda x: -x[2])[:3]
            joined = " ".join(t[1].upper().replace(" ", "") for t in texts if t[1])
            return joined[:32] if joined else "UNREAD"
        except Exception as e:
            logger.warning("EasyOCR failed: %s", e)
            return "UNREAD"

    def extract_identity(self, vehicle_crop: Optional[np.ndarray], vehicle_id_seed: int = 0):
        """Return ``license_plate`` and 512-dim ``embedding`` list."""
        if self._backend == "simulated":
            return self._fetch_simulated_identity(vehicle_id_seed)

        if vehicle_crop is None or not isinstance(vehicle_crop, np.ndarray) or vehicle_crop.size == 0:
            logger.debug("No vehicle crop; simulated identity")
            return self._fetch_simulated_identity(vehicle_id_seed)

        if self._backend == "onnx":
            try:
                emb = self._onnx.embed_vehicle(vehicle_crop)
                plate = self._onnx.read_plate(vehicle_crop)
                return {"license_plate": plate, "embedding": emb}
            except Exception as e:
                logger.warning("ONNX identity failed (%s); simulated fallback", e)
                return self._fetch_simulated_identity(vehicle_id_seed)

        # torch
        try:
            emb = self._embedding_torch(vehicle_crop)
            plate = self._plate_easyocr(vehicle_crop)
            return {"license_plate": plate, "embedding": emb}
        except Exception as e:
            logger.warning("Torch identity failed (%s); simulated fallback", e)
            return self._fetch_simulated_identity(vehicle_id_seed)

    def _fetch_simulated_identity(self, seed: int):
        chars = "ABCDEFGHJKLMNPQRSTUVWXYZ"
        nums = "1234567890"
        plate = (
            f"{chars[seed % len(chars)]}{chars[(seed * 2) % len(chars)]} "
            f"{nums[seed % len(nums)]}{nums[(seed * 3) % len(nums)]} {chars[(seed * 4) % len(chars)]}"
        )
        vector_seed = hashlib.sha256(str(seed).encode()).digest()
        embedding = [float(b) / 255.0 for b in vector_seed] * 16
        return {"license_plate": plate, "embedding": embedding[:512]}


if __name__ == "__main__":
    eng = IdentityEngine()
    print(eng.extract_identity(None, vehicle_id_seed=5))
