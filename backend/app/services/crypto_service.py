import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def derive_key(password: str, salt: bytes, iterations: int = 480000) -> bytes:
    """
    Derive a 32-byte Fernet-compatible key using PBKDF2-HMAC-SHA256.
    Never persisted, derived on-demand at login from user password + DB salt.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
    )
    raw_key = kdf.derive(password.encode())
    return base64.urlsafe_b64encode(raw_key)

def encrypt_value(plaintext: str, fernet_key: bytes) -> bytes:
    """
    Encrypt a plaintext string using the derived Fernet key.
    """
    f = Fernet(fernet_key)
    return f.encrypt(plaintext.encode())

def decrypt_value(ciphertext: bytes, fernet_key: bytes) -> str:
    """
    Decrypt a ciphertext byte string back to plaintext.
    """
    f = Fernet(fernet_key)
    return f.decrypt(ciphertext).decode()
