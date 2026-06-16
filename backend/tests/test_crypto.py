import unittest
import os
import base64
from app.services.crypto_service import derive_key, encrypt_value, decrypt_value
from cryptography.fernet import InvalidToken

class TestCryptoService(unittest.TestCase):
    def setUp(self):
        self.password = "SuperSecurePassword123!"
        self.salt = os.urandom(16)
        self.plaintext = "sk_live_test_key_abc123"

    def test_key_derivation_determinism(self):
        # The same password and salt should yield the same key
        key1 = derive_key(self.password, self.salt, iterations=1000)
        key2 = derive_key(self.password, self.salt, iterations=1000)
        self.assertEqual(key1, key2)
        # The key should be 32 base64 urlsafe bytes (length of Fernet key is 44 characters in base64)
        self.assertEqual(len(key1), 44)

    def test_key_derivation_uniqueness(self):
        # Different passwords should yield different keys
        key1 = derive_key(self.password, self.salt, iterations=1000)
        key2 = derive_key("DifferentPassword123!", self.salt, iterations=1000)
        self.assertNotEqual(key1, key2)
        
        # Different salts should yield different keys
        another_salt = os.urandom(16)
        key3 = derive_key(self.password, another_salt, iterations=1000)
        self.assertNotEqual(key1, key3)

    def test_encrypt_decrypt_roundtrip(self):
        key = derive_key(self.password, self.salt, iterations=1000)
        ciphertext = encrypt_value(self.plaintext, key)
        self.assertNotEqual(self.plaintext.encode(), ciphertext)
        
        decrypted = decrypt_value(ciphertext, key)
        self.assertEqual(self.plaintext, decrypted)

    def test_decrypt_with_wrong_key_fails(self):
        key_correct = derive_key(self.password, self.salt, iterations=1000)
        key_wrong = derive_key("WrongPassword", self.salt, iterations=1000)
        ciphertext = encrypt_value(self.plaintext, key_correct)
        
        with self.assertRaises(InvalidToken):
            decrypt_value(ciphertext, key_wrong)

if __name__ == "__main__":
    unittest.main()
