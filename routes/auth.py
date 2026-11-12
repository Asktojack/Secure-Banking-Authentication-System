import random


from utils.otp import generate_otp
from utils.authenticator import verify_authenticator
from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, flash
from utils.database import get_connection
from utils.password import hash_password, verify_password
from utils.otp import generate_otp
from utils.mail import send_email
from utils.risk import calculate_risk
from utils.device import detect_device
from datetime import datetime, timedelta

auth = Blueprint("auth", __name__)

# ==========================
# REGISTER
# ==========================
@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form["full_name"]
        username = request.form["username"]
        email = request.form["email"]
        mobile = request.form["mobile"]
        password = hash_password(request.form["password"])

        # Get authentication pattern selected by user
        auth_step1 = request.form["auth_step1"]
        auth_step2 = request.form["auth_step2"]
        auth_step3 = request.form["auth_step3"]

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Check Username
        cursor.execute(
            "SELECT * FROM users WHERE username=%s",
            (username,)
        )
        existing_user = cursor.fetchone()

        if existing_user:
            cursor.close()
            conn.close()
            return "<h2>Username already exists!</h2>"

        # Check Email
        cursor.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )
        existing_email = cursor.fetchone()

        if existing_email:
            cursor.close()
            conn.close()
            return "<h2>Email already exists!</h2>"

        # Insert user + authentication pattern
        sql = """
        INSERT INTO users
        (
            full_name,
            username,
            email,
            mobile,
            password,
            auth_step1,
            auth_step2,
            auth_step3
        )
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
        """

        values = (
            full_name,
            username,
            email,
            mobile,
            password,
            auth_step1,
            auth_step2,
            auth_step3
        )

        cursor.execute(sql, values)
        conn.commit()

        cursor.close()
        conn.close()

        return redirect(url_for("auth.login"))

    return render_template("register.html")

# ==========================
# LOGIN
# ==========================
@auth.route("/login", methods=["GET", "POST"])
def login():

    print("LOGIN ROUTE CALLED")
    print("REQUEST METHOD:", request.method)
    print("FORM DATA:", request.form)

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        print("LOGIN: Username received:", username)

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # ==========================================
        # FIND USER
        # ==========================================

        cursor.execute(
            "SELECT * FROM users WHERE username=%s",
            (username,)
        )

        user = cursor.fetchone()

        if not user:

            cursor.close()
            conn.close()

            return "<h2>User Not Found</h2>"

        # ==========================================
        # CHECK ACCOUNT LOCK
        # ==========================================

        if user["account_locked"] == 1:

            lock_time = user["lock_time"]

            if lock_time:

                unlock_time = lock_time + timedelta(minutes=10)

                if datetime.now() >= unlock_time:

                    cursor.execute(
                        """
                        UPDATE users
                        SET
                            failed_attempts = 0,
                            account_locked = 0,
                            lock_time = NULL
                        WHERE id = %s
                        """,
                        (user["id"],)
                    )

                    conn.commit()

                    user["failed_attempts"] = 0
                    user["account_locked"] = 0
                    user["lock_time"] = None

                else:

                    remaining = unlock_time - datetime.now()

                    minutes = remaining.seconds // 60
                    seconds = remaining.seconds % 60

                    cursor.close()
                    conn.close()

                    return f"""
                    <h2>
                    Your account is locked.<br><br>
                    Try again after {minutes} minute(s) {seconds} second(s).
                    </h2>
                    """

        # ==========================================
        # VERIFY PASSWORD
        # ==========================================

        if verify_password(user["password"], password):

            print("PASSWORD CORRECT")

            # ==========================================
            # RESET FAILED ATTEMPTS
            # ==========================================

            cursor.execute(
                """
                UPDATE users
                SET
                    failed_attempts = 0,
                    account_locked = 0,
                    lock_time = NULL
                WHERE id=%s
                """,
                (user["id"],)
            )

            conn.commit()

            # ==========================================
            # SAVE LOGIN HISTORY
            # ==========================================

            ip = request.remote_addr
            user_agent = request.headers.get("User-Agent")

            cursor.execute(
                """
                INSERT INTO login_history
                (user_id, ip_address, device, browser, status)
                VALUES (%s,%s,%s,%s,%s)
                """,
                (
                    user["id"],
                    ip,
                    str(user_agent),
                    str(user_agent),
                    "Success"
                )
            )

            conn.commit()

            # ==========================================
            # SAVE NOTIFICATION
            # ==========================================

            cursor.execute(
                """
                INSERT INTO notifications
                (user_id, message)
                VALUES (%s,%s)
                """,
                (
                    user["id"],
                    "Login Successful"
                )
            )

            conn.commit()

            # ==========================================
            # SAVE LOGIN SESSION
            # ==========================================

            session["username"] = username
            session["user_id"] = user["id"]
            session["user_email"] = user["email"]

            # ==========================================
            # SAVE REGISTERED AUTHENTICATION PATTERN
            # ==========================================

            session["auth_step1"] = user["auth_step1"]
            session["auth_step2"] = user["auth_step2"]
            session["auth_step3"] = user["auth_step3"]

            print("================================")
            print("REGISTERED AUTHENTICATION PATTERN")
            print("STEP 1:", user["auth_step1"])
            print("STEP 2:", user["auth_step2"])
            print("STEP 3:", user["auth_step3"])
            print("================================")

            cursor.close()
            conn.close()

            # ==========================================
            # IMPORTANT:
            # DO NOT START OTP YET
            #
            # First ask user to select pattern
            # ==========================================

            return redirect(
                url_for("auth.select_pattern")
            )

        # ==========================================
        # WRONG PASSWORD
        # ==========================================

        else:

            print("PASSWORD INCORRECT")

            attempts = user["failed_attempts"] + 1

            if attempts >= 5:

                cursor.execute(
                    """
                    UPDATE users
                    SET
                        failed_attempts=5,
                        account_locked=1,
                        lock_time=NOW()
                    WHERE id=%s
                    """,
                    (user["id"],)
                )

                conn.commit()

                cursor.execute(
                    """
                    INSERT INTO notifications
                    (user_id, message)
                    VALUES (%s,%s)
                    """,
                    (
                        user["id"],
                        "Your account has been locked after 5 failed login attempts."
                    )
                )

                conn.commit()

                cursor.close()
                conn.close()

                return """
                <h2>
                Account Locked after 5 failed attempts.
                </h2>
                """

            else:

                cursor.execute(
                    """
                    UPDATE users
                    SET failed_attempts=%s
                    WHERE id=%s
                    """,
                    (
                        attempts,
                        user["id"]
                    )
                )

                conn.commit()

                cursor.close()
                conn.close()

                return f"""
                <h2>
                Wrong Password ({attempts}/5)
                </h2>
                """

    return render_template("login.html")

# ==========================================
# AUTHENTICATION PATTERN SELECTION
# ==========================================

@auth.route("/select-pattern", methods=["GET", "POST"])
def select_pattern():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if request.method == "POST":

        selected_step1 = request.form.get("step1")
        selected_step2 = request.form.get("step2")
        selected_step3 = request.form.get("step3")

        # Registered pattern
        correct_step1 = session.get("auth_step1")
        correct_step2 = session.get("auth_step2")
        correct_step3 = session.get("auth_step3")

        print("================================")
        print("SELECTED PATTERN")
        print("STEP 1:", selected_step1)
        print("STEP 2:", selected_step2)
        print("STEP 3:", selected_step3)

        print("================================")
        print("CORRECT PATTERN")
        print("STEP 1:", correct_step1)
        print("STEP 2:", correct_step2)
        print("STEP 3:", correct_step3)
        print("================================")

        # ==========================================
        # CHECK PATTERN
        # ==========================================

        if (
            selected_step1 == correct_step1
            and selected_step2 == correct_step2
            and selected_step3 == correct_step3
        ):

            print("AUTHENTICATION PATTERN CORRECT")

            session["current_step"] = 1

            # Start first authentication method
            return redirect(
                url_for("auth.start_authentication")
            )

        else:

            print("AUTHENTICATION PATTERN INCORRECT")

            return """
            <h2>Incorrect Authentication Pattern</h2>
            <p>The selected authentication order is incorrect.</p>
            <a href="/select-pattern">Try Again</a>
            """

    return render_template("select_pattern.html")

# ==========================================
# START AUTHENTICATION METHOD
# ==========================================

@auth.route("/start-authentication")
def start_authentication():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    current_step = session.get("current_step", 1)

    method = session.get(
        f"auth_step{current_step}"
    )

    print("================================")
    print("CURRENT AUTHENTICATION STEP:", current_step)
    print("CURRENT METHOD:", method)
    print("================================")

    # ==========================================
    # EMAIL
    # ==========================================

    if method == "Email":

        otp = generate_otp()

        session["email_otp"] = otp

        print("EMAIL OTP:", otp)

        send_email(
            current_app.mail,
            session["user_email"],
            otp
        )

        return redirect(
            url_for("auth.email_otp")
        )

    # ==========================================
    # SMS
    # ==========================================

    elif method == "SMS":

        return redirect(
            url_for("auth.sms_otp")
        )

    # ==========================================
    # AUTHENTICATOR
    # ==========================================

    elif method == "Authenticator":

        return redirect(
            url_for("auth.authenticator")
        )

    return "<h2>Invalid Authentication Method</h2>"


@auth.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        username = request.form["username"]

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE username=%s",
            (username,)
        )

        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if not user:
            return "<h2>User Not Found</h2>"

        otp = generate_otp()

        session["forgot_otp"] = otp
        session["reset_user"] = username

        send_email(
            current_app.mail,
            user["email"],
            otp
        )

        return redirect(url_for("auth.forgot_otp"))

    return render_template("forgot_password.html")

@auth.route("/forgot-otp", methods=["GET", "POST"])
def forgot_otp():

    if request.method == "POST":

        entered = request.form["otp"]

        if entered == session.get("forgot_otp"):

            session.pop("forgot_otp", None)

            return redirect(url_for("auth.reset_password"))

        return "<h2>Invalid OTP</h2>"

    return render_template("forgot_otp.html")



# ==========================
# EMAIL OTP
# ==========================
@auth.route("/email-otp", methods=["GET", "POST"])
def email_otp():

    if request.method == "POST":

        entered_otp = request.form["otp"]

        if entered_otp == session.get("email_otp"):

            session.pop("email_otp", None)

            # Determine next authentication step
            if session.get("current_step") == 1:
                next_step = session.get("auth_step2")

            elif session.get("current_step") == 2:
                next_step = session.get("auth_step3")

            else:
                next_step = None

            # Move to next step
            if next_step == "Email":

                session["current_step"] = session.get("current_step", 1) + 1

                otp = generate_otp()
                session["email_otp"] = otp

                send_email(
                    current_app.mail,
                    session["user_email"],
                    otp
                )

                return redirect(url_for("auth.email_otp"))

            elif next_step == "SMS":

                session["current_step"] = session.get("current_step", 1) + 1

                return redirect(url_for("auth.sms_otp"))

            elif next_step == "Authenticator":

                session["current_step"] = session.get("current_step", 1) + 1

                return redirect(url_for("auth.authenticator"))

            else:

                return redirect(url_for("auth.dashboard"))

        else:

            return "<h2>Invalid Email OTP</h2>"

    return render_template("email_otp.html")


# ==========================
# SMS OTP
# ==========================
import random

@auth.route("/sms-otp", methods=["GET", "POST"])
def sms_otp():

    if request.method == "GET":

        otp = str(random.randint(100000, 999999))

        session["sms_otp"] = otp

        print("================================")
        print("SMS OTP =", otp)
        print("Session SMS OTP =", session.get("sms_otp"))
        print("================================")

        return render_template("sms_otp.html")

    # Verify OTP
    entered = request.form.get("otp", "").strip()
    session_otp = str(session.get("sms_otp", "")).strip()

    print("Entered OTP:", entered)
    print("Session OTP:", session_otp)

    if entered == session_otp and session_otp != "":

        print("SMS OTP VERIFIED SUCCESSFULLY")

        session.pop("sms_otp", None)

        current_step = session.get("current_step", 1)

        # Determine next step
        if current_step == 1:
            next_step = session.get("auth_step2")

        elif current_step == 2:
            next_step = session.get("auth_step3")

        else:
            next_step = None

        if next_step == "Email":

            session["current_step"] = current_step + 1

            otp = generate_otp()

            session["email_otp"] = otp

            send_email(
                current_app.mail,
                session["user_email"],
                otp
            )

            return redirect(url_for("auth.email_otp"))

        elif next_step == "SMS":

            session["current_step"] = current_step + 1

            return redirect(url_for("auth.sms_otp"))

        elif next_step == "Authenticator":

            session["current_step"] = current_step + 1

            return redirect(url_for("auth.authenticator"))

        else:

            return redirect(url_for("auth.dashboard"))

    return "<h2>Invalid SMS OTP</h2>"
#
# ==========================
# GOOGLE AUTHENTICATOR
# ==========================
@auth.route("/authenticator", methods=["GET", "POST"])
def authenticator():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if request.method == "POST":

        code = request.form.get("code", "").strip()

        if not code:
            return render_template(
                "authenticator.html",
                error="Please enter your authenticator code."
            )

        # Verify the code only once
        is_valid = verify_authenticator(code)

        print("Authenticator verification:", is_valid)

        if is_valid:

            current_step = session.get("current_step", 1)

            if current_step == 1:
                next_step = session.get("auth_step2")
            elif current_step == 2:
                next_step = session.get("auth_step3")
            else:
                next_step = None

            if next_step == "Email":
                session["current_step"] = current_step + 1
                otp = generate_otp()
                session["email_otp"] = otp

                send_email(
                    current_app.mail,
                    session["user_email"],
                    otp
                )

                return redirect(url_for("auth.email_otp"))

            elif next_step == "SMS":
                session["current_step"] = current_step + 1
                return redirect(url_for("auth.sms_otp"))

            elif next_step == "Authenticator":
                session["current_step"] = current_step + 1
                return redirect(url_for("auth.authenticator"))

            else:
                # Clear authentication-step state after completion
                session.pop("current_step", None)
                return redirect(url_for("auth.dashboard"))

        return render_template(
            "authenticator.html",
            error="Invalid Authenticator Code"
        )

    return render_template("authenticator.html")


@auth.route("/profile")
def profile():

    if "username" not in session:
        return redirect(url_for("auth.login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM users WHERE username=%s",
        (session["username"],)
    )

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        "profile.html",
        user=user
    )

@auth.route("/login-history")
def login_history():

    if "username" not in session:
        return redirect(url_for("auth.login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            login_time,
            ip_address,
            device,
            browser,
            status
        FROM login_history
        WHERE user_id = (
            SELECT id FROM users
            WHERE username=%s
        )
        ORDER BY login_time DESC
    """, (session["username"],))

    history = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "login_history.html",
        history=history
    )

@auth.route("/history")
def history():

    if "username" not in session:
        return redirect(url_for("auth.login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT id FROM users WHERE username=%s",
        (session["username"],)
    )

    user = cursor.fetchone()

    cursor.execute(
        """
        SELECT *
        FROM transactions
        WHERE user_id=%s
        ORDER BY transaction_time DESC
        """,
        (user["id"],)
    )

    transactions = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "history.html",
        transactions=transactions
    )
# ==========================
# DASHBOARD
# ==========================
@auth.route("/dashboard")
def dashboard():

    if "username" not in session:
        return redirect(url_for("auth.login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT full_name, balance
        FROM users
        WHERE username=%s
        """,
        (session["username"],)
    )

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        "dashboard.html",
        user=user
    )
# ==========================
# LOGOUT
# ==========================
@auth.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("auth.login"))


from datetime import datetime



@auth.route("/transfer", methods=["GET", "POST"])
def transfer():

    if "username" not in session:
        return redirect(url_for("auth.login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Get logged-in user
        cursor.execute(
            "SELECT id, balance FROM users WHERE username=%s",
            (session["username"],)
        )
        user = cursor.fetchone()

        if not user:
            return redirect(url_for("auth.login"))

        # Get beneficiaries
        cursor.execute(
            """
            SELECT *
            FROM beneficiaries
            WHERE user_id=%s
            """,
            (user["id"],)
        )
        beneficiaries = cursor.fetchall()

        if request.method == "POST":

            # Read fields using the names in transfer.html
            receiver_name = request.form.get(
                "receiver_name", ""
            ).strip()

            receiver_account = request.form.get(
                "account_number", ""
            ).strip()

            beneficiary_id = request.form.get(
                "beneficiary_id", ""
            ).strip()

            amount_text = request.form.get(
                "amount", ""
            ).strip()

            # Validate required fields
            if not receiver_name or not receiver_account or not amount_text:
                return render_template(
                    "transfer.html",
                    beneficiaries=beneficiaries,
                    error="Please enter the receiver name, account number, and amount."
                )

            # Validate amount
            try:
                amount = float(amount_text)
            except ValueError:
                return render_template(
                    "transfer.html",
                    beneficiaries=beneficiaries,
                    error="Please enter a valid amount."
                )

            if amount <= 0:
                return render_template(
                    "transfer.html",
                    beneficiaries=beneficiaries,
                    error="Amount must be greater than zero."
                )

            # Check current balance
            if amount > float(user["balance"]):
                return render_template(
                    "transfer.html",
                    beneficiaries=beneficiaries,
                    error="Insufficient Balance!"
                )

            # Calculate risk
            risk = calculate_risk(
                amount,
                new_device=False,
                different_city=False
            )

            if risk >= 60:
                status = "Blocked"
            elif risk >= 30:
                status = "Pending"
            else:
                status = "Approved"

            session["risk"] = risk

            session["transaction"] = {
                "receiver": receiver_name,
                "account": receiver_account,
                "beneficiary_id": beneficiary_id,
                "amount": amount,
                "risk": risk,
                "status": status
            }

            return redirect(url_for("auth.risk_check"))

        return render_template(
            "transfer.html",
            beneficiaries=beneficiaries
        )

    finally:
        cursor.close()
        conn.close()


@auth.route("/risk-check")
def risk_check():

    risk = session.get("risk", 0)

    if risk >= 60:
        return redirect(url_for("auth.high_risk"))

    elif risk >= 30:
        return redirect(url_for("auth.medium_email_otp"))

    else:
        return redirect(url_for("auth.complete_transaction"))

@auth.route("/medium-risk")
def medium_risk():

    return render_template("medium_risk.html")

@auth.route("/high-risk")
def high_risk():

    risk = session.get("risk")

    return render_template(
        "high_risk.html",
        risk=risk
    )

@auth.route("/high-email-otp", methods=["GET", "POST"])
def high_email_otp():

    if request.method == "GET":

        otp = generate_otp()

        session["high_email_otp"] = otp

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT email FROM users WHERE username=%s",
            (session["username"],)
        )

        user = cursor.fetchone()

        cursor.close()
        conn.close()

        send_email(
            current_app.mail,
            user["email"],
            otp
        )

        return render_template("high_email_otp.html")

    entered = request.form["otp"]

    if entered == session.get("high_email_otp"):

        session.pop("high_email_otp")

        return redirect(url_for("auth.high_sms_otp"))

    return "<h2>Wrong Email OTP</h2>"

@auth.route("/high-sms-otp", methods=["GET", "POST"])
def high_sms_otp():

    if request.method == "GET":

        otp = str(random.randint(100000, 999999))
        session["high_sms_otp"] = otp

        print("HIGH SMS OTP =", otp)

        return render_template("high_sms_otp.html")

    entered = request.form["otp"]

    if entered == session.get("high_sms_otp"):

         session.pop("high_sms_otp", None)

         return redirect(url_for("auth.complete_transaction"))

    return "<h2>Wrong SMS OTP</h2>"

@auth.route("/medium-email-otp", methods=["GET","POST"])
def medium_email_otp():

    if request.method == "GET":

        otp = generate_otp()

        session["medium_otp"] = otp

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT email FROM users WHERE username=%s",
            (session["username"],)
        )

        user = cursor.fetchone()

        cursor.close()
        conn.close()

        send_email(
            current_app.mail,
            user["email"],
            otp
        )

        return render_template("medium_email_otp.html")

    entered = request.form["otp"]

    if entered == session.get("medium_otp"):

        session.pop("medium_otp")

        return redirect(url_for("auth.complete_transaction"))

    return "<h2>Wrong OTP</h2>"

@auth.route("/complete-transaction")
def complete_transaction():

    if "transaction" not in session:
        return "<h2>No Transaction Found</h2>"

    transaction = session["transaction"]

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Get Logged-in User ID
    cursor.execute(
        "SELECT id FROM users WHERE username=%s",
        (session["username"],)
    )

    user = cursor.fetchone()

    sql = """
    INSERT INTO transactions
    (
        user_id,
        receiver_name,
        receiver_account,
        amount,
        latitude,
        longitude,
        transaction_time,
        risk_score,
        status
    )
    VALUES
    (
        %s,%s,%s,%s,%s,%s,NOW(),%s,%s
    )
    """

    values = (
        user["id"],
        transaction["receiver"],
        transaction["account"],
        transaction["amount"],
        12.9716,
        77.5946,
        transaction["risk"],
        "Approved"
    )

    cursor.execute(sql, values)

    # ==========================
    # NEW CODE STARTS HERE
    # ==========================

    cursor.execute(
        """
        UPDATE users
        SET balance = balance - %s
        WHERE id = %s
        """,
        (
            transaction["amount"],
            user["id"]
        )
    )

    # ==========================
    # NEW CODE ENDS HERE
    # ==========================

    conn.commit()

    cursor.execute(
        """
        INSERT INTO notifications
        (user_id, message)
        VALUES (%s, %s)
        """,
        (
            user["id"],
            f"₹{transaction['amount']} transferred successfully to {transaction['receiver']}."
        )
    )

    conn.commit()

    cursor.close()
    conn.close()

    session.pop("transaction", None)
    session.pop("risk", None)

    return "<h2>Transaction Successful</h2>"

@auth.route("/reset-password", methods=["GET", "POST"])
def reset_password():

    if request.method == "POST":

        password = request.form["password"]
        confirm = request.form["confirm"]

        if password != confirm:
            return "<h2>Passwords do not match</h2>"

        hashed = hash_password(password)

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE users
            SET password=%s
            WHERE username=%s
            """,
            (
                hashed,
                session["reset_user"]
            )
        )

        conn.commit()

        cursor.close()
        conn.close()

        session.pop("reset_user", None)

        return redirect(url_for("auth.login"))

    return render_template("reset_password.html")

@auth.route("/deposit", methods=["GET", "POST"])
def deposit():

    if "username" not in session:
        return redirect(url_for("auth.login"))

    if request.method == "POST":

        amount = float(request.form["amount"])

        # Validation
        if amount <= 0:
            return render_template(
                "deposit.html",
                error="Amount must be greater than zero."
            )

        if amount > 100000:
            return render_template(
                "deposit.html",
                error="Maximum deposit limit is ₹100000."
            )

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Get Logged-in User
        cursor.execute(
            """
            SELECT id, balance
            FROM users
            WHERE username=%s
            """,
            (session["username"],)
        )

        user = cursor.fetchone()

        # Update Balance
        cursor.execute(
            """
            UPDATE users
            SET balance = balance + %s
            WHERE id=%s
            """,
            (
                amount,
                user["id"]
            )
        )

        conn.commit()

        # Save Deposit History
        cursor.execute(
            """
            INSERT INTO deposits
            (user_id, amount, status)
            VALUES (%s,%s,%s)
            """,
            (
                user["id"],
                amount,
                "Success"
            )
        )

        conn.commit()

        # Save Notification
        cursor.execute(
            """
            INSERT INTO notifications
            (user_id, message)
            VALUES (%s,%s)
            """,
            (
                user["id"],
                f"₹{amount} deposited successfully."
            )
        )

        conn.commit()

        # Get Updated Balance
        cursor.execute(
            """
            SELECT balance
            FROM users
            WHERE id=%s
            """,
            (user["id"],)
        )

        updated_user = cursor.fetchone()

        cursor.close()
        conn.close()

        return render_template(
            "deposit_success.html",
            amount=amount,
            balance=updated_user["balance"]
        )

    return render_template("deposit.html")

@auth.route("/add-beneficiary", methods=["GET", "POST"])
def add_beneficiary():

    if "username" not in session:
        return redirect(url_for("auth.login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Get logged-in user ID
    cursor.execute(
        "SELECT id FROM users WHERE username=%s",
        (session["username"],)
    )

    user = cursor.fetchone()

    if request.method == "POST":

        name = request.form["name"]
        account = request.form["account"]
        bank = request.form["bank"]
        ifsc = request.form["ifsc"]

        cursor.execute(
            """
            INSERT INTO beneficiaries
            (user_id, beneficiary_name, account_number, bank_name, ifsc_code)
            VALUES (%s,%s,%s,%s,%s)
            """,
            (
                user["id"],
                name,
                account,
                bank,
                ifsc
            )
        )

        conn.commit()

        cursor.close()
        conn.close()

        return redirect(url_for("auth.view_beneficiaries"))

    cursor.close()
    conn.close()

    return render_template("add_beneficiary.html")

@auth.route("/view-beneficiaries")
def view_beneficiaries():

    if "username" not in session:
        return redirect(url_for("auth.login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT id FROM users WHERE username=%s",
        (session["username"],)
    )

    user = cursor.fetchone()

    cursor.execute(
        """
        SELECT *
        FROM beneficiaries
        WHERE user_id=%s
        """,
        (user["id"],)
    )

    beneficiaries = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "view_beneficiaries.html",
        beneficiaries=beneficiaries
    )

@auth.route("/fraud-logs")
def fraud_logs():
    ...

@auth.route("/edit-profile", methods=["GET", "POST"])
def edit_profile():

    if "username" not in session:
        return redirect(url_for("auth.login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM users WHERE username=%s",
        (session["username"],)
    )

    user = cursor.fetchone()

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        mobile = request.form["mobile"]

        cursor.execute(
            """
            UPDATE users
            SET
                name=%s,
                email=%s,
                mobile=%s
            WHERE username=%s
            """,
            (
                name,
                email,
                mobile,
                session["username"]
            )
        )

        conn.commit()

        flash("Profile Updated Successfully!", "success")

        cursor.close()
        conn.close()

        return redirect(url_for("auth.profile"))

    cursor.close()
    conn.close()

    return render_template(
        "edit_profile.html",
        user=user
    )

@auth.route("/notifications")
def notifications():

    if "username" not in session:
        return redirect(url_for("auth.login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT id FROM users WHERE username=%s",
        (session["username"],)
    )

    user = cursor.fetchone()

    cursor.execute(
        """
        SELECT *
        FROM notifications
        WHERE user_id=%s
        ORDER BY created_at DESC
        """,
        (user["id"],)
    )

    notifications = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "notifications.html",
        notifications=notifications
    )

@auth.route("/deposit-history")
def deposit_history():

    if "username" not in session:
        return redirect(url_for("auth.login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT id FROM users WHERE username=%s",
        (session["username"],)
    )

    user = cursor.fetchone()

    cursor.execute(
        """
        SELECT *
        FROM deposits
        WHERE user_id=%s
        ORDER BY deposit_time DESC
        """,
        (user["id"],)
    )

    deposits = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "deposit_history.html",
        deposits=deposits
    )

@auth.route("/withdraw", methods=["GET", "POST"])
def withdraw():

    if "username" not in session:
        return redirect(url_for("auth.login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Get logged-in user
    cursor.execute(
        "SELECT * FROM users WHERE username=%s",
        (session["username"],)
    )

    user = cursor.fetchone()

    if request.method == "POST":

        amount = float(request.form["amount"])

        # Check balance
        if amount > user["balance"]:

            cursor.close()
            conn.close()

            return "<h2>Insufficient Balance!</h2>"

        # Deduct balance
        cursor.execute(
            """
            UPDATE users
            SET balance = balance - %s
            WHERE id=%s
            """,
            (
                amount,
                user["id"]
            )
        )

        conn.commit()

        # Save withdrawal history
        cursor.execute(
            """
            INSERT INTO withdrawals
            (user_id, amount, status)
            VALUES (%s,%s,%s)
            """,
            (
                user["id"],
                amount,
                "Success"
            )
        )

        conn.commit()

        # Save notification
        cursor.execute(
            """
            INSERT INTO notifications
            (user_id, message)
            VALUES (%s,%s)
            """,
            (
                user["id"],
                f"₹{amount} withdrawn successfully."
            )
        )

        conn.commit()

        cursor.close()
        conn.close()

        return redirect(url_for("auth.dashboard"))

    cursor.close()
    conn.close()

    return render_template("withdraw.html")

@auth.route("/balance")
def balance():

    if "username" not in session:
        return redirect(url_for("auth.login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Get user details
    cursor.execute(
        "SELECT * FROM users WHERE username=%s",
        (session["username"],)
    )

    user = cursor.fetchone()

    # Total Deposits
    cursor.execute(
        """
        SELECT IFNULL(SUM(amount),0) AS total
        FROM deposits
        WHERE user_id=%s
        """,
        (user["id"],)
    )

    total_deposit = cursor.fetchone()["total"]

    # Total Withdrawals
    cursor.execute(
        """
        SELECT IFNULL(SUM(amount),0) AS total
        FROM withdrawals
        WHERE user_id=%s
        """,
        (user["id"],)
    )

    total_withdraw = cursor.fetchone()["total"]

    # Total Transfers
    cursor.execute(
        """
        SELECT IFNULL(SUM(amount),0) AS total
        FROM transactions
        WHERE user_id=%s
        """,
        (user["id"],)
    )

    total_transfer = cursor.fetchone()["total"]

    cursor.close()
    conn.close()

    return render_template(
        "balance.html",
        user=user,
        total_deposit=total_deposit,
        total_withdraw=total_withdraw,
        total_transfer=total_transfer
    )

@auth.route("/login-pattern", methods=["GET", "POST"])
def login_pattern():

    if request.method == "POST":

        selected_step1 = request.form.get("step1")
        selected_step2 = request.form.get("step2")
        selected_step3 = request.form.get("step3")

        selected_pattern = [
            selected_step1,
            selected_step2,
            selected_step3
        ]

        registered_pattern = session.get("auth_steps")

        print("REGISTERED PATTERN:", registered_pattern)
        print("SELECTED PATTERN:", selected_pattern)

        # Check whether selected pattern matches registration pattern
        if selected_pattern != registered_pattern:

            return """
            <h2>Incorrect Authentication Pattern</h2>
            <p>
            The authentication order you selected does not
            match your registered authentication pattern.
            </p>

            <a href="/login-pattern">Try Again</a>
            """

        # Pattern is correct
        session["auth_index"] = 0

        return redirect(url_for("auth.next_auth_step"))

    return render_template("login_pattern.html")