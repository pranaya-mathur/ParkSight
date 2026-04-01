import os
from ultralytics import YOLO

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
