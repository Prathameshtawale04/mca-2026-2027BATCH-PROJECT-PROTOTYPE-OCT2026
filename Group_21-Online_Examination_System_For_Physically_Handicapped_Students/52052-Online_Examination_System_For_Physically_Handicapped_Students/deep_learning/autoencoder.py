import cv2
import numpy as np
from sklearn.neural_network import MLPRegressor
import joblib
import os
from pathlib import Path

MODEL_PATH = Path(__file__).resolve().with_name("autoencoder_model.pkl")

class AutoEncoderDetector:

    def __init__(self):

        if MODEL_PATH.exists():

            self.model = joblib.load(MODEL_PATH)

        else:

            self.model = MLPRegressor( hidden_layer_sizes=(64, 32, 64),  max_iter=200)

    def preprocess(self, frame):

        image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        image = cv2.resize(image, (32, 32))

        image = image.astype(np.float32) / 255.0

        return image.flatten()

    def train(self, frames):

        data = np.array(  [self.preprocess(f) for f in frames]  )

        self.model.fit(data, data)

        joblib.dump(self.model, MODEL_PATH)

    def detect(self, frame):

        sample = self.preprocess(frame)

        reconstructed = self.model.predict( [sample]  )[0]

        error = np.mean( (sample - reconstructed) ** 2  )

        return error
