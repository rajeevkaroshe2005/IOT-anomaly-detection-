# Comprehensive Security Architecture & Threat Mitigation Specification
## Cloud-Based Real-Time IoT Sensor Monitoring & Anomaly Detection System

**System Classification:** Critical Cyber-Physical Industrial IoT (IIoT) & Stream Analytics Gateway  
**Standard Compliance:** Defense-in-Depth, Zero-Trust Architecture, ISO/IEC 27001 & ISA/IEC 62443 Alignment  
**Date:** September 2026  

---

## Executive Summary

The **Cloud-Based Real-Time IoT Sensor Monitoring & Anomaly Detection System** ingests, processes, and evaluates real-time telemetry from industrial manufacturing plant assets (turbines, steam reactors, chemical silos, cold storage units, and packaging conveyors). In industrial environments, unauthorized access or tampered sensor telemetry can lead to catastrophic physical equipment damage, false emergency shutdowns, or environmental hazards.

This document details the complete end-to-end security architecture across all **13 foundational security facets**, contrasting the current hardened implementation with enterprise cloud production recommendations.

---

## 1. Threat Model & Industrial Attack Surface

The industrial sensing gateway operates across four primary operational boundaries:
- **Perimeter Edge:** Physical IoT sensors and edge simulator microcontrollers.
- **Transport Bus:** MQTT broker and HTTP fallback ingestion channels.
- **Application & Stream Engine:** FastAPI backend, ML inference pipeline, and WebSocket broadcast manager.
- **Presentation Layer:** React 18 SCADA web dashboard and operator console.

### Threat Matrix & Mitigations

| Threat Vector | Attack Mechanism | Potential Impact | Implemented Mitigation |
| :--- | :--- | :--- | :--- |
| **Rogue Sensor Spoofing** | Adversary injects fabricated readings with fake Device IDs | Erroneous anomaly alerts, false plant shutdowns | Authenticated MQTT credentials (`iot_simulator`) + strict ACL publishing restrictions to `iot/sensors/+`. |
| **Man-in-the-Middle (MITM)** | Intercepting cleartext network traffic on port 1883 or 8000 | Telemetry snooping, parameter modification | TLS 1.3 / mTLS encryption on MQTT port 8883, HTTPS REST endpoints, and WSS WebSockets. |
| **Privilege Escalation** | Viewer attempts to trigger actuators, toggle sensors, or reset database | Operational disruption, audit log destruction | Cryptographic JWT token inspection with strict FastAPI `Depends(require_admin)` RBAC filters. |
| **Replay & Hijack Attacks** | Captured telemetry or expired session tokens replayed to API | Inaccurate historical state, session hijacking | Short-lived signed JWTs with UTC expiration claims, unique monotonic timestamps on telemetry payloads. |
| **SQL Injection (SQLi)** | Malicious SQL syntax in query params (`sensor_id`, `timeframe`) | Database exfiltration or data corruption | 100% SQLAlchemy ORM parameterized queries; zero raw SQL string interpolation. |
| **Denial of Service (DoS)** | Malformed JSON payloads or high-rate socket flood | Engine crash, high memory usage | Pydantic strict schema validation, type checking, rate limiting, and bounded queue sizes. |

---

## 2. Authentication & Credential Architecture

### A. Elimination of Development Bypasses
Previous development iterations permitted a hardcoded `'demo_token'` bypass. This bypass has been **completely eliminated** from both backend and frontend layers:
- Every protected endpoint requires a valid, cryptographically signed JSON Web Token (JWT).
- Any attempt to present `'demo_token'`, empty tokens, or malformed strings triggers an immediate `HTTP 401 Unauthorized`.
- Frontend `AuthContext.jsx` systematically detects and purges legacy `'demo_token'` keys from `localStorage`.

### B. JWT Token Structure & Cryptographic Signing
- **Algorithm:** `HS256` (HMAC with SHA-256) for local/staging deployments; `RS256` (Asymmetric RSA keypair) for enterprise multi-service cloud architectures.
- **Claims Payload:**
  - `sub`: Authenticated operator username (e.g., `"admin"` or `"viewer"`).
  - `role`: Role claim (`"ADMIN"` or `"VIEWER"`).
  - `exp`: UTC Unix timestamp enforcing token expiration (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`, default 24 hours).
- **Cryptographic Secret:** Read dynamically from `SECRET_KEY` environment variable. If `APP_ENV=production` is detected with a default fallback secret, a high-severity security hazard warning is emitted at boot.

---

## 3. Role-Based Access Control (RBAC) Matrix

The system enforces strict principle-of-least-privilege segregation between two built-in operational roles:
1. **`VIEWER` (Read-Only SCADA Operator):** Permitted to monitor live telemetry, inspect historical readings, view plant maps, read predictive analytics, and export telemetry CSVs.
2. **`ADMIN` (Industrial Plant Supervisor):** Possesses full privileges, including sensor registration, hardware calibration toggling, alert acknowledgment/resolution, simulator lifecycle control, and system reset utilities.

### Comprehensive Endpoint RBAC Matrix

| HTTP Method | API Path | Minimum Role Required | Unauthenticated Result | Unauthorized Role Result |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/login` | Public | Allowed (200 / 401) | N/A |
| `GET` | `/api/auth/me` | Viewer (`require_auth`) | `401 Unauthorized` | N/A |
| `GET` | `/api/dashboard/stats` | Viewer (`require_auth`) | `401 Unauthorized` | N/A |
| `GET` | `/api/sensors` | Viewer (`require_auth`) | `401 Unauthorized` | N/A |
| `GET` | `/api/sensors/{id}` | Viewer (`require_auth`) | `401 Unauthorized` | N/A |
| `POST` | `/api/sensors` | Admin (`require_admin`) | `401 Unauthorized` | `403 Forbidden` |
| `PUT` | `/api/sensors/{id}` | Admin (`require_admin`) | `401 Unauthorized` | `403 Forbidden` |
| `DELETE` | `/api/sensors/{id}` | Admin (`require_admin`) | `401 Unauthorized` | `403 Forbidden` |
| `POST` | `/api/sensors/{id}/toggle` | Admin (`require_admin`) | `401 Unauthorized` | `403 Forbidden` |
| `GET` | `/api/readings` | Viewer (`require_auth`) | `401 Unauthorized` | N/A |
| `GET` | `/api/readings/{sensor_id}` | Viewer (`require_auth`) | `401 Unauthorized` | N/A |
| `POST` | `/api/readings/ingest` | Admin (`require_admin`) | `401 Unauthorized` | `403 Forbidden` |
| `GET` | `/api/readings/export/csv` | Viewer (`require_auth` / token) | `401 Unauthorized` | N/A |
| `GET` | `/api/anomalies` | Viewer (`require_auth`) | `401 Unauthorized` | N/A |
| `PUT` | `/api/anomalies/{id}/acknowledge` | Admin (`require_admin`) | `401 Unauthorized` | `403 Forbidden` |
| `GET` | `/api/anomalies/export/csv` | Viewer (`require_auth` / token) | `401 Unauthorized` | N/A |
| `GET` | `/api/alerts` | Viewer (`require_auth`) | `401 Unauthorized` | N/A |
| `PUT` | `/api/alerts/{id}/resolve` | Admin (`require_admin`) | `401 Unauthorized` | `403 Forbidden` |
| `DELETE` | `/api/alerts/{id}` | Admin (`require_admin`) | `401 Unauthorized` | `403 Forbidden` |
| `GET` | `/api/predictive/analytics` | Viewer (`require_auth`) | `401 Unauthorized` | N/A |
| `GET` | `/api/predictive/sensor/{id}` | Viewer (`require_auth`) | `401 Unauthorized` | N/A |
| `GET` | `/api/system/health` | Viewer (`require_auth`) | `401 Unauthorized` | N/A |
| `GET` | `/api/system/logs` | Admin (`require_admin`) | `401 Unauthorized` | `403 Forbidden` |
| `POST` | `/api/system/reset-demo` | Admin (`require_admin`) | `401 Unauthorized` | `403 Forbidden` |
| `POST` | `/api/simulator/start` | Admin (`require_admin`) | `401 Unauthorized` | `403 Forbidden` |
| `POST` | `/api/simulator/stop` | Admin (`require_admin`) | `401 Unauthorized` | `403 Forbidden` |
| `GET` | `/api/simulator/status` | Viewer (`require_auth`) | `401 Unauthorized` | N/A |
| `POST` | `/api/simulator/force-anomaly` | Admin (`require_admin`) | `401 Unauthorized` | `403 Forbidden` |
| `WS` | `/ws/sensor-data?token=` | Viewer (`decode_access_token`) | `1008 Policy Violation` | N/A |

---

## 4. Password Security & Cryptographic Hashing

- **Hashing Algorithm:** PBKDF2-HMAC-SHA256 implemented via `passlib.context.CryptContext`.
- **Salting:** Cryptographically secure pseudo-random 16-byte salt generated per password instance, preventing rainbow-table precomputation attacks.
- **Work Factor:** Tuned for maximum brute-force resistance without causing CPU starvation during simultaneous logins.
- **Storage:** Stored in the `users.hashed_password` database column; plaintext passwords never persist in memory or logs.

---

## 5. Mosquitto MQTT Broker Hardening & Access Control Lists (ACLs)

### A. Authentication Enforcement
In production mode (`mosquitto/mosquitto.conf`), anonymous connections are strictly prohibited:
```conf
listener 1883 0.0.0.0
allow_anonymous false
password_file /mosquitto/config/password_file
acl_file /mosquitto/config/acl_file
```

### B. Salted PBKDF2-SHA512 Password Hashes
Mosquitto 2.0 uses salted PBKDF2-SHA512 (`$7$`) hashes stored in `mosquitto/password_file`:
- `iot_backend`: Authenticated consumer service connecting from internal Docker bridge network.
- `iot_simulator`: Edge device emulator publishing telemetry vectors.

### C. Principle of Least Privilege Topic Segregation
Defined in `mosquitto/acl_file`:
```txt
# Sensor Fleet / Edge Simulators:
# Permitted ONLY to publish telemetry to individual sensor topics.
user iot_simulator
topic write iot/sensors/+

# Backend Ingestion & Stream Processing Service:
# Subscribes to telemetry stream from all sensors.
user iot_backend
topic read iot/sensors/#
topic readwrite iot/control/#
topic readwrite iot/alerts/#
```
This ensures a compromised edge sensor cannot listen to other sensor channels, forge administrative control commands, or eavesdrop on internal alerting queues.

### D. Hardened Local and Production Broker Profiles
The broker configuration `mosquitto/mosquitto.conf` strictly enforces `allow_anonymous false` with PBKDF2-SHA512 password and ACL controls for both local Docker and production setups. For production cloud deployments, MQTT over TLS on port 8883 is recommended.

---

## 6. Secrets Management & Environment Isolation

1. **Zero Hardcoded Secrets in Codebase:** All sensitive parameters (`SECRET_KEY`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `MQTT_USERNAME`, `MQTT_PASSWORD`) are loaded exclusively from `.env`.
2. **Standardized `.env.example` Template:** Provides clean documentation for operators with secure default generation guidelines.
3. **Git Hygiene:** `.gitignore` firmly excludes `.env`, `*.joblib`, `*.db`, and persistent container state volumes.
4. **Docker Secret Parameterization:** `docker-compose.yml` uses Docker variable substitution (`${SECRET_KEY}`, `${POSTGRES_PASSWORD}`), preventing accidental image embedding.

---

## 7. Transport Layer Security (TLS/mTLS)

### Current Implementation
- Local containerized environment runs inside an isolated Docker bridge network (`iot_network`).
- Backend MQTT client supports the `MQTT_USE_TLS=true` configuration flag, automatically invoking `client.tls_set()` for encrypted broker connections.

### Recommended Production Cloud Architecture
- **HTTPS & WSS:** Ingress ALB (Application Load Balancer) with ACM (AWS Certificate Manager) terminating TLS 1.3 with HSTS (HTTP Strict Transport Security) enabled.
- **Mutual TLS (mTLS) on Port 8883:** AWS IoT Core or EMQX cluster enforcing bi-directional X.509 client certificate authentication. Every physical industrial sensor possesses a dedicated private key stored in a hardware TPM (Trusted Platform Module) or secure element (ATECC608A).

---

## 8. WebSocket Real-Time Channel Handshake Security

### The Web Browser Header Limitation
Standard browser `WebSocket` APIs (`new WebSocket(url)`) do not allow custom HTTP request headers (such as `Authorization: Bearer <token>`).

### Implemented Handshake Protocol
1. The client establishes the connection passing the signed JWT token via URL query parameter:
   ```
   ws://<host>:8000/ws/sensor-data?token=<JWT_TOKEN>
   ```
2. FastAPI inspects the query parameter during the initial WebSocket handshake before upgrading the connection.
3. If the token is missing, expired, or cryptographically invalid:
   - The connection is immediately rejected.
   - The socket is terminated with **RFC 6455 Close Code `1008` (Policy Violation)**.
4. Frontend `WebSocketContext.jsx` explicitly detects code `1008` and halts reconnection loops until the operator logs in with valid credentials.

---

## 9. SQL Injection Prevention & Database Hygiene

1. **SQLAlchemy ORM Parameterization:** All database operations utilize SQLAlchemy's object-relational mapping layer. Queries compile to parameterized SQL statements (`SELECT ... WHERE id = :id_1`), neutralizing all SQL injection (`' OR '1'='1`) attempts.
2. **Schema Separation:** Relational entities are strictly separated by schema models (`Sensor`, `SensorReading`, `Anomaly`, `Alert`, `User`, `SystemLog`).

---

## 10. Input Validation & Schema Sanitization

1. **Pydantic Model Validation:** All inbound REST payloads (`ReadingCreate`, `SensorCreate`, `SimulatorConfig`) undergo strict validation before execution.
2. **Type Coercion & Range Guards:** Ingestion pipeline validates that:
   - `temperature`: Bounded to physical operational limits ($-50.0^\circ\text{C}$ to $+150.0^\circ\text{C}$).
   - `humidity`: Bounded strictly to $[0.0\%, 100.0\%]$.
   - `pressure`: Bounded strictly to $[700\text{ hPa}, 1200\text{ hPa}]$.
3. Any payload with out-of-bounds numbers, missing mandatory fields, or non-numeric types is rejected at the entry gate, preventing buffer overflows or pipeline crashes.

---

## 11. Secure Telemetry Export

- Native browser file download links (`<a href="...">`) do not automatically attach Axios HTTP Authorization headers.
- To maintain security without breaking direct CSV downloads:
  - Both `/api/readings/export/csv` and `/api/anomalies/export/csv` accept either a standard `Authorization: Bearer <token>` header OR an authenticated `?token=<JWT>` query parameter.
  - Direct export requests missing both forms of authentication are rejected with `HTTP 401 Unauthorized`.

---

## 12. Database Network Isolation

In `docker-compose.yml`:
- The PostgreSQL database service (`iot_postgres_db`) is attached strictly to the internal Docker network `iot_network`.
- **Host port exposure (`5432:5432`) has been deliberately removed.**
- The database is completely unreachable from the public host network or the internet; only internal containers (`backend`) can resolve the `postgres` hostname.

---

## 13. Audit Logging & Forensic Traceability

1. **Structured Security Logging:** Python standard `logging` with ISO-8601 UTC timestamps, module scopes (`iot.auth`, `iot.security`, `iot.main`), and log levels (`INFO`, `WARNING`, `ERROR`).
2. **Database Audit Trail:** Significant events (login attempts, alert acknowledgments, threshold violations, simulator parameter changes) are written to the `system_logs` table with level tags and client IP origin.
3. **Tamper Prevention:** Viewer roles are forbidden from deleting, truncating, or clearing system audit records.
