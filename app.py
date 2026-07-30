from flask import Flask, render_template, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from models import db, User, LoginHistory

from flask_login import (
    LoginManager,
    login_user,
    login_required,
    logout_user,
    current_user
)

from config import Config
from forms import RegisterForm, LoginForm

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = "login"

login_manager.login_message = "Please login to access this page."
login_manager.login_message_category = "warning"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

with app.app_context():
    db.create_all()


# ---------------- Home ----------------
@app.route("/")
def home():
    return render_template("index.html")


# ---------------- Sign Up ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():

    form = RegisterForm()

    if form.validate_on_submit():

        # Check if email already exists
        existing_user = User.query.filter_by(
            email=form.email.data
        ).first()

        if existing_user:
            flash("Email already registered!", "danger")
            return redirect(url_for("signup"))

        # Hash the password
        hashed_password = generate_password_hash(form.password.data)

        # Create new user
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=hashed_password
        )

        # Save to database
        db.session.add(new_user)
        db.session.commit()

        flash("Registration Successful!", "success")

        return redirect(url_for("home"))

    return render_template("signup.html", form=form)


# ---------------- Login ----------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    form = LoginForm()

    if form.validate_on_submit():

        # Find user by email
        user = User.query.filter_by(email=form.email.data).first()

        if user:

            # Check if account is locked
            if user.is_locked:

                if user.lock_time and datetime.utcnow() >= user.lock_time + timedelta(minutes=15):

                    # Unlock automatically
                    user.is_locked = False
                    user.failed_attempts = 0
                    user.lock_time = None
                    db.session.commit()

                else:

                    remaining = 15 - int(
                        (datetime.utcnow() - user.lock_time).total_seconds() // 60
                    )

                    flash(
                        f"Account is locked. Try again in {remaining} minute(s).",
                        "danger"
                    )

                    return redirect(url_for("login"))

            # Check password
            if check_password_hash(user.password_hash, form.password.data):

                # Reset failed attempts after successful login
                user.failed_attempts = 0
                user.is_locked = False
                user.lock_time = None

                db.session.commit()

                login_user(user)
                
                log = LoginHistory(
                    username=user.username,
                    email=user.email,
                    status="Success",
                    ip_address=request.remote_addr
                )

                db.session.add(log)
                db.session.commit()

                flash("Login Successful!", "success")
                return redirect(url_for("dashboard"))

            else:
                log = LoginHistory(
                username=user.username,
                email=user.email,
                status="Failed",
                ip_address=request.remote_addr
                )

                db.session.add(log)

                # Increase failed attempts
                user.failed_attempts += 1

                if user.failed_attempts >= 5:

                    user.is_locked = True

                    user.lock_time = datetime.utcnow()

                    flash(
                        "Account locked for 15 minutes due to multiple failed login attempts.",
                        "danger"
                    )
                else:

                    remaining = 5 - user.failed_attempts

                    flash(
                        f"Invalid password! {remaining} attempt(s) remaining.",
                        "warning"
                    )

                db.session.commit()

        else:
            
            log = LoginHistory(
        username="Unknown",
        email=form.email.data,
        status="Failed",
        ip_address=request.remote_addr
        )

        db.session.add(log)
        db.session.commit()

        flash("Email not found.", "danger")

            

    return render_template("login.html", form=form)
    
# ---------------- Dashboard ----------------
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

# ---------------- Login History ----------------
@app.route("/login-history")
@login_required
def login_history():

    history = LoginHistory.query.order_by(
        LoginHistory.login_time.desc()
    ).all()

    return render_template(
        "login_history.html",
        history=history
    )

# ---------------- Security Testing ----------------

@app.route("/security-test", methods=["GET", "POST"])
@login_required
def security_test():

    xss_input = ""
    sql_result = ""

    if request.method == "POST":

        test_type = request.form.get("test_type")

        if test_type == "xss":

            xss_input = request.form.get("xss_input")

        elif test_type == "sql":

            email = request.form.get("email")

            user = User.query.filter_by(
                email=email
            ).first()

            if user:
                sql_result = "User found. SQL Injection blocked using SQLAlchemy ORM."
            else:
                sql_result = "Invalid user. SQL Injection attempt failed."

    return render_template(
        "security_test.html",
        xss_input=xss_input,
        sql_result=sql_result
    )


# ---------------- Logout ----------------
@app.route("/logout")
@login_required
def logout():
    logout_user()

    flash("Logged out successfully.", "success")

    return redirect(url_for("home"))

# ---------------- Security Headers ----------------
@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
        "script-src 'self' https://cdn.jsdelivr.net;"
    )
    return response

# ---------------- Error Handlers ----------------
@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(error):
    return render_template("500.html"), 500

if __name__ == "__main__":
    app.run(debug=True)