from flask import Blueprint, render_template, session, redirect
from database import get_connection

profile = Blueprint("profile", __name__)


@profile.route("/profile")
def profile_page():

    if "student_id" not in session:
        return redirect("/login")

    connection = get_connection()

    cursor = connection.cursor(dictionary=True)

    cursor.execute(   "SELECT * FROM students WHERE student_id=%s",    (session["student_id"],) )

    student = cursor.fetchone()

    cursor.close()
    connection.close()

    return render_template(
        "profile.html",
        student=student
    )