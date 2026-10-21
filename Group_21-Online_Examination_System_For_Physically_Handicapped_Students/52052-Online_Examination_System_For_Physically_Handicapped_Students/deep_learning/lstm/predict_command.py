import pickle
from pathlib import Path

import numpy as np

from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences

BASE_DIR = Path(__file__).resolve().parent

model = load_model( BASE_DIR / "lstm_model.keras")

with open( BASE_DIR / "tokenizer.pkl","rb") as file:

    tokenizer = pickle.load(file)

with open( BASE_DIR / "label_encoder.pkl", "rb") as file:

    encoder = pickle.load(file)

with open( BASE_DIR / "max_length.pkl","rb") as file:

    max_length = pickle.load(file)


def predict_command(text):

    sequence = tokenizer.texts_to_sequences( [text.lower()] )

    sequence = pad_sequences(   sequence,  maxlen=max_length )

    prediction = model.predict( sequence, verbose=0 )

    index = np.argmax( prediction )

    command = encoder.inverse_transform( [index] )[0]

    confidence = float(   np.max(prediction) )

    return command, confidence