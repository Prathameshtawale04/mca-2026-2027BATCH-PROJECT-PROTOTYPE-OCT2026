from mtcnn import MTCNN
import cv2


class FaceDetector:

    def __init__(self):

        self.detector = MTCNN()


    def detect_faces(self, frame, min_confidence=0.90):
        if frame is None or frame.size == 0:
            return []

        rgb_frame = cv2.cvtColor( frame, cv2.COLOR_BGR2RGB  )

        detections = self.detector.detect_faces( rgb_frame  )

        height, width = frame.shape[:2]
        faces = []
        for detection in detections:
            if detection.get("confidence", 0) < min_confidence:
                continue
            x, y, box_width, box_height = detection["box"]
            left, top = max(0, x), max(0, y)
            right, bottom = min(width, x + box_width), min(height, y + box_height)
            if right > left and bottom > top:
                faces.append((left, top, right - left, bottom - top))
        return faces

    def detect_face(self, frame):
        faces = self.detect_faces(frame)
        return faces[0] if len(faces) == 1 else None
