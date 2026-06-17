import base64
import os
from flask import Blueprint, request, jsonify, session
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db
from app.models.user import User
from app.services.crypto_service import derive_key

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/signup", methods=["POST"])
def signup():
    if current_user.is_authenticated:
        return jsonify({"message": "Already authenticated"}), 400
        
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
        
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "User with this email already exists"}), 400
        
    # Generate KDF salt
    salt_bytes = os.urandom(16)
    kdf_salt = base64.b64encode(salt_bytes).decode("utf-8")
    
    # Hash password for standard login checks
    password_hash = generate_password_hash(password)
    
    user = User(
        email=email,
        password_hash=password_hash,
        kdf_salt=kdf_salt
    )
    
    db.session.add(user)
    db.session.commit()
    
    # Log the user in
    login_user(user)
    
    # Derive encryption key and store in session
    fernet_key = derive_key(password, salt_bytes)
    session["fernet_key"] = fernet_key.decode("utf-8")
    
    return jsonify({
        "message": "Signup successful",
        "user": user.to_dict()
    }), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    if current_user.is_authenticated:
        return jsonify({"message": "Already authenticated", "user": current_user.to_dict()}), 200
        
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
        
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid email or password"}), 401
        
    login_user(user)
    
    # Derive Fernet key using the user's specific salt
    salt_bytes = base64.b64decode(user.kdf_salt.encode("utf-8"))
    fernet_key = derive_key(password, salt_bytes)
    session["fernet_key"] = fernet_key.decode("utf-8")
    
    return jsonify({
        "message": "Login successful",
        "user": user.to_dict()
    }), 200

@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    session.pop("fernet_key", None)
    session.clear()
    return jsonify({"message": "Logout successful"}), 200

@auth_bp.route("/me", methods=["GET"])
def me():
    if current_user.is_authenticated:
        # Check if the cryptographic key is present (meaning session is fully initialized)
        has_key = "fernet_key" in session
        return jsonify({
            "authenticated": True,
            "user": current_user.to_dict(),
            "has_key": has_key
        }), 200
    return jsonify({"authenticated": False}), 200
