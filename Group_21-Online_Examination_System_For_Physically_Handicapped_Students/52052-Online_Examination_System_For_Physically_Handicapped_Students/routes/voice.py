from flask import Blueprint
from flask import request
from flask import jsonify

from deep_learning.lstm.predict_command import predict_command

voice = Blueprint( "voice", __name__)


@voice.route("/predict_voice_command", methods=["POST"])
def predict_voice():

    data = request.get_json()

    text = data["text"]

    command, confidence = predict_command(text)

    return jsonify({  "command": command, "confidence": confidence  })