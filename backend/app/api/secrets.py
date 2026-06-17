from datetime import datetime, date, timezone
from flask import Blueprint, request, jsonify, session
from flask_login import login_required, current_user
from app.extensions import db
from app.models.secret import Secret
from app.services.crypto_service import encrypt_value, decrypt_value
from cryptography.fernet import InvalidToken

secrets_bp = Blueprint("secrets", __name__)

def get_session_key():
    """Retrieve the Fernet key from the session. Returns bytes or None."""
    key_str = session.get("fernet_key")
    if not key_str:
        return None
    return key_str.encode("utf-8")

def mask_secret_value(value: str) -> str:
    """Mask a secret value for safe display (e.g. sk_li...1a2b)."""
    if not value:
        return ""
    if len(value) <= 8:
        return "••••••••"
    # Show first 5 chars and last 4 chars
    return f"{value[:5]}...{value[-4:]}"

def is_rate_limited():
    """Simple session-based rate limiter for reveal operations."""
    now = datetime.now(timezone.utc).timestamp()
    reveals = session.get("reveals", [])
    
    # Filter out reveals older than 60 seconds
    reveals = [ts for ts in reveals if now - ts < 60]
    
    # Check limit (default 10 reveals per minute)
    limit = 10
    if len(reveals) >= limit:
        session["reveals"] = reveals
        return True
        
    reveals.append(now)
    session["reveals"] = reveals
    return False

@secrets_bp.route("", methods=["GET"])
@login_required
def list_secrets():
    key = get_session_key()
    if not key:
        return jsonify({"error": "Encryption key missing in session. Please log in again."}), 401
        
    secrets = Secret.query.filter_by(user_id=current_user.id).order_by(Secret.created_at.desc()).all()
    
    result = []
    for secret in secrets:
        try:
            decrypted = decrypt_value(secret.encrypted_value, key)
            masked = mask_secret_value(decrypted)
        except InvalidToken:
            masked = "Error: Decryption Failed (Wrong Key)"
        
        result.append(secret.to_dict(masked_value=masked))
        
    return jsonify(result), 200

@secrets_bp.route("", methods=["POST"])
@login_required
def create_secret():
    key = get_session_key()
    if not key:
        return jsonify({"error": "Encryption key missing in session. Please log in again."}), 401
        
    data = request.get_json() or {}
    service_name = data.get("service_name")
    raw_value = data.get("value")
    
    if not service_name or not raw_value:
        return jsonify({"error": "Service name and secret value are required"}), 400
        
    # Optional parameters
    notes = data.get("notes")
    # Tags can be passed as an array or comma-separated string
    tags_data = data.get("tags", [])
    if isinstance(tags_data, list):
        tags = ",".join(tags_data)
    else:
        tags = str(tags_data)
        
    expiry_date_str = data.get("expiry_date")
    expiry_date = None
    if expiry_date_str:
        try:
            expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Expiry date must be in YYYY-MM-DD format"}), 400
            
    # Healthcheck config
    healthcheck_url = data.get("healthcheck_url")
    healthcheck_method = data.get("healthcheck_method", "GET")
    healthcheck_auth_style = data.get("healthcheck_auth_style", "bearer")
    healthcheck_auth_field = data.get("healthcheck_auth_field")
    
    # Encrypt the value
    encrypted_value = encrypt_value(raw_value, key)
    
    secret = Secret(
        user_id=current_user.id,
        service_name=service_name,
        encrypted_value=encrypted_value,
        notes=notes,
        tags=tags,
        expiry_date=expiry_date,
        healthcheck_url=healthcheck_url,
        healthcheck_method=healthcheck_method,
        healthcheck_auth_style=healthcheck_auth_style,
        healthcheck_auth_field=healthcheck_auth_field,
        last_check_status="unchecked"
    )
    
    db.session.add(secret)
    db.session.commit()
    
    masked = mask_secret_value(raw_value)
    return jsonify({
        "message": "Secret created successfully",
        "secret": secret.to_dict(masked_value=masked)
    }), 201

@secrets_bp.route("/<int:id>", methods=["GET"])
@login_required
def get_secret(id):
    key = get_session_key()
    if not key:
        return jsonify({"error": "Encryption key missing in session. Please log in again."}), 401
        
    secret = Secret.query.filter_by(id=id, user_id=current_user.id).first()
    if not secret:
        return jsonify({"error": "Secret not found"}), 404
        
    try:
        decrypted = decrypt_value(secret.encrypted_value, key)
        masked = mask_secret_value(decrypted)
    except InvalidToken:
        masked = "Error: Decryption Failed"
        
    return jsonify(secret.to_dict(masked_value=masked)), 200

@secrets_bp.route("/<int:id>", methods=["PUT"])
@login_required
def update_secret(id):
    key = get_session_key()
    if not key:
        return jsonify({"error": "Encryption key missing in session. Please log in again."}), 401
        
    secret = Secret.query.filter_by(id=id, user_id=current_user.id).first()
    if not secret:
        return jsonify({"error": "Secret not found"}), 404
        
    data = request.get_json() or {}
    
    # Update simple fields
    if "service_name" in data:
        secret.service_name = data["service_name"]
    if "notes" in data:
        secret.notes = data["notes"]
    if "tags" in data:
        tags_data = data["tags"]
        if isinstance(tags_data, list):
            secret.tags = ",".join(tags_data)
        else:
            secret.tags = str(tags_data)
            
    if "expiry_date" in data:
        expiry_date_str = data["expiry_date"]
        if expiry_date_str:
            try:
                secret.expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"error": "Expiry date must be in YYYY-MM-DD format"}), 400
        else:
            secret.expiry_date = None
            
    # Update healthcheck fields
    if "healthcheck_url" in data:
        secret.healthcheck_url = data["healthcheck_url"]
    if "healthcheck_method" in data:
        secret.healthcheck_method = data["healthcheck_method"]
    if "healthcheck_auth_style" in data:
        secret.healthcheck_auth_style = data["healthcheck_auth_style"]
    if "healthcheck_auth_field" in data:
        secret.healthcheck_auth_field = data["healthcheck_auth_field"]
        
    # Update encrypted value if a new one is sent
    raw_value = data.get("value")
    if raw_value:
        secret.encrypted_value = encrypt_value(raw_value, key)
        # Reset check status if key changed
        secret.last_check_status = "unchecked"
        secret.last_checked_at = None
        
    db.session.commit()
    
    # Determine the masked representation
    try:
        if raw_value:
            masked = mask_secret_value(raw_value)
        else:
            decrypted = decrypt_value(secret.encrypted_value, key)
            masked = mask_secret_value(decrypted)
    except InvalidToken:
        masked = "Error: Decryption Failed"
        
    return jsonify({
        "message": "Secret updated successfully",
        "secret": secret.to_dict(masked_value=masked)
    }), 200

@secrets_bp.route("/<int:id>", methods=["DELETE"])
@login_required
def delete_secret(id):
    secret = Secret.query.filter_by(id=id, user_id=current_user.id).first()
    if not secret:
        return jsonify({"error": "Secret not found"}), 404
        
    db.session.delete(secret)
    db.session.commit()
    
    return jsonify({"message": "Secret deleted successfully"}), 200

@secrets_bp.route("/<int:id>/reveal", methods=["POST"])
@login_required
def reveal_secret(id):
    if is_rate_limited():
        return jsonify({"error": "Too many requests. Please wait a minute before revealing more secrets."}), 429
        
    key = get_session_key()
    if not key:
        return jsonify({"error": "Encryption key missing in session. Please log in again."}), 401
        
    secret = Secret.query.filter_by(id=id, user_id=current_user.id).first()
    if not secret:
        return jsonify({"error": "Secret not found"}), 404
        
    try:
        decrypted = decrypt_value(secret.encrypted_value, key)
        return jsonify({"value": decrypted}), 200
    except InvalidToken:
        return jsonify({"error": "Decryption failed. Invalid session encryption key."}), 400
