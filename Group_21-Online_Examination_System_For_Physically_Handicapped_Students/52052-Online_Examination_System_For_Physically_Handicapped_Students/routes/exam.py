from flask import Blueprint, render_template, session,request, redirect
from database import get_connection

exam = Blueprint("exam", __name__)


@exam.route("/exam")
def exam_page():

    if "student_id" not in session:
        return redirect("/login")
    if not session.get("exam_face_verified"):
        return redirect("/start_exam")

    connection = get_connection()

    cursor = connection.cursor(dictionary=True)

    cursor.execute(""" SELECT question_id,  question,   option_a,  option_b,   option_c, option_d FROM questions  """)

    questions = cursor.fetchall()

    cursor.close()

    connection.close()

    return render_template("exam.html", questions=questions )

@exam.route("/submit", methods=["POST"])
def submit_exam():

    if "student_id" not in session:
        return redirect("/login")
    if not session.get("exam_face_verified"):
        return redirect("/start_exam")

    connection = get_connection()

    cursor = connection.cursor(dictionary=True)

    cursor.execute(""" SELECT   question_id,   correct_answer  FROM questions """)

    questions = cursor.fetchall()

    score = 0

    total_questions = len(questions)

    for question in questions:

        selected_answer = request.form.get(  f"q{question['question_id']}")


        if selected_answer == question["correct_answer"]:

            score += 1

    percentage = round( (score / total_questions) * 100,  2  )

    cursor.execute( """  INSERT INTO results (  student_id,  score,  total_questions,   percentage )  VALUES  (  %s,  %s, %s, %s )
        """, (  session["student_id"],  score,  total_questions,  percentage ) )

    connection.commit()

    cursor.close()

    connection.close()

    return render_template(   "result.html", score=score,total_questions=total_questions,  percentage=percentage )
