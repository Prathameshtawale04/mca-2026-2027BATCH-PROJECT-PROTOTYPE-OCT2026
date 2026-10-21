import os
from pathlib import Path
import cv2
import numpy as np

from deep_learning.face.mtcnn_detector import FaceDetector
from deep_learning.face.facenet_model import FaceEmbedding


class FaceVerifier:

    def __init__(self):

        self.detector = FaceDetector()
        self.embedding_model = FaceEmbedding()

    def verify_student( self, frame, student_id,  embedding_folder=None ):

        project_root = Path(__file__).resolve().parents[2]
        embedding_folder = embedding_folder or project_root / "dataset" / "embeddings"

        embedding_path = os.path.join(  str(embedding_folder), f"{student_id}.npy" )

        if not os.path.exists(embedding_path):
            return False, 0.0

        stored_embedding = np.load(embedding_path)
        stored_embedding = stored_embedding / max(float(np.linalg.norm(stored_embedding)), 1e-12)

        faces = self.detector.detect_faces(frame)
        if len(faces) != 1:
            return False, 0.0

        x, y, w, h = faces[0]

        face_image = frame[ y:y+h,  x:x+w ]

        current_embedding = self.embedding_model.get_embedding( face_image  )

        similarity = np.dot( stored_embedding,  current_embedding  )

        if similarity >= 0.75:
            return True, similarity

        return False, similarity
