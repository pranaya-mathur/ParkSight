import os
import urllib.request

from ultralytics import YOLO

# Vehicle Re-ID (OSNet, MIT) — Kazuhito00 sample repo
VEHICLE_REID_ONNX_URL = (
    "https://raw.githubusercontent.com/Kazuhito00/vehicle-reid-0001-onnx-sample/main/"
    "vehicle_reid_0001/model/osnet_ain_x1_0_vehicle_reid_optimized.onnx"
)
# LPRNet ONNX — hpc203 OpenCV demo repo
LPRNET_ONNX_URL = (
    "https://raw.githubusercontent.com/hpc203/license-plate-detect-recoginition-opencv/main/"
    "Final_LPRNet_model.onnx"
)
MNET_PLATE_ONNX_URL = (
    "https://raw.githubusercontent.com/hpc203/license-plate-detect-recoginition-opencv/main/"
    "mnet_plate.onnx"
)


def _download_file(url: str, dest: str) -> None:
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        print(f"✅ Already present: {dest}")
        return
    print(f"⬇️ Downloading {url} -> {dest}")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    urllib.request.urlretrieve(url, dest)
    print(f"✅ Saved {dest} ({os.path.getsize(dest) // 1024} KB)")


def download_identity_onnx_models():
    """OSNet vehicle Re-ID + LPRNet ONNX into edge/models/ (for IdentityEngine auto/onnx)."""
    base = os.path.join(os.getcwd(), "edge", "models")
    _download_file(VEHICLE_REID_ONNX_URL, os.path.join(base, "vehicle_reid_osnet.onnx"))
    _download_file(LPRNET_ONNX_URL, os.path.join(base, "lprnet.onnx"))
    _download_file(MNET_PLATE_ONNX_URL, os.path.join(base, "mnet_plate.onnx"))


def download_yolo_models():
    """Download official YOLO11 and YOLOv5 models for detection.
    YOLO11 is preferred for high-accuracy and NMS-free performance.
    """
    models = ["yolo11n.pt", "yolov8n.pt"] # Support both for fallback
    
    target_dir = os.path.join(os.getcwd(), "edge")
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        
    print(f"📦 Downloading models to {target_dir}...")
    
    for model_name in models:
        model_path = os.path.join(target_dir, model_name)
        if not os.path.exists(model_path):
            print(f"⬇️ Downloading {model_name}...")
            model = YOLO(model_name) # This triggers an auto-download from Ultralytics
            # Weights are usually in root, let's move them if they aren't where we want
            if os.path.exists(model_name):
                os.rename(model_name, model_path)
            print(f"✅ {model_name} ready.")
        else:
            print(f"✅ {model_name} already exists.")

if __name__ == "__main__":
    download_yolo_models()
    download_identity_onnx_models()
