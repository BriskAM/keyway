import requests
from datetime import datetime, timezone
from flask import current_app

ALLOWED_METHODS = {"GET", "POST", "HEAD"}

def run_healthcheck(secret, decrypted_value: str) -> dict:
    """
    Executes an outbound HTTP request using the decrypted secret value.
    Enforces strict security properties:
    - 5-second timeout (or configurable)
    - allow_redirects=False (prevent key leakage via redirects)
    - Redacted/omitted response body
    """
    method = (secret.healthcheck_method or "GET").upper()
    if method not in ALLOWED_METHODS:
        return {"status": "error", "message": f"Unsupported method: {method}"}
    
    url = secret.healthcheck_url
    if not url:
        return {"status": "error", "message": "No healthcheck URL configured"}
        
    headers = {}
    params = {}
    
    # Apply authentication styling
    auth_style = secret.healthcheck_auth_style
    auth_field = secret.healthcheck_auth_field
    
    if auth_style == "bearer":
        headers["Authorization"] = f"Bearer {decrypted_value}"
    elif auth_style == "header":
        if auth_field:
            headers[auth_field] = decrypted_value
        else:
            headers["Authorization"] = decrypted_value
    elif auth_style == "query_param":
        if auth_field:
            params[auth_field] = decrypted_value
        else:
            params["api_key"] = decrypted_value
            
    # Timeout settings
    timeout = 5
    if current_app:
        timeout = current_app.config.get("HEALTHCHECK_TIMEOUT_SECONDS", 5)
        
    try:
        resp = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            timeout=timeout,
            allow_redirects=False  # Crucial: do not follow redirects
        )
        
        # Determine status: < 400 is considered valid, 4xx/5xx invalid
        status = "valid" if resp.status_code < 400 else "invalid"
        return {
            "status": status,
            "http_status": resp.status_code,
            "checked_at": datetime.now(timezone.utc)
        }
        
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "message": "Connection timed out",
            "checked_at": datetime.now(timezone.utc)
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": "Could not connect to destination endpoint",
            "checked_at": datetime.now(timezone.utc)
        }
