from flask import Blueprint, render_template, session, redirect

instructions = Blueprint("instructions", __name__)

@instructions.route("/instructions")
def instructions_page():

    if "student_id" not in session:
        return redirect("/login")

    return render_template("instructions.html")