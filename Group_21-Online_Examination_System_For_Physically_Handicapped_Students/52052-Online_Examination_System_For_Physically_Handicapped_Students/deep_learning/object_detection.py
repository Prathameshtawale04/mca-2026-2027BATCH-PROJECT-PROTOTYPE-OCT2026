from ultralytics import YOLO
from pathlib import Path

MODEL_PATH = Path(__file__).resolve().parents[1] / "yolov8n.pt"
model = YOLO(str(MODEL_PATH))


TARGET_OBJECTS = {  "person", "book", "cell phone",  "tablet", "laptop",  "tv", "mobile"}

def detect_objects(frame):

    if frame is None or frame.size == 0:
        return {"objects": [], "detections": [], "suspicious": False}

    results = model(frame, verbose=False, conf=0.12, imgsz=960)

    detected = []
    detections = []
    suspicious = False

    person_count = 0
    for result in results:

        for box in result.boxes:

            class_id = int(box.cls[0])

            label = model.names[class_id]
            if label not in TARGET_OBJECTS:
                continue

            confidence = float(box.conf[0])
            if confidence < 0.12:
                continue

            detected.append(label)
            display_label = "Phone / tablet" if label == "cell phone" else label.title()
            x1, y1, x2, y2 = [int(value) for value in box.xyxy[0].tolist()]
            detections.append({ "label": display_label, "confidence": round(confidence, 3),  "box": [x1, y1, x2, y2],
                "kind": "object"   })

            if label == "cell phone" and confidence >= 0.45:

                suspicious = True

            if label == "person" and confidence >= 0.50:
                person_count += 1


    if person_count > 1:

        suspicious = True

        detected.append("Multiple Persons")

    return {"objects": detected,  "detections": detections, "suspicious": suspicious }
