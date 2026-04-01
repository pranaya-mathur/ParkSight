import os
import sys
from ultralytics import YOLO

def download_yolo_weights(model_name="yolo26n.pt"):
    """Downloads the real YOLO weights for the ParkSight Edge Perception."""
    
    print(f"📡 Initializing download for {model_name}...")
    
    # Path to the edge directory
    target_dir = os.path.join(os.path.dirname(__file__), "edge")
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    target_path = os.path.join(target_dir, model_name)
    
    try:
        # This will download the model to the current directory and then we move it
        model = YOLO(model_name)
        print(f"✅ Successfully downloaded {model_name}")
        
        # Verify the model can be loaded
        print(f"🔎 Validating model architecture...")
        print(model.info())
        
        print(f"📦 Model ready at {target_path}")
        
    except Exception as e:
        print(f"❌ Error downloading model: {str(e)}")
        print("💡 Tip: Ensure you have an active internet connection and 'ultralytics' installed.")

if __name__ == "__main__":
    # You can specify a different model name if needed, e.g., 'yolov8n.pt'
    model = sys.argv[1] if len(sys.argv) > 1 else "yolo26n.pt"
    download_yolo_weights(model)
