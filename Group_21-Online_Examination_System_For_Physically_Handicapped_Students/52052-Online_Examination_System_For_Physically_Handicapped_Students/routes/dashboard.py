from flask import Blueprint, session, redirect,render_template,flash
from database import get_connection
from deep_learning.monitoring.warning_manager import WarningManager

dashboard = Blueprint("dashboard", __name__)


@dashboard.route("/dashboard")
def dashboard_page():

    if "student_id" not in session:
        return redirect("/login")

    connection = get_connection()

    cursor = connection.cursor(dictionary=True)

    cursor.execute(  """  SELECT face_registered   FROM students  WHERE student_id = %s  """,
        (session["student_id"],)  )

    student = cursor.fetchone()

    cursor.close()
    connection.close()

    return render_template("dashboard.html",student_name=session["student_name"],face_registered=student["face_registered"]
    )
@dashboard.route("/start_exam")
def start_exam():

    if "student_id" not in session:
        return redirect("/login")

    connection = get_connection()

    cursor = connection.cursor(dictionary=True)

    cursor.execute( """ SELECT face_registered FROM students WHERE student_id = %s  """,    (session["student_id"],))

    student = cursor.fetchone()

    cursor.close()
    connection.close()

    if not student["face_registered"]:
        return redirect("/face_registration")

    return redirect("/instructions")

@dashboard.route("/verify_face")
def verify_face():

    if "student_id" not in session:
        return redirect("/login")

    WarningManager.reset_student(session["student_id"])
    session.pop("exam_face_verified", None)
    return render_template("verify_face.html")
