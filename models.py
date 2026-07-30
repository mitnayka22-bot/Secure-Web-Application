from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(80), nullable=False)

    email = db.Column(db.String(120), unique=True, nullable=False)

    password_hash = db.Column(db.String(255), nullable=False)

    # -------- Security Features --------
    # Number of failed login attempts
    failed_attempts = db.Column(db.Integer, nullable=False, default=0)

    # Lock account after multiple failed attempts
    is_locked = db.Column(db.Boolean, nullable=False, default=False)

    lock_time = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f"<User {self.email}>"

class LoginHistory(db.Model):
    __tablename__ = "login_history"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(80), nullable=False)

    email = db.Column(db.String(120), nullable=False)

    status = db.Column(db.String(20), nullable=False)

    ip_address = db.Column(db.String(50), nullable=False)

    login_time = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<LoginHistory {self.email} {self.status}>"