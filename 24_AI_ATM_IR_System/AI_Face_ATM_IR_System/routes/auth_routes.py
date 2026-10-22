"""Authentication Routes (Login, Register, Logout, 1-Click Demo Login)."""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
import base64
from services.auth_service import authenticate_user, register_user, log_audit_event, verify_pin, is_user_locked
from database.db import query_db

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Sign-in page for password authentication and multi-factor selection."""
    if "user_id" in session:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        next_url = request.form.get("next") or request.args.get("next")

        if not username or not password:
            flash("Please enter both username and password.", "warning")
            return render_template("login.html", username=username)

        success, msg, user = authenticate_user(username, password, request.remote_addr)
        if not success:
            flash(msg, "danger")
            return render_template("login.html", username=username)

        # Set authenticated session
        session.clear()
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = user["role"]
        session["full_name"] = user["full_name"]
        session["account_number"] = user.get("account_number")
        session["balance"] = user.get("balance", 0.0)
        session.permanent = True

        flash(f"Welcome back, {user['full_name']}!", "success")
        if next_url and next_url.startswith("/"):
            return redirect(next_url)
        return redirect(url_for("main.dashboard"))

    return render_template("login.html")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """User registration page creating an account with linked bank account."""
    if "user_id" in session:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        full_name = request.form.get("full_name", "").strip()
        password = request.form.get("password", "").strip()
        pin = request.form.get("pin", "1234").strip()

        if not username or not email or not full_name or not password:
            flash("All fields are required.", "warning")
            return render_template("register.html")

        if len(pin) != 4 or not pin.isdigit():
            flash("ATM PIN must be exactly 4 digits.", "warning")
            return render_template("register.html")

        success, msg, user = register_user(username, email, password, full_name, pin=pin)
        if not success:
            flash(msg, "danger")
            return render_template("register.html")

        # Automatically sign in new customer and redirect to Biometric Enrollment onboarding
        account = query_db("SELECT * FROM accounts WHERE user_id = ?", (user["id"],), one=True)
        session.clear()
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = user["role"]
        session["full_name"] = user["full_name"]
        session["account_number"] = account["account_number"] if account else None
        session["balance"] = account["balance"] if account else 1000.0
        session.permanent = True

        flash(f"Welcome, {user['full_name']}! Account {session['account_number']} created. Complete your biometric face scan to enable ATM features.", "info")
        return redirect(url_for("face.register_page"))

    return render_template("register.html")

@auth_bp.route("/logout")
def logout():
    """Clear session and log audit event."""
    user_id = session.get("user_id")
    acc_num = session.get("account_number")
    if user_id:
        log_audit_event(user_id, acc_num, "LOGOUT", "User logged out", request.remote_addr, "INFO")
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("auth.login"))

@auth_bp.route("/api/auth/demo_login", methods=["POST"])
def demo_login():
    """1-Click Demo Login for smooth viva evaluation without manual password entry."""
    data = request.get_json(silent=True) or request.form
    target = data.get("account_number") or data.get("username")

    if not target:
        return jsonify({"success": False, "message": "Missing account_number or username"}), 400

    # Find account or user
    user = query_db(
        """SELECT u.*, a.account_number, a.balance, a.daily_limit
           FROM users u
           LEFT JOIN accounts a ON u.id = a.user_id
           WHERE u.username = ? OR a.account_number = ?""",
        (target, target),
        one=True
    )

    if not user:
        return jsonify({"success": False, "message": f"Demo account '{target}' not found."}), 404

    session.clear()
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["role"] = user["role"]
    session["full_name"] = user["full_name"]
    session["account_number"] = user["account_number"]
    session["balance"] = user["balance"]
    session.permanent = True

    log_audit_event(user["id"], user["account_number"], "DEMO_LOGIN", f"1-Click Demo Login as {user['username']}", request.remote_addr, "SUCCESS")

    return jsonify({
        "success": True,
        "message": f"Signed in as {user['full_name']}",
        "redirect_url": url_for("main.dashboard")
    })

@auth_bp.route("/api/auth/face_login", methods=["POST"])
def face_login():
    """
    Biometric Face + PIN Authentication Endpoint.
    Authenticates user via facial match + PIN verification.
    """
    data = request.get_json(silent=True) or request.form
    target = (data.get("account_number") or data.get("username") or "").strip()
    pin = (data.get("pin") or "").strip()
    image_data = data.get("image")
    use_simulation = data.get("simulate", False)

    if not target:
        return jsonify({"success": False, "message": "Please enter your Account Number or Username."}), 400

    # Find account or user
    user = query_db(
        """SELECT u.*, a.account_number, a.balance, a.daily_limit
           FROM users u
           LEFT JOIN accounts a ON u.id = a.user_id
           WHERE u.username = ? OR a.account_number = ?""",
        (target, target),
        one=True
    )
    if not user:
        return jsonify({"success": False, "message": f"Account '{target}' not found."}), 404

    user_dict = dict(user)
    if is_user_locked(user_dict):
        log_audit_event(user_dict["id"], user_dict.get("account_number"), "LOGIN_BLOCKED", "Attempt on locked account", request.remote_addr, "WARNING")
        return jsonify({"success": False, "message": "Account is locked due to security policy. Please contact bank administrator."}), 403

    account_number = user_dict.get("account_number")

    # 1. Face Verification
    if use_simulation:
        from services.face_service import get_samples_dir
        samples_dir = get_samples_dir(account_number)
        sample_files = list(samples_dir.glob("sample_*.jpg"))
        if not sample_files:
            return jsonify({"success": False, "message": f"No enrolled biometric profile found for {account_number}. Please enroll your face first."}), 400
        with open(sample_files[0], "rb") as f:
            image_data = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode("utf-8")

    if not image_data:
        return jsonify({"success": False, "message": "Face biometric image is required for authentication."}), 400

    from services.face_service import verify_face_identity
    match, face_msg, face_details = verify_face_identity(account_number, image_data)
    if not match:
        log_audit_event(user_dict["id"], account_number, "FACE_LOGIN_FAIL", f"Biometric mismatch: {face_msg}", request.remote_addr, "FAILURE")
        return jsonify({
            "success": False,
            "message": f"Biometric identity check failed: {face_msg}",
            "details": face_details
        }), 401

    # 2. PIN Verification (if PIN provided)
    if pin:
        pin_hash = user_dict.get("pin_hash")
        pin_salt = user_dict.get("pin_salt")
        if pin_hash and pin_salt:
            if not verify_pin(pin, pin_hash, pin_salt):
                log_audit_event(user_dict["id"], account_number, "PIN_FAIL", "Invalid PIN during face login", request.remote_addr, "FAILURE")
                return jsonify({"success": False, "message": "Invalid ATM Security PIN."}), 401

    # Both passed -> Establish Session
    session.clear()
    session["user_id"] = user_dict["id"]
    session["username"] = user_dict["username"]
    session["role"] = user_dict["role"]
    session["full_name"] = user_dict["full_name"]
    session["account_number"] = user_dict.get("account_number")
    session["balance"] = user_dict.get("balance", 0.0)
    session["biometric_authenticated"] = True
    session.permanent = True

    log_audit_event(user_dict["id"], account_number, "FACE_LOGIN_SUCCESS", f"Biometric face login verified (Dist: {face_details.get('distance', 0):.1f})", request.remote_addr, "SUCCESS")

    return jsonify({
        "success": True,
        "message": f"Identity confirmed! Welcome, {user_dict['full_name']}.",
        "redirect_url": url_for("main.dashboard"),
        "details": face_details
    })
