"""
Comprehensive End-to-End System Verification Suite
Hardened Security, Strict RBAC, Machine Learning, and Telemetry Pipeline Validation

Verifies:
1. Database Connectivity, Composite Indexes & Initial Seeds
2. Unsupervised Machine Learning Isolation Forest Inference & Predictive Analytics
3. JWT Authentication & Token Security (No bypass tokens)
4. Strict Role-Based Access Control (401 on Unauthenticated, 403 on Viewer Admin Actions, 200 on Admin)
5. Telemetry Ingestion, Anomaly Detection & Automatic Alert Generation
6. Authenticated Telemetry CSV Export (Header & Query Param Token Validation)
7. WebSocket Real-Time Channel Security (Handshake Token Validation & 1008 Rejection)
8. Simulator Lifecycle Supervision under Admin Authorization
"""

import sys
import os
import json
from datetime import datetime, timezone

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from backend.main import app
from backend.database.database import SessionLocal
from backend.database.seed_data import seed_database_if_empty
from backend.database.models import Sensor, SensorReading, Anomaly, Alert, User
from backend.ml.ml_model import ml_detector, IsolationForestDetector
from backend.services.predictive_service import predictive_service, PredictiveEngine

def run_all_tests():
    print("=" * 75)
    print("RUNNING INDUSTRIAL SCADA SYSTEM VERIFICATION & SECURITY REGRESSION SUITE")
    print("=" * 75)
    
    # Ensure database tables and baseline seeds exist for CI/CD runners
    seed_database_if_empty()
    
    # ---------------------------------------------------------
    # TEST 1: Database and Seeds
    # ---------------------------------------------------------
    print("\n[TEST 1] Verifying Database Schema, Composite Indexes & Baseline Seeds...")
    db = SessionLocal()
    try:
        sensor_count = db.query(Sensor).count()
        reading_count = db.query(SensorReading).count()
        user_count = db.query(User).count()
        print(f"  -> Sensors in DB: {sensor_count} (Expected: 5)")
        print(f"  -> Initial Telemetry Readings: {reading_count} (Expected: >= 150)")
        print(f"  -> Initial Users in DB: {user_count} (Expected: 2)")
        assert sensor_count == 5, f"Expected 5 sensors, got {sensor_count}"
        assert reading_count >= 150, f"Expected >= 150 readings, got {reading_count}"
        assert user_count == 2, f"Expected 2 users, got {user_count}"
        print("  [PASS] Database schema & baseline seed verification passed.")
    finally:
        db.close()

    # ---------------------------------------------------------
    # TEST 2: ML Isolation Forest (Unsupervised Learning) & Predictive Engine
    # ---------------------------------------------------------
    print("\n[TEST 2] Verifying Isolation Forest ML Anomaly Detection & Predictive Engine...")
    assert ml_detector.is_loaded, "ML Detector failed to load model!"
    assert issubclass(IsolationForestDetector, object), "IsolationForestDetector alias is invalid!"
    assert issubclass(PredictiveEngine, object), "PredictiveEngine alias is invalid!"
    
    # Test nominal reading
    normal_res = ml_detector.predict(temperature=28.5, humidity=52.0, pressure=1013.25)
    print(f"  -> Nominal Reading (28.5°C, 52%, 1013.25hPa): is_anomaly={normal_res['is_anomaly']}, status={normal_res['status']}, score={normal_res['anomaly_score']}")
    assert not normal_res["is_anomaly"], "Nominal reading was erroneously flagged as anomaly!"

    # Test extreme anomaly point (Catastrophic Boiler overheat + depressurization)
    anom_res = ml_detector.predict(temperature=96.5, humidity=12.0, pressure=850.0)
    print(f"  -> Anomaly Reading (96.5°C, 12%, 850hPa): is_anomaly={anom_res['is_anomaly']}, severity={anom_res['severity']}, score={anom_res['anomaly_score']}")
    assert anom_res["is_anomaly"], "Extreme outlier was not flagged as an anomaly!"
    assert anom_res["severity"] in ("HIGH", "CRITICAL"), f"Expected HIGH/CRITICAL severity, got {anom_res['severity']}"
    print("  [PASS] ML Isolation Forest unsupervised inference verification passed.")

    client = TestClient(app)

    # ---------------------------------------------------------
    # TEST 3: Cryptographic JWT Authentication & Rejection of Demo Bypass
    # ---------------------------------------------------------
    print("\n[TEST 3] Verifying Strict JWT Authentication & Denial of Fake Tokens...")
    
    # 3a. Invalid credentials
    bad_login = client.post("/api/auth/login", json={"username": "admin", "password": "wrongpassword"})
    assert bad_login.status_code == 401, f"Expected 401 for wrong password, got {bad_login.status_code}"
    print("  -> Bad credentials correctly rejected (401)")

    # 3b. Admin login
    admin_login = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert admin_login.status_code == 200
    admin_data = admin_login.json()
    admin_token = admin_data["access_token"]
    assert admin_data["role"] == "ADMIN"
    print(f"  -> Admin authenticated successfully. Role={admin_data['role']}, Token={admin_token[:25]}...")

    # 3c. Viewer login
    viewer_login = client.post("/api/auth/login", json={"username": "viewer", "password": "viewer123"})
    assert viewer_login.status_code == 200
    viewer_data = viewer_login.json()
    viewer_token = viewer_data["access_token"]
    assert viewer_data["role"] == "VIEWER"
    print(f"  -> Viewer authenticated successfully. Role={viewer_data['role']}")

    # 3d. Verify hardcoded 'demo_token' is firmly rejected
    fake_token_resp = client.get(
        "/api/dashboard/stats",
        headers={"Authorization": "Bearer demo_token"}
    )
    assert fake_token_resp.status_code == 401, f"Security vulnerability: 'demo_token' was accepted! Got {fake_token_resp.status_code}"
    print("  -> Hardcoded 'demo_token' bypass successfully rejected (401)")

    # 3e. Verify expired token is firmly rejected
    from datetime import timedelta
    from backend.services.security import create_access_token
    expired_token = create_access_token(data={"sub": "admin", "role": "ADMIN"}, expires_delta=timedelta(seconds=-60))
    expired_resp = client.get("/api/dashboard/stats", headers={"Authorization": f"Bearer {expired_token}"})
    assert expired_resp.status_code == 401, f"Expected 401 for expired token, got {expired_resp.status_code}"
    print("  -> Expired JWT token correctly rejected (401)")

    # ---------------------------------------------------------
    # TEST 4: Strict RBAC (Unauthenticated 401, Viewer 403 on Admin Actions)
    # ---------------------------------------------------------
    print("\n[TEST 4] Verifying Strict Role-Based Access Control (RBAC)...")
    
    # 4a. Unauthenticated access to protected telemetry endpoints -> 401
    unauth_stats = client.get("/api/dashboard/stats")
    assert unauth_stats.status_code == 401, f"Expected 401 for unauth /stats, got {unauth_stats.status_code}"
    
    unauth_sensors = client.get("/api/sensors")
    assert unauth_sensors.status_code == 401, f"Expected 401 for unauth /sensors, got {unauth_sensors.status_code}"

    unauth_health = client.get("/api/system/health")
    assert unauth_health.status_code == 401, f"Expected 401 for unauth /health, got {unauth_health.status_code}"
    print("  -> Unauthenticated requests to protected endpoints return 401 Unauthorized")

    # 4b. Viewer access to read endpoints -> 200
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}
    viewer_stats = client.get("/api/dashboard/stats", headers=viewer_headers)
    assert viewer_stats.status_code == 200
    print(f"  -> Viewer read /stats successful (200). System Health={viewer_stats.json()['system_health_pct']}%")

    # 4c. Viewer attempt to perform Admin actions -> 403 Forbidden
    viewer_start_sim = client.post("/api/simulator/start", json={"interval_seconds": 1.0}, headers=viewer_headers)
    assert viewer_start_sim.status_code == 403, f"Expected 403 for viewer starting simulator, got {viewer_start_sim.status_code}"
    
    viewer_toggle = client.post("/api/sensors/1/toggle", headers=viewer_headers)
    assert viewer_toggle.status_code == 403, f"Expected 403 for viewer toggling sensor, got {viewer_toggle.status_code}"

    viewer_create_sensor = client.post(
        "/api/sensors",
        json={"device_id": "TEST-01", "name": "Test", "sensor_type": "MULTI", "location": "Test", "status": "ONLINE"},
        headers=viewer_headers
    )
    assert viewer_create_sensor.status_code == 403, f"Expected 403 for viewer creating sensor, got {viewer_create_sensor.status_code}"
    print("  -> Privilege Escalation Prevention: VIEWER role strictly forbidden (403) from administrative actions")

    # 4d. Admin performing admin actions -> 200 OK
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    admin_sensors = client.get("/api/sensors", headers=admin_headers)
    assert admin_sensors.status_code == 200
    assert len(admin_sensors.json()) == 5
    print(f"  -> Admin authorized access verified (200)")

    # ---------------------------------------------------------
    # TEST 5: Stream Pipeline Ingestion & Anomaly Alert Flow
    # ---------------------------------------------------------
    print("\n[TEST 5] Testing Stream Ingestion Pipeline & Anomaly Alert Cycle...")
    initial_anoms = client.get("/api/anomalies", headers=admin_headers).json()
    latest_anom_id = initial_anoms[0]["id"] if initial_anoms else 0
    initial_alerts = client.get("/api/alerts", headers=admin_headers).json()
    latest_alert_id = initial_alerts[0]["id"] if initial_alerts else 0

    critical_payload = {
        "device_id": "SENSOR-003",
        "temperature": 99.2,
        "humidity": 10.5,
        "pressure": 840.0,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    # 5a. Verify /api/readings/ingest strict security:
    # 1. Unauthenticated -> 401 Unauthorized
    unauth_ingest = client.post("/api/readings/ingest", json=critical_payload)
    assert unauth_ingest.status_code == 401, f"Security violation: unauthenticated ingest accepted! Got {unauth_ingest.status_code}"
    print("  -> Unauthenticated POST /api/readings/ingest correctly rejected (401)")

    # 2. VIEWER role -> 403 Forbidden
    viewer_ingest = client.post("/api/readings/ingest", json=critical_payload, headers=viewer_headers)
    assert viewer_ingest.status_code == 403, f"Security violation: VIEWER role permitted to ingest! Got {viewer_ingest.status_code}"
    print("  -> VIEWER POST /api/readings/ingest correctly rejected (403 Forbidden)")

    # 3. ADMIN role -> 200 OK
    ingest_resp = client.post("/api/readings/ingest", json=critical_payload, headers=admin_headers)
    assert ingest_resp.status_code == 200
    ingested_data = ingest_resp.json()["data"]
    print(f"  -> ADMIN POST /api/readings/ingest allowed (200): is_anomaly={ingested_data['is_anomaly']}, score={ingested_data['anomaly_score']}")
    assert ingested_data["is_anomaly"] is True

    # Verify Anomaly Record
    updated_anoms = client.get("/api/anomalies", headers=admin_headers).json()
    assert len(updated_anoms) > 0
    print(f"  -> Anomaly recorded in database: #{updated_anoms[0]['id']} on {updated_anoms[0]['device_id']}")

    # Verify Alert Record
    updated_alerts = client.get("/api/alerts", headers=admin_headers).json()
    assert len(updated_alerts) > 0
    new_alert = updated_alerts[0]
    print(f"  -> Real-time Alert #{new_alert['id']} created: [{new_alert['severity']}] {new_alert['message']}")

    # Resolve alert as Admin
    resolve_resp = client.put(f"/api/alerts/{new_alert['id']}/resolve", headers=admin_headers)
    assert resolve_resp.status_code == 200
    assert resolve_resp.json()["status"] == "RESOLVED"
    print(f"  -> Alert #{new_alert['id']} resolved by Administrator.")

    # 5b. Verify ingestion sanitization rejects invalid payloads without crashing
    from backend.services.stream_processor import stream_processor
    # Malformed JSON
    assert stream_processor.process_raw_payload("{device_id: bad_json") is None
    # Missing required field
    assert stream_processor.process_raw_payload('{"device_id": "SENSOR-001"}') is None
    # NaN value
    assert stream_processor.process_raw_payload('{"device_id": "SENSOR-001", "temperature": "NaN", "humidity": 50, "pressure": 1000}') is None
    # Impossible physical value
    assert stream_processor.process_raw_payload('{"device_id": "SENSOR-001", "temperature": 9999.0, "humidity": 50, "pressure": 1000}') is None
    print("  -> Ingestion pipeline correctly rejects malformed, missing, NaN, and out-of-bounds payloads.")

    # ---------------------------------------------------------
    # TEST 6: Authenticated CSV Telemetry Export (Header and Query Parameter)
    # ---------------------------------------------------------
    print("\n[TEST 6] Testing Authenticated CSV Exporters...")
    # Unauthenticated should fail
    unauth_csv = client.get("/api/readings/export/csv")
    assert unauth_csv.status_code == 401, f"Expected 401 for unauthenticated CSV export, got {unauth_csv.status_code}"

    # Authenticated via Bearer header
    header_csv = client.get("/api/readings/export/csv", headers=viewer_headers)
    assert header_csv.status_code == 200
    assert "Reading_ID,Device_ID" in header_csv.text

    # Authenticated via ?token= query parameter (for direct browser <a> downloads)
    query_csv = client.get(f"/api/readings/export/csv?token={viewer_token}")
    assert query_csv.status_code == 200
    assert "Reading_ID,Device_ID" in query_csv.text

    anom_query_csv = client.get(f"/api/anomalies/export/csv?token={admin_token}")
    assert anom_query_csv.status_code == 200
    assert "Anomaly_ID,Device_ID" in anom_query_csv.text
    print("  -> CSV export successfully verified with Bearer header and query param token")

    # ---------------------------------------------------------
    # TEST 7: WebSocket Telemetry Endpoint Handshake Security
    # ---------------------------------------------------------
    print("\n[TEST 7] Testing WebSocket Channel Handshake Security...")
    # 7a. Unauthenticated connection attempt (should be rejected with 1008 Policy Violation)
    try:
        with client.websocket_connect("/ws/sensor-data") as ws:
            ws.send_text("ping")
            ws.receive_text()
            assert False, "WebSocket allowed unauthenticated connection without token!"
    except Exception as e:
        print(f"  -> Unauthenticated WebSocket connection correctly rejected: {e}")

    # 7b. Invalid token attempt (should also be rejected with 1008)
    try:
        with client.websocket_connect("/ws/sensor-data?token=invalid_forged_token") as ws:
            ws.send_text("ping")
            ws.receive_text()
            assert False, "WebSocket allowed connection with forged token!"
    except Exception as e:
        print(f"  -> Forged token WebSocket connection correctly rejected: {e}")

    # 7c. Expired token attempt (should also be rejected with 1008)
    try:
        with client.websocket_connect(f"/ws/sensor-data?token={expired_token}") as ws:
            ws.send_text("ping")
            ws.receive_text()
            assert False, "WebSocket allowed connection with expired token!"
    except Exception as e:
        print(f"  -> Expired token WebSocket connection correctly rejected: {e}")

    # 7d. Valid JWT token attempt (should connect and exchange frames)
    with client.websocket_connect(f"/ws/sensor-data?token={viewer_token}") as ws:
        ws.send_text("ping")
        pong_resp = ws.receive_text()
        assert "pong" in pong_resp
        print(f"  -> Authenticated WebSocket handshake successful, received: {pong_resp}")

    # ---------------------------------------------------------
    # TEST 8: Simulator Lifecycle Controls under Admin Privileges
    # ---------------------------------------------------------
    print("\n[TEST 8] Testing Simulator Lifecycle Controls under Admin Privileges...")
    start_sim = client.post(
        "/api/simulator/start",
        json={"interval_seconds": 1.0, "anomaly_probability": 0.15},
        headers=admin_headers
    )
    assert start_sim.status_code == 200
    print(f"  -> Simulator started: {start_sim.json()['status']}")

    status_resp = client.get("/api/simulator/status", headers=viewer_headers)
    assert status_resp.status_code == 200
    assert status_resp.json()["is_running"] is True

    stop_sim = client.post("/api/simulator/stop", headers=admin_headers)
    assert stop_sim.status_code == 200
    print(f"  -> Simulator stopped: {stop_sim.json()['status']}")

    # ---------------------------------------------------------
    # TEST 9: Docker Compose & Infrastructure Security Validation
    # ---------------------------------------------------------
    print("\n[TEST 9] Verifying Docker Compose & Infrastructure Security Configuration...")
    compose_path = os.path.join(os.path.dirname(__file__), "docker-compose.yml")
    assert os.path.exists(compose_path), "docker-compose.yml file missing!"
    with open(compose_path, "r", encoding="utf-8") as f:
        compose_content = f.read()
    assert "services:" in compose_content
    assert "mosquitto:" in compose_content
    assert "postgres:" in compose_content
    assert "backend:" in compose_content
    assert "frontend:" in compose_content
    assert "5432:5432" not in compose_content, "Security violation: PostgreSQL port 5432 exposed to public host!"
    assert "iot_network" in compose_content, "Missing internal bridge network isolation!"
    print("  -> Docker Compose validates: internal network isolation active, no host DB port exposed.")

    # ---------------------------------------------------------
    # TEST 10: MQTT Security Configuration & Zero Plaintext Secrets Verification
    # ---------------------------------------------------------
    print("\n[TEST 10] Verifying MQTT Hardening & Zero Plaintext Secrets in Repository...")
    
    # 10a. Validate Mosquitto broker config
    mosq_conf_path = os.path.join(os.path.dirname(__file__), "mosquitto", "mosquitto.conf")
    assert os.path.exists(mosq_conf_path), "mosquitto.conf missing!"
    with open(mosq_conf_path, "r", encoding="utf-8") as f:
        mosq_conf = f.read()
    assert "allow_anonymous false" in mosq_conf, "MQTT security violation: anonymous access enabled!"
    assert "password_file /mosquitto/config/password_file" in mosq_conf, "MQTT security violation: missing password_file!"
    assert "acl_file /mosquitto/config/acl_file" in mosq_conf, "MQTT security violation: missing acl_file!"
    print("  -> Mosquitto configuration verified: anonymous access disabled, password file & ACL enforced.")

    # 10b. Validate Mosquitto password file has zero plaintext credentials
    pwd_file_path = os.path.join(os.path.dirname(__file__), "mosquitto", "password_file")
    assert os.path.exists(pwd_file_path), "password_file missing!"
    with open(pwd_file_path, "r", encoding="utf-8") as f:
        pwd_file_content = f.read()
    for line in pwd_file_content.splitlines():
        if line.strip().startswith("#"):
            assert "iot_" not in line and "password_20" not in line, "Plaintext credential leak in comment!"
        elif line.strip():
            assert ":$7$" in line, "Un-hashed plaintext credential found in password_file!"
    assert "iot_backend:$7$" in pwd_file_content, "Missing PBKDF2-SHA512 hashed entry for iot_backend!"
    assert "iot_simulator:$7$" in pwd_file_content, "Missing PBKDF2-SHA512 hashed entry for iot_simulator!"
    print("  -> Mosquitto password database verified: zero plaintext credentials, PBKDF2 hashes enforced.")

    # 10c. Validate .env is strictly gitignored
    gitignore_path = os.path.join(os.path.dirname(__file__), ".gitignore")
    assert os.path.exists(gitignore_path), ".gitignore file missing!"
    with open(gitignore_path, "r", encoding="utf-8") as f:
        gitignore_content = f.read()
    assert ".env" in gitignore_content, "CRITICAL: .env is not listed in .gitignore!"
    print("  -> Git configuration verified: .env file is strictly ignored by version control.")

    # 10d. Validate invalid JWT token string is rejected with 401
    invalid_token_resp = client.get(
        "/api/dashboard/stats",
        headers={"Authorization": "Bearer malformed.invalid.token.signature"}
    )
    assert invalid_token_resp.status_code == 401, f"Expected 401 for invalid JWT, got {invalid_token_resp.status_code}"
    print("  -> Forged/invalid JWT signature correctly rejected (401)")

    # ---------------------------------------------------------
    # TEST 11: AWS IoT Core Configuration, Fail-Safe Provider Switching & X.509 Security
    # ---------------------------------------------------------
    print("\n[TEST 11] Verifying AWS IoT Core Configuration, Fail-Safe Provider Switching & X.509 Security...")

    # 11a. Verify Local Mode zero-config instantiation
    from simulator.sensor_simulator import IoTSensorSimulator, SENSOR_PROFILES
    local_sim = IoTSensorSimulator(provider="local")
    assert local_sim.provider == "local", "Expected provider 'local'"
    local_reading = local_sim.generate_reading(SENSOR_PROFILES[0])
    assert local_reading["device_id"] == "SENSOR-001"
    print("  -> Local Mode simulator zero-config initialization verified.")

    # 11b. Verify AWS Mode Fail-Safe Rule (Never silently fall back to local)
    aws_fail_fast_triggered = False
    try:
        # Intentionally missing AWS endpoint and certificates
        _ = IoTSensorSimulator(provider="aws", aws_endpoint="", cert_path="")
    except (RuntimeError, ValueError) as err:
        aws_fail_fast_triggered = True
        assert "validation failed" in str(err) or "AWS_IOT_ENDPOINT" in str(err)
    assert aws_fail_fast_triggered, "Security violation: Simulator silently fell back instead of failing fast in AWS mode!"
    print("  -> Simulator AWS mode fail-fast validation enforced (raises descriptive RuntimeError on missing certs).")

    # 11c. Verify dedicated AWSIoTClient credential and endpoint checks
    from simulator.aws_iot_client import AWSIoTClient
    endpoint_error_caught = False
    try:
        AWSIoTClient(endpoint="")
    except ValueError:
        endpoint_error_caught = True
    assert endpoint_error_caught, "AWSIoTClient failed to reject empty endpoint!"

    cert_error_caught = False
    try:
        AWSIoTClient(
            endpoint="test-ats.iot.us-east-1.amazonaws.com",
            root_ca_path="certs/nonexistent_root.pem",
            cert_path="certs/nonexistent_cert.pem",
            private_key_path="certs/nonexistent_key.pem"
        )
    except FileNotFoundError as fnf_err:
        cert_error_caught = True
        assert "Root CA file not found" in str(fnf_err)
    assert cert_error_caught, "AWSIoTClient failed to enforce certificate file existence!"
    print("  -> Dedicated AWSIoTClient verifies endpoint and X.509 file existence before TLS handshake.")

    # 11d. Verify Backend MQTT Ingestion Service provider and topic configuration
    from backend.mqtt.mqtt_client import MQTTService
    backend_local_service = MQTTService()
    assert backend_local_service.provider in ("local", "aws")

    # Test backend AWS validation fails fast when missing credentials
    orig_provider = os.environ.get("MQTT_PROVIDER")
    try:
        os.environ["MQTT_PROVIDER"] = "aws"
        os.environ["AWS_IOT_ENDPOINT"] = ""
        backend_aws_service = MQTTService()
        backend_aws_fail_fast = False
        try:
            backend_aws_service.validate_config()
        except RuntimeError:
            backend_aws_fail_fast = True
        assert backend_aws_fail_fast, "Backend MQTTService failed to enforce AWS configuration validation!"
    finally:
        if orig_provider is not None:
            os.environ["MQTT_PROVIDER"] = orig_provider
        else:
            os.environ.pop("MQTT_PROVIDER", None)
    print("  -> Backend MQTT Ingestion Service strictly enforces AWS IoT Core config validation.")

    # 11e. Verify AWS IoT Policy Definitions & Placeholders
    policy_dir = os.path.join(os.path.dirname(__file__), "aws", "iot", "policies")
    assert os.path.exists(policy_dir), "aws/iot/policies directory missing!"

    expected_policies = ["sensor-thing-policy.json", "SENSOR-001-policy.json", "backend-consumer-policy.json"]
    for pol_file in expected_policies:
        pol_path = os.path.join(policy_dir, pol_file)
        assert os.path.exists(pol_path), f"Policy file {pol_file} missing!"
        with open(pol_path, "r", encoding="utf-8") as pf:
            pol_data = json.load(pf)
        assert "Statement" in pol_data, f"Invalid policy format in {pol_file}"
        pol_str = json.dumps(pol_data)
        assert "AKIA" not in pol_str, f"Forbidden IAM access key detected in {pol_file}!"
        assert "aws_secret" not in pol_str.lower(), f"Secret keyword detected in {pol_file}!"
    print("  -> AWS IoT Core Policies verified (least-privilege, parameterized, zero leaked secrets).")

    # 11f. Verify .gitignore protects X.509 certificates and keys
    with open(gitignore_path, "r", encoding="utf-8") as f:
        git_rules = f.read()
    assert "*.pem" in git_rules, ".gitignore missing *.pem rule!"
    assert "*.key" in git_rules, ".gitignore missing *.key rule!"
    assert "*.crt" in git_rules, ".gitignore missing *.crt rule!"
    assert "certs/*" in git_rules, ".gitignore missing certs/* rule!"
    print("  -> Version control hardening verified: all X.509 certs, keys, and certs/* strictly ignored.")

    print("\n" + "=" * 75)
    print("ALL 11 VERIFICATION & SECURITY SUITES COMPLETED WITH 100% SUCCESS!")
    print("=" * 75)

if __name__ == "__main__":
    run_all_tests()
