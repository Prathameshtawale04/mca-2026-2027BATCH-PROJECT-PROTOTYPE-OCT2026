from flask import Blueprint, render_template, request, redirect, flash,session
from database import get_connection
from werkzeug.security import generate_password_hash, check_password_hash

auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM students WHERE email=%s", (email,))

        student = cursor.fetchone()

        cursor.close()
        conn.close()

        if student:

            if check_password_hash(student["password"], password):

                session["student_id"] = student["student_id"]
                session["student_name"] = student["full_name"]
                session["student_email"] = student["email"]

                return redirect("/dashboard")

            else:
                flash("Incorrect Password")

        else:
            flash("Email not registered")

    return render_template("login.html")


@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form["name"]
        email = request.form["email"]
        mobile = request.form["mobile"]
        gender = request.form["gender"]
        dob = request.form["dob"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        hashed_password = generate_password_hash(password)

        if password != confirm_password:
            flash("Passwords do not match.")
            return redirect("/register")

        conn = get_connection()
        cursor = conn.cursor()


        cursor.execute("SELECT * FROM students WHERE email=%s",  (email,)  )

        student = cursor.fetchone()

        if student:
            flash("Email already registered.")
            cursor.close()
            conn.close()
            return redirect("/register")

        cursor.execute(""" INSERT INTO students  (full_name, email, mobile, gender, dob, password)
            VALUES (%s, %s, %s, %s, %s, %s) """, ( full_name,   email,
            mobile,    gender,    dob, hashed_password ))

        conn.commit()

        cursor.close()
        conn.close()

        flash("Registration Successful. Please Login.")
        return redirect("/login")

    return render_template("register.html")
@auth.route("/logout")
def logout():

    session.clear()

    flash("Logged out successfully.")

    return redirect("/login")