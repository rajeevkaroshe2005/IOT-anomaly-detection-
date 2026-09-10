"""
Database Auto-Seeder & Historical Data Generator
Initializes schema, default admin/viewer users, 5 industrial sensors,
and pre-populates 150+ realistic readings, anomalies, and alerts.
"""

from datetime import datetime, timedelta, timezone
import random
import logging
from sqlalchemy.orm import Session
from .database import Base, engine, SessionLocal
from .models import User, Sensor, SensorReading, Anomaly, Alert, SystemLog
from backend.services.security import get_password_hash

logger = logging.getLogger("iot.seed")

DEMO_SENSORS = [
    {
        "device_id": "SENSOR-001",
        "name": "Main Assembly Line 1",
        "location": "Production Floor",
        "status": "ONLINE",
        "base_temp": 28.5,
        "base_hum": 52.0,
        "base_press": 1013.25
    },
    {
        "device_id": "SENSOR-002",
        "name": "Cold Storage Unit 3",
        "location": "Warehouse",
        "status": "ONLINE",
        "base_temp": 18.2,
        "base_hum": 58.0,
        "base_press": 1012.0
    },
    {
        "device_id": "SENSOR-003",
        "name": "Steam Boiler Reactor",
        "location": "Boiler Room",
        "status": "ONLINE",
        "base_temp": 39.5,
        "base_hum": 42.0,
        "base_press": 1010.5
    },
    {
        "device_id": "SENSOR-004",
        "name": "Packaging Conveyor B",
        "location": "Assembly Line",
        "status": "ONLINE",
        "base_temp": 26.8,
        "base_hum": 50.5,
        "base_press": 1014.0
    },
    {
        "device_id": "SENSOR-005",
        "name": "Raw Chemical Silo",
        "location": "Storage Area",
        "status": "ONLINE",
        "base_temp": 24.1,
        "base_hum": 48.0,
        "base_press": 1011.8
    }
]

def seed_database_if_empty():
    """Initializes tables and seeds demo data if the database is clean."""
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # 1. Seed Users if not present
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            logger.info("Seeding default Administrator user (admin / admin123)...")
            db.add(User(
                username="admin",
                email="admin@industrial-iot.io",
                hashed_password=get_password_hash("admin123"),
                role="ADMIN",
                created_at=datetime.now(timezone.utc)
            ))

        viewer_user = db.query(User).filter(User.username == "viewer").first()
        if not viewer_user:
            logger.info("Seeding default Viewer user (viewer / viewer123)...")
            db.add(User(
                username="viewer",
                email="viewer@industrial-iot.io",
                hashed_password=get_password_hash("viewer123"),
                role="VIEWER",
                created_at=datetime.now(timezone.utc)
            ))
        db.commit()

        # 2. Seed Sensors
        existing_sensor_count = db.query(Sensor).count()
        if existing_sensor_count == 0:
            logger.info("Seeding 5 industrial IoT sensors...")
            created_sensors = []
            for item in DEMO_SENSORS:
                s = Sensor(
                    device_id=item["device_id"],
                    name=item["name"],
                    location=item["location"],
                    status=item["status"],
                    is_enabled=True,
                    created_at=datetime.now(timezone.utc) - timedelta(days=7),
                    last_seen=datetime.now(timezone.utc)
                )
                db.add(s)
                db.flush()
                created_sensors.append((s, item))

            db.commit()

            # 3. Seed historical readings over the past 3 hours
            logger.info("Seeding realistic historical readings and initial anomalies...")
            now = datetime.now(timezone.utc)
            total_readings = 0

            # 30 historical timestamps (every 6 minutes over last 3 hours)
            timestamps = [now - timedelta(minutes=6 * i) for i in range(29, -1, -1)]

            for sensor_entity, profile in created_sensors:
                for idx, ts in enumerate(timestamps):
                    # Normal jitter
                    t = profile["base_temp"] + random.uniform(-1.8, 1.8)
                    h = profile["base_hum"] + random.uniform(-3.5, 3.5)
                    p = profile["base_press"] + random.uniform(-2.0, 2.0)

                    is_anomaly = False
                    anomaly_score = round(random.uniform(0.08, 0.28), 4)
                    severity = "NORMAL"

                    # Inject historical anomaly on SENSOR-003 (Boiler Room overheat ~45 mins ago)
                    if profile["device_id"] == "SENSOR-003" and idx == 22:
                        t = 94.2
                        h = 18.5
                        p = 1008.0
                        is_anomaly = True
                        anomaly_score = 0.9650
                        severity = "CRITICAL"

                    # Inject historical anomaly on SENSOR-005 (Storage Area depressurization ~15 mins ago)
                    elif profile["device_id"] == "SENSOR-005" and idx == 27:
                        t = 24.8
                        h = 49.0
                        p = 865.4
                        is_anomaly = True
                        anomaly_score = 0.8920
                        severity = "HIGH"

                    reading = SensorReading(
                        sensor_id=sensor_entity.id,
                        temperature=round(t, 2),
                        humidity=round(h, 2),
                        pressure=round(p, 2),
                        timestamp=ts,
                        is_anomaly=is_anomaly,
                        anomaly_score=anomaly_score
                    )
                    db.add(reading)
                    db.flush()
                    total_readings += 1

                    if is_anomaly:
                        anomaly_record = Anomaly(
                            sensor_id=sensor_entity.id,
                            reading_id=reading.id,
                            temperature=round(t, 2),
                            humidity=round(h, 2),
                            pressure=round(p, 2),
                            anomaly_score=anomaly_score,
                            severity=severity,
                            reason=f"Extreme divergence on {sensor_entity.name} - Isolation Forest Flagged Outlier",
                            timestamp=ts,
                            acknowledged=False
                        )
                        db.add(anomaly_record)

                        alert_type = "TEMPERATURE_SPIKE" if t > 60 else "PRESSURE_DROP"
                        alert_record = Alert(
                            sensor_id=sensor_entity.id,
                            type=alert_type,
                            severity=severity,
                            message=f"Critical Anomaly Detected on {sensor_entity.device_id} ({sensor_entity.name}): T={t:.1f}°C, P={p:.1f}hPa. Isolation Forest Score: {anomaly_score:.2f}",
                            status="ACTIVE",
                            created_at=ts
                        )
                        db.add(alert_record)

            db.add(SystemLog(
                level="INFO",
                source="SYSTEM",
                message=f"System initialized with 5 sensors and {total_readings} historical readings.",
                timestamp=now
            ))
            db.commit()
            logger.info(f"Database seeded successfully with {total_readings} historical sensor data points.")

    except Exception as e:
        logger.error(f"Error during database initialization/seeding: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()
