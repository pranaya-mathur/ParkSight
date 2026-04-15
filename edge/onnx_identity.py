"""
ONNX Runtime inference for vehicle Re-ID (OSNet / vehicle-reid-0001 style) and LPRNet.

Preprocessing matches:
  - Re-ID: Kazuhito00/vehicle-reid-0001-onnx-sample (RGB, 208x208, float32 0–255, NCHW)
  - LPR: hpc203 — ``mnet_plate.onnx`` + warp + ``lprnet.onnx``; ROI resize fallback if MNet finds no chip.
"""
from __future__ import annotations

import logging
import os
from typing import List, Optional

import cv2
import numpy as np

from .plate_pipeline import MNetPlateExtractor

logger = logging.getLogger("onnx-identity")

# Chinese provinces + alnum + blank (same order as hpc203 LPRNet demo)
LPR_CHARS = [
    "京", "沪", "津", "渝", "冀", "晋", "蒙", "辽", "吉", "黑",
    "苏", "浙", "皖", "闽", "赣", "鲁", "豫", "鄂", "湘", "粤",
    "桂", "琼", "川", "贵", "云", "藏", "陕", "甘", "青", "宁",
    "新",
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
    "A", "B", "C", "D", "E", "F", "G", "H", "J", "K",
    "L", "M", "N", "P", "Q", "R", "S", "T", "U", "V",
    "W", "X", "Y", "Z", "I", "O", "-",
]


def default_model_dir() -> str:
    return os.path.join(os.path.dirname(__file__), "models")


class OnnxIdentityRuntime:
    """Loads optional ONNX models from ``edge/models/``."""

    def __init__(self, models_dir: Optional[str] = None):
        self.models_dir = models_dir or default_model_dir()
        self._reid_path = os.path.join(self.models_dir, "vehicle_reid_osnet.onnx")
        self._lpr_path = os.path.join(self.models_dir, "lprnet.onnx")
        self._mnet_path = os.path.join(self.models_dir, "mnet_plate.onnx")
        self._reid_session = None
        self._lpr_session = None
        self._reid_in_name = None
        self._lpr_in_name = None
        self._mnet: Optional[MNetPlateExtractor] = None

    def reid_available(self) -> bool:
        return os.path.isfile(self._reid_path)

    def lpr_available(self) -> bool:
        return os.path.isfile(self._lpr_path)

    def mnet_available(self) -> bool:
        return os.path.isfile(self._mnet_path)

    def _ensure_mnet(self) -> None:
        if self._mnet is not None:
            return
        self._mnet = MNetPlateExtractor(self._mnet_path)
        logger.info("MNet plate detector loaded: %s", self._mnet_path)

    def _ensure_reid(self):
        if self._reid_session is not None:
            return
        import onnxruntime as ort

        self._reid_session = ort.InferenceSession(
            self._reid_path, providers=["CPUExecutionProvider"]
        )
        self._reid_in_name = self._reid_session.get_inputs()[0].name
        logger.info("ONNX vehicle Re-ID loaded: %s", self._reid_path)

    def _ensure_lpr(self):
        if self._lpr_session is not None:
            return
        import onnxruntime as ort

        self._lpr_session = ort.InferenceSession(
            self._lpr_path, providers=["CPUExecutionProvider"]
        )
        self._lpr_in_name = self._lpr_session.get_inputs()[0].name
        logger.info("ONNX LPRNet loaded: %s", self._lpr_path)

    def embed_vehicle(self, crop_bgr: np.ndarray) -> List[float]:
        """512-D embedding, L2-normalized."""
        self._ensure_reid()
        if crop_bgr.dtype != np.uint8:
            crop_bgr = np.clip(crop_bgr, 0, 255).astype(np.uint8)
        h, w = crop_bgr.shape[:2]
        if h < 16 or w < 16:
            raise ValueError("crop too small for Re-ID")
        rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
        rgb = cv2.resize(rgb, (208, 208), interpolation=cv2.INTER_AREA)
        chw = rgb.transpose(2, 0, 1).astype(np.float32)
        batch = np.expand_dims(chw, axis=0)
        out = self._reid_session.run(None, {self._reid_in_name: batch})[0]
        vec = np.array(out[0], dtype=np.float64).flatten()
        n = np.linalg.norm(vec) + 1e-9
        vec = (vec / n).astype(float)
        if vec.size != 512:
            logger.warning("Re-ID output dim is %s, expected 512", vec.size)
        return vec[:512].tolist() if vec.size >= 512 else np.pad(vec, (0, 512 - vec.size)).tolist()

    def _plate_roi(self, crop_bgr: np.ndarray) -> np.ndarray:
        """Heuristic: top portion of vehicle bbox as plate region (no MNet warp)."""
        h, w = crop_bgr.shape[:2]
        y2 = max(1, int(h * 0.38))
        roi = crop_bgr[0:y2, :, :]
        if roi.size == 0:
            roi = crop_bgr
        return cv2.resize(roi, (94, 24), interpolation=cv2.INTER_AREA)

    def _lpr_ctc_decode(self, plate_bgr_94x24: np.ndarray) -> str:
        """Run LPRNet on a 94×24 BGR plate chip."""
        self._ensure_lpr()
        x = plate_bgr_94x24.astype(np.float32)
        x = (x - 127.5) / 128.0
        chw = x.transpose(2, 0, 1)
        batch = np.expand_dims(chw, 0)
        preb = self._lpr_session.run(None, {self._lpr_in_name: batch})[0]
        if preb.ndim == 3:
            preb = preb[0]
        preb_label = np.argmax(preb, axis=0)
        blank = len(LPR_CHARS) - 1
        out_idx: List[int] = []
        pre_c = int(preb_label[0])
        if pre_c != blank:
            out_idx.append(pre_c)
        for c in preb_label[1:]:
            c = int(c)
            if c == pre_c or c == blank:
                if c == blank:
                    pre_c = c
                continue
            out_idx.append(c)
            pre_c = c
        text = "".join(LPR_CHARS[i] for i in out_idx if 0 <= i < len(LPR_CHARS))
        return text.strip("-") or "UNREAD"

    def read_plate(self, crop_bgr: np.ndarray) -> str:
        """MNet + warp + LPRNet when weights exist; else coarse ROI + LPRNet."""
        if not self.lpr_available():
            return "UNREAD"
        chip: Optional[np.ndarray] = None
        if self.mnet_available():
            try:
                self._ensure_mnet()
                chip = self._mnet.extract_warped_plate(crop_bgr)
            except Exception as e:
                logger.warning("MNet plate path failed (%s); ROI fallback", e)
        if chip is None:
            chip = self._plate_roi(crop_bgr)
        try:
            return self._lpr_ctc_decode(chip)
        except Exception as e:
            logger.warning("LPRNet decode failed: %s", e)
            return "UNREAD"
