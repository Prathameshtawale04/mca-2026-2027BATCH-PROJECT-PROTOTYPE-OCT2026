import pandas as pd
import pickle

from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences

from tensorflow.keras.models import Sequential

from tensorflow.keras.layers import Embedding
from tensorflow.keras.layers import LSTM
from tensorflow.keras.layers import Dense

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

csv_path = BASE_DIR / "dataset" / "voice_commands" / "commands.csv"

data = pd.read_csv(csv_path)

texts = data["command"]

labels = data["label"]

tokenizer = Tokenizer()

tokenizer.fit_on_texts(texts)

sequences = tokenizer.texts_to_sequences(texts)

max_length = max(

    len(sequence)

    for sequence in sequences

)

X = pad_sequences(

    sequences,

    maxlen=max_length

)

encoder = LabelEncoder()

y = encoder.fit_transform(labels)

model = Sequential()

model.add(Embedding(input_dim=len(tokenizer.word_index)+1, output_dim=32,   input_length=max_length ))

model.add( LSTM(64))

model.add( Dense( len(encoder.classes_),  activation="softmax"  ))

model.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])

model.fit( X, y, epochs=200,  verbose=1)

model.save(BASE_DIR / "deep_learning" / "lstm" / "lstm_model.keras")

with open( BASE_DIR / "deep_learning" / "lstm" / "tokenizer.pkl","wb") as file:

    pickle.dump( tokenizer,  file )

with open( BASE_DIR / "deep_learning" / "lstm" / "label_encoder.pkl","wb") as file:

    pickle.dump(encoder,  file  )

with open( BASE_DIR / "deep_learning" / "lstm" / "max_length.pkl", "wb") as file:

    pickle.dump( max_length,  file )

print( "LSTM Model Trained Successfully")