import unittest
import json
import base64
from unittest.mock import patch, MagicMock
import requests
import tempfile


from app import create_app, db
from app.models.user import User
from app.models.secret import Secret
from app.services.crypto_service import decrypt_value

class TestKeywayAPI(unittest.TestCase):
    def setUp(self):
        self.test_session_dir = tempfile.mkdtemp()
        # Override config for testing
        self.app = create_app(overrides={
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SESSION_TYPE": "filesystem",
            "SESSION_FILE_DIR": self.test_session_dir,
            "WTF_CSRF_ENABLED": False
        })
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        self.email = "test@keyway.dev"
        self.password = "Secr3tPa$$word"

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_signup_and_login(self):
        # 1. Test Signup
        resp = self.client.post("/api/auth/signup", json={
            "email": self.email,
            "password": self.password
        })
        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()
        self.assertIn("user", data)
        self.assertEqual(data["user"]["email"], self.email)
        
        # Verify user created in DB and salt generated
        user = User.query.filter_by(email=self.email).first()
        self.assertIsNotNone(user)
        self.assertIsNotNone(user.kdf_salt)
        
        # Logout
        self.client.post("/api/auth/logout")
        
        # 2. Test Login
        resp = self.client.post("/api/auth/login", json={
            "email": self.email,
            "password": self.password
        })
        self.assertEqual(resp.status_code, 200)
        
        # Verify user is authenticated
        resp = self.client.get("/api/auth/me")
        data = resp.get_json()
        self.assertTrue(data["authenticated"])
        self.assertTrue(data["has_key"])

    def test_secrets_crud(self):
        # Register and login
        self.client.post("/api/auth/signup", json={
            "email": self.email,
            "password": self.password
        })
        
        # 1. Create Secret
        resp = self.client.post("/api/secrets", json={
            "service_name": "Stripe Live Key",
            "value": "sk_live_123456789abcde",
            "notes": "Used for payment processing",
            "tags": ["stripe", "production"],
            "expiry_date": "2026-12-31"
        })
        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()
        self.assertEqual(data["secret"]["service_name"], "Stripe Live Key")
        self.assertEqual(data["secret"]["masked_value"], "sk_li...bcde") # masked
        
        # Verify DB value is encrypted
        db_secret = Secret.query.filter_by(service_name="Stripe Live Key").first()
        self.assertIsNotNone(db_secret)
        self.assertNotEqual(db_secret.encrypted_value, b"sk_live_123456789abcde")
        
        # 2. List Secrets
        resp = self.client.get("/api/secrets")
        self.assertEqual(resp.status_code, 200)
        secrets = resp.get_json()
        self.assertEqual(len(secrets), 1)
        self.assertEqual(secrets[0]["masked_value"], "sk_li...bcde")
        
        # 3. Reveal Secret
        resp = self.client.post(f"/api/secrets/{db_secret.id}/reveal")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["value"], "sk_live_123456789abcde")
        
        # 4. Update Secret
        resp = self.client.put(f"/api/secrets/{db_secret.id}", json={
            "service_name": "Stripe Live Key V2",
            "value": "sk_live_newkey987654",
            "tags": "stripe,billing"
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["secret"]["service_name"], "Stripe Live Key V2")
        self.assertEqual(resp.get_json()["secret"]["masked_value"], "sk_li...7654")
        
        # 5. Delete Secret
        resp = self.client.delete(f"/api/secrets/{db_secret.id}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Secret.query.count(), 0)

    @patch("requests.request")
    def test_healthcheck_safety_and_execution(self, mock_request):
        # Setup mock responses
        mock_resp_valid = MagicMock()
        mock_resp_valid.status_code = 200
        
        mock_resp_invalid = MagicMock()
        mock_resp_invalid.status_code = 401
        
        # Register and login
        self.client.post("/api/auth/signup", json={
            "email": self.email,
            "password": self.password
        })
        
        # Create secret with healthcheck URL
        resp = self.client.post("/api/secrets", json={
            "service_name": "SendGrid API Key",
            "value": "SG.testkey12345",
            "healthcheck_url": "https://api.sendgrid.com/v3/scopes",
            "healthcheck_method": "GET",
            "healthcheck_auth_style": "bearer"
        })
        secret_id = resp.get_json()["secret"]["id"]
        
        # Test Case 1: Valid API status
        mock_request.return_value = mock_resp_valid
        resp = self.client.post(f"/api/secrets/{secret_id}/healthcheck")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["status"], "valid")
        
        # Verify redirect block and timeout options were passed
        mock_request.assert_called_with(
            method="GET",
            url="https://api.sendgrid.com/v3/scopes",
            headers={"Authorization": "Bearer SG.testkey12345"},
            params={},
            timeout=5,
            allow_redirects=False
        )
        
        # Test Case 2: Invalid status (401 Unauthorized)
        mock_request.return_value = mock_resp_invalid
        resp = self.client.post(f"/api/secrets/{secret_id}/healthcheck")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["status"], "invalid")
        
        # Test Case 3: Connection timeout
        mock_request.side_effect = requests.exceptions.Timeout("Timeout occurred")
        resp = self.client.post(f"/api/secrets/{secret_id}/healthcheck")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["status"], "error")
        self.assertEqual(resp.get_json()["error_message"], "Connection timed out")

    @patch("requests.request")
    def test_healthcheck_test_connection_endpoint(self, mock_request):
        # Register and login
        self.client.post("/api/auth/signup", json={
            "email": self.email,
            "password": self.password
        })
        
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_request.return_value = mock_resp
        
        resp = self.client.post("/api/secrets/test-healthcheck", json={
            "healthcheck_url": "https://api.github.com/user",
            "healthcheck_method": "GET",
            "healthcheck_auth_style": "bearer",
            "value": "ghp_mocktoken"
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["status"], "valid")
        
        mock_request.assert_called_with(
            method="GET",
            url="https://api.github.com/user",
            headers={"Authorization": "Bearer ghp_mocktoken"},
            params={},
            timeout=5,
            allow_redirects=False
        )


if __name__ == "__main__":
    unittest.main()
