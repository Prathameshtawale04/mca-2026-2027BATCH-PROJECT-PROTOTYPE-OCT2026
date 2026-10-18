from flask import Blueprint, render_template, session, redirect
from database import get_connection

history = Blueprint("history", __name__)


@history.route("/history")
def history_page():

    if "student_id" not in session:
        return redirect("/login")

    connection = get_connection()

    cursor = connection.cursor(dictionary=True)

    cursor.execute("""  SELECT   result_id, score,   total_questions,   percentage, exam_date FROM results
        WHERE student_id=%s  ORDER BY exam_date DESC """, (session["student_id"],))

    history_data = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "history.html",
        results=history_data
    )