"""
Stream Processing Pipeline
Processes real-time IoT sensor telemetry streams:
MQTT Ingest -> JSON Validation -> Missing Value Check -> Cleaning ->
Feature Assembly -> ML Isolation Forest Inference -> Database Commit -> WebSocket Broadcast
"""

from datetime import datetime, timezone
import json
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.database.database import SessionLocal
from backend.database.models import Sensor, SensorReading, Anomaly, Alert, SystemLog
from backend.ml.ml_model import ml_detector
from backend.services.websocket_manager import ws_manager

logger = logging.getLogger("iot.stream_processor")

class StreamProcessor:
    def __init__(self):
        self.total_processed = 0
        self.total_anomalies = 0
        self.main_loop = None

    def set_event_loop(self, loop):
        self.main_loop = loop

    def process_raw_payload(self, payload_str: str) -> Optional[Dict[str, Any]]:
        """
        Step 1 & 2: JSON Parsing and Missing-value Check
        """
        try:
            payload = json.loads(payload_str)
        except Exception as e:
            logger.warning(f"[Pipeline Stage 1] Invalid JSON rejected: {payload_str[:100]} | Error: {e}")
            return None

        return self.process_reading(payload)

    def process_reading(self, payload: dict) -> Optional[Dict[str, Any]]:
        """
        Executes the full stream processing pipeline.
        """
        # Step 2: Missing Value / Type Validation
        required_fields = ["device_id", "temperature", "humidity", "pressure"]
        for field in required_fields:
            if field not in payload or payload[field] is None:
                logger.warning(f"[Pipeline Stage 2] Missing field '{field}' in payload: {payload}")
                return None

        # Step 3: Data Cleaning & Type Casting
        try:
            device_id = str(payload["device_id"]).strip()
            temp = float(payload["temperature"])
            hum = float(payload["humidity"])
            press = float(payload["pressure"])
            
            raw_ts = payload.get("timestamp")
            if raw_ts:
                try:
                    ts = datetime.fromisoformat(str(raw_ts).replace("Z", "+00:00"))
                except Exception:
                    ts = datetime.now(timezone.utc)
            else:
                ts = datetime.now(timezone.utc)
        except (ValueError, TypeError) as e:
            logger.warning(f"[Pipeline Stage 3] Data cleaning failed for payload: {payload} | Error: {e}")
            return None

        # Step 4 & 5: Feature Preparation & ML Anomaly Detection
        # Features: [temperature, humidity, pressure]
        ml_result = ml_detector.predict(temperature=temp, humidity=hum, pressure=press)
        is_anomaly = ml_result["is_anomaly"]
        anomaly_score = ml_result["anomaly_score"]
        severity = ml_result["severity"]
        reason = ml_result["reason"]

        # Step 6: Database Storage
        db: Session = SessionLocal()
        reading_dict = None
        alert_dict = None
        anomaly_dict = None

        try:
            # Match or register Sensor
            sensor = db.query(Sensor).filter(Sensor.device_id == device_id).first()
            if not sensor:
                sensor = Sensor(
                    device_id=device_id,
                    name=f"Industrial Node {device_id}",
                    location="Main Facility",
                    status="ONLINE",
                    is_enabled=True,
                    created_at=datetime.now(timezone.utc),
                    last_seen=datetime.now(timezone.utc)
                )
                db.add(sensor)
                db.flush()
            else:
                sensor.status = "ONLINE"
                sensor.last_seen = datetime.now(timezone.utc)

            # Store Sensor Reading
            reading = SensorReading(
                sensor_id=sensor.id,
                temperature=round(temp, 2),
                humidity=round(hum, 2),
                pressure=round(press, 2),
                timestamp=ts,
                is_anomaly=is_anomaly,
                anomaly_score=anomaly_score
            )
            db.add(reading)
            db.flush()
            reading_dict = reading.to_dict()

            # Handle Anomaly & Alert Generation
            if is_anomaly:
                self.total_anomalies += 1
                anomaly_record = Anomaly(
                    sensor_id=sensor.id,
                    reading_id=reading.id,
                    temperature=round(temp, 2),
                    humidity=round(hum, 2),
                    pressure=round(press, 2),
                    anomaly_score=anomaly_score,
                    severity=severity,
                    reason=reason,
                    timestamp=ts,
                    acknowledged=False
                )
                db.add(anomaly_record)
                db.flush()
                anomaly_dict = anomaly_record.to_dict()

                # Determine Alert classification
                alert_type = "ENVIRONMENTAL_ANOMALY"
                if temp > 50.0:
                    alert_type = "CRITICAL_TEMPERATURE_SPIKE"
                elif temp < 10.0:
                    alert_type = "LOW_TEMPERATURE_FREEZE"
                elif press < 950.0:
                    alert_type = "PRESSURE_DEPRESSURIZATION"
                elif press > 1050.0:
                    alert_type = "PRESSURE_SURGE"
                elif hum < 20.0 or hum > 85.0:
                    alert_type = "HUMIDITY_OUT_OF_BOUNDS"

                alert_msg = f"{alert_type} on {device_id} ({sensor.name}): T={temp:.1f}°C, H={hum:.1f}%, P={press:.1f}hPa. Isolation Forest Score: {anomaly_score:.2f} [{severity}]."
                alert_record = Alert(
                    sensor_id=sensor.id,
                    type=alert_type,
                    severity=severity,
                    message=alert_msg,
                    status="ACTIVE",
                    created_at=ts
                )
                db.add(alert_record)
                db.flush()
                alert_dict = alert_record.to_dict()

                db.add(SystemLog(
                    level="WARNING" if severity == "LOW" else "ERROR",
                    source="ML_ANOMALY",
                    message=alert_msg,
                    timestamp=ts
                ))

            db.commit()
            self.total_processed += 1

        except Exception as e:
            logger.error(f"[Pipeline Stage 6] Database commit failed: {e}", exc_info=True)
            db.rollback()
            return None
        finally:
            db.close()

        # Step 7: Real-Time WebSocket Broadcast
        if reading_dict:
            # 7a. Broadcast New Reading
            ws_manager.broadcast_sync("NEW_READING", reading_dict, loop=self.main_loop)

            # 7b. If Anomaly, broadcast Anomaly Event
            if is_anomaly and anomaly_dict:
                ws_manager.broadcast_sync("ANOMALY_DETECTED", anomaly_dict, loop=self.main_loop)

            # 7c. If Alert, broadcast Alert Event
            if alert_dict:
                ws_manager.broadcast_sync("ALERT_GENERATED", alert_dict, loop=self.main_loop)

        return reading_dict

stream_processor = StreamProcessor()
