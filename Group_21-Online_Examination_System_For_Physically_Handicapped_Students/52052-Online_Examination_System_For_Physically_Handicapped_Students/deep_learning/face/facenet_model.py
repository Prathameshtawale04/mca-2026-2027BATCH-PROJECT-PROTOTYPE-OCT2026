import cv2
import numpy as np
from keras_facenet import FaceNet

model = FaceNet()


class FaceEmbedding:

    def __init__(self):
        self.model = model

    def get_embedding(self, face_image):

        face_image = cv2.cvtColor( face_image,cv2.COLOR_BGR2RGB)

        face_image = cv2.resize(  face_image,(160, 160) )

        face_image = face_image.astype("float32")

        face_image = np.expand_dims( face_image, axis=0  )

        embedding = self.model.embeddings( face_image )[0]

        embedding = embedding / np.linalg.norm( embedding  )

        return embedding