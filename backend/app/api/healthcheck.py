from datetime import datetime, timezone
import concurrent.futures
from flask import Blueprint, jsonify, session
from flask_login import login_required, current_user

from app.extensions import db
from app.models.secret import Secret
from app.services.crypto_service import decrypt_value
from app.services.healthcheck_service import run_healthcheck
from cryptography.fernet import InvalidToken

healthcheck_bp = Blueprint("healthcheck", __name__)

def get_session_key():
    key_str = session.get("fernet_key")
    if not key_str:
        return None
    return key_str.encode("utf-8")

@healthcheck_bp.route("/<int:id>/healthcheck", methods=["POST"])
@login_required
def trigger_healthcheck(id):
    key = get_session_key()
    if not key:
        return jsonify({"error": "Encryption key missing in session. Please log in again."}), 401
        
    secret = Secret.query.filter_by(id=id, user_id=current_user.id).first()
    if not secret:
        return jsonify({"error": "Secret not found"}), 404
        
    if not secret.healthcheck_url:
        return jsonify({"error": "No healthcheck URL configured for this secret"}), 400
        
    try:
        decrypted = decrypt_value(secret.encrypted_value, key)
    except InvalidToken:
        return jsonify({"error": "Decryption failed. Invalid session encryption key."}), 400
        
    # Execute the check
    result = run_healthcheck(secret, decrypted)
    
    # Update DB fields
    secret.last_check_status = result["status"]
    secret.last_checked_at = result["checked_at"]
    db.session.commit()
    
    return jsonify({
        "message": "Healthcheck completed",
        "status": secret.last_check_status,
        "http_status": result.get("http_status"),
        "error_message": result.get("message"),
        "last_checked_at": secret.last_checked_at.isoformat()
    }), 200

@healthcheck_bp.route("/healthcheck-all", methods=["POST"])
@login_required
def trigger_healthcheck_all():
    key = get_session_key()
    if not key:
        return jsonify({"error": "Encryption key missing in session. Please log in again."}), 401
        
    # Get all secrets of user that have healthcheck URL
    secrets = Secret.query.filter_by(user_id=current_user.id).filter(Secret.healthcheck_url.isnot(None), Secret.healthcheck_url != "").all()
    
    if not secrets:
        return jsonify({"message": "No secrets with healthcheck configurations found", "results": []}), 200
        
    results = []
    
    def check_and_update(sec):
        try:
            dec = decrypt_value(sec.encrypted_value, key)
            res = run_healthcheck(sec, dec)
            return sec.id, res
        except InvalidToken:
            return sec.id, {"status": "error", "message": "Decryption failed", "checked_at": datetime.now(timezone.utc)}
            
    # Run in parallel using a ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_secret = {executor.submit(check_and_update, sec): sec for sec in secrets}
        for future in concurrent.futures.as_completed(future_to_secret):
            sec = future_to_secret[future]
            try:
                sec_id, result = future.result()
                # Find database object to update
                db_secret = Secret.query.get(sec_id)
                if db_secret:
                    db_secret.last_check_status = result["status"]
                    db_secret.last_checked_at = result["checked_at"]
                    results.append({
                        "id": db_secret.id,
                        "service_name": db_secret.service_name,
                        "status": db_secret.last_check_status,
                        "http_status": result.get("http_status"),
                        "error_message": result.get("message")
                    })
            except Exception as exc:
                results.append({
                    "id": sec.id,
                    "service_name": sec.service_name,
                    "status": "error",
                    "error_message": f"Exception occurred during execution: {str(exc)}"
                })
                
    db.session.commit()
    
    return jsonify({
        "message": f"Completed batch check of {len(results)} secrets",
        "results": results
    }), 200
