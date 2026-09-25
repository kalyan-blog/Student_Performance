from flask import Blueprint, request, jsonify, session
from database.db import _find, _insert, _update, _delete, _all, init_db
import bcrypt
from functools import wraps

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

init_db()


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required"}), 401
        if session.get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated


@auth_bp.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        name = data.get("name", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        role = data.get("role", "faculty")
        if not all([name, email, password]):
            return jsonify({"error": "Name, email, and password are required"}), 400
        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400
        existing = _find("users", "email", email)
        if existing.data:
            return jsonify({"error": "Email already registered"}), 409
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        result = _insert("users", {"name": name, "email": email, "password": hashed, "role": role})
        user = result.data[0]
        session["user_id"] = user["id"]
        session["name"] = user["name"]
        session["email"] = user["email"]
        session["role"] = user["role"]
        return jsonify({"message": "Registration successful", "user": {"id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"]}}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400
        result = _find("users", "email", email)
        if not result.data:
            return jsonify({"error": "Invalid email or password"}), 401
        user = result.data[0]
        stored = user["password"].encode("utf-8") if isinstance(user["password"], str) else user["password"]
        if not bcrypt.checkpw(password.encode("utf-8"), stored):
            return jsonify({"error": "Invalid email or password"}), 401
        session["user_id"] = user["id"]
        session["name"] = user["name"]
        session["email"] = user["email"]
        session["role"] = user["role"]
        return jsonify({"message": "Login successful", "user": {"id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"]}}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    try:
        data = request.get_json()
        email = data.get("email", "").strip().lower()
        if not email:
            return jsonify({"error": "Email is required"}), 400
        existing = _find("users", "email", email)
        if not existing.data:
            return jsonify({"error": "If the email exists, a reset link has been sent"}), 200
        new_pw = "temp123"
        hashed = bcrypt.hashpw(new_pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        _update("users", "email", email, {"password": hashed})
        return jsonify({"message": "Password reset successful. Temporary password: temp123"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/session", methods=["GET"])
@login_required
def get_session():
    return jsonify({"user": {"id": session["user_id"], "name": session.get("name"), "email": session.get("email"), "role": session.get("role")}}), 200


@auth_bp.route("/users", methods=["GET"])
@admin_required
def get_users():
    try:
        result = _all("users")
        users = [{"id": u["id"], "name": u["name"], "email": u["email"], "role": u["role"], "created_at": u["created_at"]} for u in result.data]
        return jsonify({"users": users}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/users/<user_id>", methods=["DELETE"])
@admin_required
def delete_user(user_id):
    try:
        _delete("users", "id", user_id)
        return jsonify({"message": "User deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500