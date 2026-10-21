from flask import Flask,render_template,redirect
from config import Config
from database import get_connection
from routes.auth import auth
from routes.dashboard import dashboard
from routes.face import face
from routes.profile import profile
from routes.instructions import instructions
from routes.history import history
from routes.exam import exam
from routes.voice import voice

app = Flask(__name__)
app.config.from_object(Config)


app.register_blueprint(auth)
app.register_blueprint(dashboard)
app.register_blueprint(face)
app.register_blueprint(profile)
app.register_blueprint(instructions)
app.register_blueprint(exam)
app.register_blueprint(history)
app.register_blueprint(voice)

@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
