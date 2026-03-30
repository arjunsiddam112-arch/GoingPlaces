from ultralytics import YOLO

# Load pretrained YOLO model
model = YOLO("yolov8n.pt")  # nano model (fast)

# Train model
model.train(
    data="dataset.yaml",
    epochs=50,
    imgsz=640,
    batch=16,
    name="leaf_disease_detector"
)