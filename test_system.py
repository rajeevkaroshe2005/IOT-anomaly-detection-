"""
Comprehensive End-to-End System Verification Suite
Verifies:
1. Database Connectivity & Initial Seeds
2. Machine Learning Isolation Forest Inference
3. REST API Endpoints (Sensors, Stats, Health, Auth)
4. Stream Processing Pipeline Ingestion
5. Anomaly Detection & Automatic Alert Generation
6. Simulator Process Control
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
from backend.database.models import Sensor, SensorReading, Anomaly, Alert, User
from backend.ml.ml_model import ml_detector

def run_all_tests():
    print("=" * 70)
    print("RUNNING COMPREHENSIVE INDUSTRIAL IOT SYSTEM VERIFICATION")
    print("=" * 70)
    
    # 1. Test Database and Seeds
    print("\n[TEST 1] Verifying Database Schema & Initial Seeding...")
    db = SessionLocal()
    try:
        sensor_count = db.query(Sensor).count()
        reading_count = db.query(SensorReading).count()
        user_count = db.query(User).count()
        print(f"  -> Sensors in DB: {sensor_count} (Expected: 5)")
        print(f"  -> Initial Readings in DB: {reading_count} (Expected: >= 150)")
        print(f"  -> Initial Users in DB: {user_count} (Expected: 2)")
        assert sensor_count == 5, f"Expected 5 sensors, got {sensor_count}"
        assert reading_count >= 150, f"Expected >=150 readings, got {reading_count}"
        assert user_count == 2, f"Expected 2 users, got {user_count}"
        print("  [PASS] Database seed verification passed.")
    finally:
        db.close()

    # 2. Test ML Isolation Forest
    print("\n[TEST 2] Verifying Isolation Forest ML Anomaly Detection...")
    assert ml_detector.is_loaded, "ML Detector failed to load model!"
    
    # Test nominal point
    normal_res = ml_detector.predict(temperature=28.5, humidity=52.0, pressure=1013.25)
    print(f"  -> Nominal Reading (28.5°C, 52%, 1013.25hPa): is_anomaly={normal_res['is_anomaly']}, status={normal_res['status']}, score={normal_res['anomaly_score']}")
    assert not normal_res["is_anomaly"], "Nominal reading was erroneously flagged as anomaly!"

    # Test extreme anomaly point (Boiler overheat)
    anom_res = ml_detector.predict(temperature=96.5, humidity=12.0, pressure=850.0)
    print(f"  -> Anomaly Reading (96.5°C, 12%, 850hPa): is_anomaly={anom_res['is_anomaly']}, severity={anom_res['severity']}, score={anom_res['anomaly_score']}")
    assert anom_res["is_anomaly"], "Extreme outlier was not flagged as an anomaly!"
    assert anom_res["severity"] in ("HIGH", "CRITICAL"), f"Expected HIGH/CRITICAL severity, got {anom_res['severity']}"
    print("  [PASS] ML Isolation Forest inference verification passed.")

    # 3. Test REST API Endpoints with TestClient
    print("\n[TEST 3] Verifying REST API Endpoints via HTTP TestClient...")
    client = TestClient(app)

    # 3a. Root Health probe
    root_resp = client.get("/")
    assert root_resp.status_code == 200
    print(f"  -> Root probe: {root_resp.json()['service']}")

    # 3b. Dashboard Stats
    stats_resp = client.get("/api/dashboard/stats")
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    print(f"  -> Dashboard Stats: Total Sensors={stats['total_sensors']}, Online={stats['online_sensors']}, Readings={stats['total_readings']}, Health={stats['system_health_pct']}%")
    assert stats["total_sensors"] == 5
    assert stats["online_sensors"] >= 4

    # 3c. Sensors List
    sensors_resp = client.get("/api/sensors")
    assert sensors_resp.status_code == 200
    sensors_list = sensors_resp.json()
    print(f"  -> Sensors endpoint returned {len(sensors_list)} sensors: {[s['device_id'] for s in sensors_list]}")
    assert len(sensors_list) == 5

    # 3d. Authentication
    login_resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    admin_token = token_data["access_token"]
    print(f"  -> Admin login successful. Role={token_data['role']}, Token={admin_token[:20]}...")

    # 3e. System Health
    health_resp = client.get("/api/system/health")
    assert health_resp.status_code == 200
    health_data = health_resp.json()
    print(f"  -> System Health: Overall={health_data['overall_status']}, Subsystems={len(health_data['subsystems'])}")
    for sub in health_data["subsystems"]:
        print(f"     - {sub['name']}: {sub['status']}")

    # 4. Ingest Reading through Stream Processing Pipeline
    print("\n[TEST 4] Testing Stream Pipeline Ingestion & Anomaly Alert Flow...")
    initial_anoms = client.get("/api/anomalies").json()
    latest_anom_id = initial_anoms[0]["id"] if initial_anoms else 0
    initial_alerts = client.get("/api/alerts").json()
    latest_alert_id = initial_alerts[0]["id"] if initial_alerts else 0

    # Ingest a critical anomaly payload on SENSOR-003 (Boiler Room)
    critical_payload = {
        "device_id": "SENSOR-003",
        "temperature": 98.4,
        "humidity": 11.2,
        "pressure": 845.0,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    ingest_resp = client.post("/api/readings/ingest", json=critical_payload)
    assert ingest_resp.status_code == 200
    ingested_data = ingest_resp.json()["data"]
    print(f"  -> Ingested critical payload: is_anomaly={ingested_data['is_anomaly']}, score={ingested_data['anomaly_score']}")
    assert ingested_data["is_anomaly"] is True

    # Verify Anomaly Record was saved
    updated_anoms = client.get("/api/anomalies").json()
    assert len(updated_anoms) > 0
    assert updated_anoms[0]["id"] > latest_anom_id or updated_anoms[0]["device_id"] == "SENSOR-003"
    print(f"  -> Anomaly verified: latest id={updated_anoms[0]['id']} on {updated_anoms[0]['device_id']}")

    # Verify Alert Record was generated
    updated_alerts = client.get("/api/alerts").json()
    assert len(updated_alerts) > 0
    new_alert = updated_alerts[0]
    assert new_alert["id"] > latest_alert_id or new_alert["device_id"] == "SENSOR-003"
    print(f"  -> New Alert Generated: #{new_alert['id']} [{new_alert['severity']}] {new_alert['message']}")

    # Test Resolving Alert as Admin
    resolve_resp = client.put(
        f"/api/alerts/{new_alert['id']}/resolve",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resolve_resp.status_code == 200
    assert resolve_resp.json()["status"] == "RESOLVED"

    # 5. Test Predictive Analytics & CSV Export
    print("\n[TEST 5] Testing Predictive RUL Engine & CSV Exporter...")
    pred_resp = client.get("/api/predictive/analytics")
    assert pred_resp.status_code == 200
    pred_data = pred_resp.json()
    print(f"  -> Predictive Analytics Fleet Status: {pred_data['fleet_risk_status']}")
    print(f"  -> Sensor Forecast Count: {len(pred_data['sensor_forecasts'])}")

    readings_csv = client.get("/api/readings/export/csv")
    assert readings_csv.status_code == 200
    assert "Reading_ID,Device_ID" in readings_csv.text
    print("  -> Readings CSV Export verified")

    anoms_csv = client.get("/api/anomalies/export/csv")
    assert anoms_csv.status_code == 200
    assert "Anomaly_ID,Device_ID" in anoms_csv.text
    print("  -> Anomalies CSV Export verified")
    print(f"  -> Alert #{new_alert['id']} successfully resolved by Administrator.")

    # 6. Test Simulator Controls
    print("\n[TEST 6] Testing Simulator Service Controls...")
    sim_status = client.get("/api/simulator/status").json()
    print(f"  -> Initial Simulator Status: Running={sim_status['is_running']}")
    
    start_sim = client.post("/api/simulator/start", json={"interval_seconds": 1.0, "anomaly_probability": 0.2})
    assert start_sim.status_code == 200
    print(f"  -> Start Simulator Response: {start_sim.json()}")
    
    active_status = client.get("/api/simulator/status").json()
    assert active_status["is_running"] is True
    print(f"  -> Simulator successfully running in background.")
    
    stop_sim = client.post("/api/simulator/stop")
    assert stop_sim.status_code == 200
    print(f"  -> Simulator successfully stopped.")

    print("\n" + "=" * 70)
    print("ALL 5 CORE VERIFICATION SUITES PASSED WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == "__main__":
    run_all_tests()
