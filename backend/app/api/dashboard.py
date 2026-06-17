from datetime import date
from flask import Blueprint, jsonify, session
from flask_login import login_required, current_user

from app.extensions import db
from app.models.secret import Secret
from app.services.crypto_service import decrypt_value
from app.api.secrets import mask_secret_value, get_session_key
from cryptography.fernet import InvalidToken

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("", methods=["GET"])
@login_required
def get_dashboard_data():
    key = get_session_key()
    if not key:
        return jsonify({"error": "Encryption key missing in session. Please log in again."}), 401
        
    today = date.today()
    all_secrets = Secret.query.filter_by(user_id=current_user.id).all()
    
    # Process secrets and decrypt to generate masked values
    processed_secrets = []
    for secret in all_secrets:
        try:
            decrypted = decrypt_value(secret.encrypted_value, key)
            masked = mask_secret_value(decrypted)
        except InvalidToken:
            masked = "Error: Decryption Failed"
            
        processed_secrets.append((secret, masked))
        
    expiring_soon = []
    expired = []
    invalid_keys = []
    unchecked = []
    
    for secret, masked in processed_secrets:
        # Expiry checks
        if secret.expiry_date:
            days_to_expiry = (secret.expiry_date - today).days
            if 0 <= days_to_expiry <= 7:
                expiring_soon.append(secret.to_dict(masked_value=masked))
            elif days_to_expiry < 0:
                expired.append(secret.to_dict(masked_value=masked))
                
        # Health status checks
        if secret.last_check_status == "invalid":
            invalid_keys.append(secret.to_dict(masked_value=masked))
        elif secret.healthcheck_url and secret.last_check_status == "unchecked":
            unchecked.append(secret.to_dict(masked_value=masked))
            
    return jsonify({
        "total_secrets": len(all_secrets),
        "expiring_soon": expiring_soon,
        "expired": expired,
        "invalid_keys": invalid_keys,
        "unchecked": unchecked
    }), 200
