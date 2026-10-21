import os
from pathlib import Path
import cv2
import numpy as np

from deep_learning.face.mtcnn_detector import FaceDetector
from deep_learning.face.facenet_model import FaceEmbedding


class FaceRegistration:

    def __init__(self):

        self.detector = FaceDetector()
        self.embedding_model = FaceEmbedding()

    def register_student(  self, student_id, dataset_folder=None,  embedding_folder=None ):

        project_root = Path(__file__).resolve().parents[2]
        dataset_folder = Path(dataset_folder or project_root / "dataset" / "students")
        embedding_folder = Path(embedding_folder or project_root / "dataset" / "embeddings")

        student_folder = os.path.join(  str(dataset_folder),  str(student_id)  )

        if not os.path.exists(student_folder):
            return False, "Student images not found."

        os.makedirs(  embedding_folder,  exist_ok=True  )

        embeddings = []

        for image_name in sorted(os.listdir(student_folder)):

            image_path = os.path.join( student_folder,   image_name   )

            image = cv2.imread(image_path)

            if image is None:
                continue

            faces = self.detector.detect_faces(image)
            if len(faces) != 1:
                continue

            x, y, w, h = faces[0]

            face_image = image[y:y+h, x:x+w]

            embedding = self.embedding_model.get_embedding( face_image )

            embeddings.append(embedding)

        if len(embeddings) < 20:
            return False, "Not enough valid face images."

        average_embedding = np.mean(embeddings, axis=0 )

        embedding_path = os.path.join( str(embedding_folder), f"{student_id}.npy"  )

        np.save( embedding_path, average_embedding )

        return True, "Face registered successfully."
