"""
MNet plate detection + perspective warp (hpc203 license-plate-detect-recoginition-opencv),
without the full ``detect_rec`` loop — returns a single best 94×24 BGR plate chip for LPRNet.

Uses one DNN forward, then a **score cascade** (strict → lenient) so tight vehicle crops
still yield a warp when class scores are low (common on full-frame scenes).
"""
from __future__ import annotations

import logging
import os
from itertools import product
from math import ceil
from typing import List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger("plate-pipeline")

# Extra (conf, vis) pairs after the caller’s primary thresholds — same decode/NMS/warp math.
_DEFAULT_CASCADE: List[Tuple[float, float]] = [
    (0.12, 0.18),
    (0.06, 0.10),
    (0.03, 0.05),
    (0.015, 0.028),
    (0.008, 0.014),
    (0.004, 0.008),
    (0.002, 0.004),
    (0.001, 0.0018),
    (0.0006, 0.0011),
]


class MNetPlateExtractor:
    """Retinaface-style MNet on 640×640 letterbox; warp plate to 94×24."""

    def __init__(
        self,
        model_path: str,
        confidence_threshold: float = 0.22,
        top_k: int = 5000,
        nms_threshold: float = 0.45,
        keep_top_k: int = 750,
        vis_thres: float = 0.30,
        extra_cascade: Optional[List[Tuple[float, float]]] = None,
    ):
        if not os.path.isfile(model_path):
            raise FileNotFoundError(model_path)
        self.model_path = model_path
        self.model = cv2.dnn.readNet(model_path)
        self.im_height = 640
        self.im_width = 640
        self.scale = np.array([[self.im_width, self.im_height]], dtype=np.float32)
        self.confidence_threshold = confidence_threshold
        self.top_k = top_k
        self.nms_threshold = nms_threshold
        self.keep_top_k = keep_top_k
        self.vis_thres = vis_thres
        self._cascade: List[Tuple[float, float]] = [
            (confidence_threshold, vis_thres),
            *list(extra_cascade or _DEFAULT_CASCADE),
        ]
        self.min_sizes = [[24, 48], [96, 192], [384, 768]]
        self.steps = [8, 16, 32]
        self.variance = [0.1, 0.2]
        self.clip = False
        self.prior_data = self._generate_priors()
        self.points_ref = np.float32([[0, 0], [94, 0], [0, 24], [94, 24]])

    def _generate_priors(self) -> np.ndarray:
        feature_maps = [[ceil(self.im_height / s), ceil(self.im_width / s)] for s in self.steps]
        anchors = []
        for k, f in enumerate(feature_maps):
            min_sizes = self.min_sizes[k]
            for i, j in product(range(f[0]), range(f[1])):
                for min_size in min_sizes:
                    s_kx = min_size / self.im_width
                    s_ky = min_size / self.im_height
                    dense_cx = [x * self.steps[k] / self.im_width for x in [j + 0.5]]
                    dense_cy = [y * self.steps[k] / self.im_height for y in [i + 0.5]]
                    for cy, cx in product(dense_cy, dense_cx):
                        anchors += [cx, cy, s_kx, s_ky]
        output = np.asarray(anchors, dtype=np.float32).reshape(-1, 4)
        if self.clip:
            output = np.clip(output, 0, 1)
        return output

    @staticmethod
    def _decode(loc: np.ndarray, priors: np.ndarray, variances) -> np.ndarray:
        boxes = np.concatenate(
            (
                priors[:, :2] + loc[:, :2] * variances[0] * priors[:, 2:],
                priors[:, 2:] * np.exp(loc[:, 2:] * variances[1]),
            ),
            axis=1,
        )
        boxes[:, :2] -= boxes[:, 2:] / 2
        return boxes

    @staticmethod
    def _decode_landm(pre: np.ndarray, priors: np.ndarray, variances) -> np.ndarray:
        landms = np.concatenate(
            (
                priors[:, :2] + pre[:, :2] * variances[0] * priors[:, 2:],
                priors[:, :2] + pre[:, 2:4] * variances[0] * priors[:, 2:],
                priors[:, :2] + pre[:, 4:6] * variances[0] * priors[:, 2:],
                priors[:, :2] + pre[:, 6:8] * variances[0] * priors[:, 2:],
            ),
            axis=1,
        )
        return landms

    def _resize_image(self, srcimg: np.ndarray):
        top, left, newh, neww = 0, 0, self.im_height, self.im_width
        if srcimg.shape[0] != srcimg.shape[1]:
            hw_scale = srcimg.shape[0] / srcimg.shape[1]
            if hw_scale > 1:
                newh, neww = self.im_height, int(self.im_width / hw_scale)
                img = cv2.resize(srcimg, (neww, newh), interpolation=cv2.INTER_AREA)
                left = int((self.im_width - neww) * 0.5)
                img = cv2.copyMakeBorder(
                    img, 0, 0, left, self.im_width - neww - left, cv2.BORDER_CONSTANT, value=0
                )
            else:
                newh, neww = int(self.im_height * hw_scale), self.im_width
                img = cv2.resize(srcimg, (neww, newh), interpolation=cv2.INTER_AREA)
                top = int((self.im_height - newh) * 0.5)
                img = cv2.copyMakeBorder(
                    img, top, self.im_height - newh - top, 0, 0, cv2.BORDER_CONSTANT, value=0
                )
        else:
            img = cv2.resize(srcimg, (self.im_width, self.im_height), interpolation=cv2.INTER_AREA)
        return img, newh, neww, top, left

    def extract_warped_plate(self, srcimg: np.ndarray) -> Optional[np.ndarray]:
        """
        Run MNet on ``srcimg`` (e.g. full vehicle crop), return best 94×24 BGR warped plate or None.
        """
        if srcimg is None or srcimg.size == 0 or srcimg.ndim != 3:
            return None
        if srcimg.shape[0] < 16 or srcimg.shape[1] < 32:
            return None

        img, newh, neww, top, left = self._resize_image(srcimg)
        blob = cv2.dnn.blobFromImage(img, mean=(104, 117, 123))
        self.model.setInput(blob)
        loc, conf, landms = self.model.forward(["loc", "conf", "landms"])

        loc = np.squeeze(loc, axis=0) if loc.ndim == 3 else loc
        conf = np.squeeze(conf, axis=0) if conf.ndim == 3 else conf
        landms = np.squeeze(landms, axis=0) if landms.ndim == 3 else landms

        boxes640 = self._decode(loc, self.prior_data, self.variance)
        boxes640 = boxes640 * np.tile(self.scale, (1, 2))
        scores = conf[:, 1].astype(np.float32)
        landms640 = self._decode_landm(landms, self.prior_data, self.variance)
        landms640 = landms640 * np.tile(self.scale, (1, 4))

        best_warped = None
        best_score = -1.0

        for conf_th, vis_th in self._cascade:
            inds = np.where(scores > conf_th)[0]
            if inds.size == 0:
                continue
            boxes = boxes640[inds].copy()
            scs = scores[inds].copy()
            lands = landms640[inds].copy()

            nms_out = cv2.dnn.NMSBoxes(
                boxes.tolist(),
                scs.tolist(),
                float(conf_th),
                float(self.nms_threshold),
                top_k=int(self.keep_top_k),
            )
            if nms_out is None or len(nms_out) == 0:
                continue
            idx_arr = np.asarray(nms_out, dtype=np.int32).reshape(-1)

            boxes = boxes - np.array([[left, top, 0, 0]], dtype=np.float32)
            lands = lands - np.tile(np.array([[left, top]], dtype=np.float32), (1, 4))
            srcim_scale = np.array([[srcimg.shape[1] / neww, srcimg.shape[0] / newh]], dtype=np.float32)
            boxes = boxes * np.tile(srcim_scale, (1, 2))
            lands = lands * np.tile(srcim_scale, (1, 4))

            for flat in idx_arr:
                idx = int(flat)
                if idx < 0 or idx >= len(scs):
                    continue
                sc = float(scs[idx])
                if sc < vis_th:
                    continue
                xmin, ymin, width, height = boxes[idx, :].astype(float)
                new_x1 = lands[idx, 4] - xmin
                new_y1 = lands[idx, 5] - ymin
                new_x2 = lands[idx, 6] - xmin
                new_y2 = lands[idx, 7] - ymin
                new_x3 = lands[idx, 2] - xmin
                new_y3 = lands[idx, 3] - ymin
                new_x4 = lands[idx, 0] - xmin
                new_y4 = lands[idx, 1] - ymin
                points = np.float32(
                    [[new_x1, new_y1], [new_x2, new_y2], [new_x3, new_y3], [new_x4, new_y4]]
                )
                try:
                    M = cv2.getPerspectiveTransform(points, self.points_ref)
                except cv2.error:
                    continue
                yi1, yi2 = int(ymin), int(ymin + height)
                xi1, xi2 = int(xmin), int(xmin + width)
                yi1, yi2 = max(0, yi1), min(srcimg.shape[0], yi2)
                xi1, xi2 = max(0, xi1), min(srcimg.shape[1], xi2)
                if yi2 <= yi1 or xi2 <= xi1:
                    continue
                img_box = srcimg[yi1:yi2, xi1:xi2, :]
                if img_box.size == 0:
                    continue
                try:
                    processed = cv2.warpPerspective(img_box, M, (94, 24))
                except cv2.error:
                    continue
                if sc > best_score:
                    best_score = sc
                    best_warped = processed

            if best_warped is not None:
                break

        if best_warped is None:
            logger.debug("MNet: no plate chip after cascade (max_score=%.4f)", float(scores.max()))
        return best_warped
