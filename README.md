# 🔑 Keyway — Encrypted Secrets Vault

**[Demo, architecture diagram and install steps](https://akshitmehta.pages.dev/projects/keyway/)**

Keyway is a self-hosted secrets vault designed specifically for developers to manage API keys, tokens, and credentials. Unlike a generic password manager, Keyway tracks key expiration dates and runs on-demand health checks to verify that keys are still valid against actual provider APIs.

---

## 🔒 Security & Cryptographic Design

Keyway uses a strict **zero-persistence** model for raw encryption keys, which is explainable in security reviews and interviews:

### 1. Key Derivation (KDF)
- Every user is assigned a cryptographically secure random 16-byte salt (`kdf_salt`) during signup.
- Keyway never stores the decryption key in the database or disk. Instead, when you log in, Keyway derives a 32-byte symmetric Fernet key from your password and your unique salt using **PBKDF2-HMAC-SHA256** with **480,000 iterations** (exceeding OWASP 2026 security recommendation minimums).
- The key is derived deterministically: the same password always produces the same key.

### 2. Session-Only Memory Storage
- Once derived at login, the Fernet key is stored **only in the server-side Flask-Session** (`session['fernet_key']`).
- When running in Docker, session data is cached in a secure **Redis** container. When running locally without Redis, it falls back to a server-side filesystem session store.
- The derived key **never** leaves the server memory (it is never sent to the client, cookies only store a signed session identifier).
- Logging out immediately terminates the session and destroys the key memory.

### 3. Threat Model & Boundaries
- **Protected Against**: Database leaks. If an attacker gains full access to the SQL database, they only get binary ciphertexts and salts. They cannot decrypt anything without performing a brute-force attack on the 480,000-iteration PBKDF2 hash.
- **Out of Scope**: Full machine compromise. If an attacker gains root/admin shell access to the host server during active user sessions, they can read the server's RAM or cache to extract the key. Keyway is designed as a local/private self-hosted utility, not a multi-tenant enterprise system.

---

## ⚡ Healthcheck Safety Controls

To ensure outbound checks do not expose your credentials:
1. **Redirects Blocked (`allow_redirects=False`)**: Prevents a redirect from silently sending the authorization header to an unexpected domain.
2. **Short Timeouts (5s)**: Outbound requests timeout after 5 seconds to prevent slow external APIs from hanging backend worker processes.
3. **No Response Logging**: Keyway inspects only the HTTP status code (e.g. `< 400` is valid) and discards the response body immediately to prevent logging APIs that echo back keys in error messages.
4. **Method Restrictions**: Only `GET`, `POST`, and `HEAD` methods are permitted.

---

## 🛠️ Development & Setup

### Option 1: Docker Compose (Recommended)
This runs the entire production-ready stack: PostgreSQL database, Redis session cache, Gunicorn backend, and Nginx frontend.

1. Clone the repository and navigate inside:
   ```bash
   cd wonderful-lavoisier
   ```
2. Copy the environment template:
   ```bash
   cp .env.example .env
   ```
3. Boot the containers:
   ```bash
   docker-compose up --build
   ```
4. Access the application at [http://localhost:8080](http://localhost:8080).

### Option 2: Local Development (SQLite & Filesystem Sessions)
Ideal for testing or quick hacks without Docker.

#### Backend
1. Create a virtual environment and install requirements:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r backend/requirements.txt
   ```
2. Run backend development server (starts on `http://127.0.0.1:5000`):
   ```bash
   python backend/run.py
   ```

   > **macOS:** port 5000 is used by AirPlay Receiver, so sign-up and login fail with a 403. Run the backend on another port and point the frontend at it:
   > ```bash
   > FLASK_RUN_PORT=5055 python backend/run.py
   > VITE_API_BASE_URL=http://localhost:5055 npm run dev   # from frontend/
   > ```

#### Frontend
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   npm install
   ```
2. Run development server (starts on `http://localhost:5173`):
   ```bash
   npm run dev
   ```

---

## 🧪 Running Tests

A comprehensive unit and integration test suite is provided. To execute:

```bash
source venv/bin/activate
PYTHONPATH=backend python -m unittest discover -s backend/tests/
```
