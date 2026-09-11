"""
SQLAlchemy ORM Data Models
Tables: users, sensors, sensor_readings, anomalies, alerts, system_logs
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Index
)
from sqlalchemy.orm import relationship
from .database import Base

def utcnow():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="VIEWER", nullable=False)  # ADMIN or VIEWER
    created_at = Column(DateTime, default=utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Sensor(Base):
    __tablename__ = "sensors"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    location = Column(String(100), nullable=False)
    status = Column(String(20), default="ONLINE", nullable=False)  # ONLINE, OFFLINE, MAINTENANCE
    is_enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    last_seen = Column(DateTime, default=utcnow, nullable=True)

    readings = relationship("SensorReading", back_populates="sensor", cascade="all, delete-orphan")
    anomalies = relationship("Anomaly", back_populates="sensor", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="sensor", cascade="all, delete-orphan")

    def to_dict(self, latest_reading=None):
        data = {
            "id": self.id,
            "device_id": self.device_id,
            "name": self.name,
            "location": self.location,
            "status": self.status,
            "is_enabled": self.is_enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
        }
        if latest_reading:
            data.update({
                "temperature": latest_reading.temperature,
                "humidity": latest_reading.humidity,
                "pressure": latest_reading.pressure,
                "is_anomaly": latest_reading.is_anomaly,
                "anomaly_score": latest_reading.anomaly_score,
                "last_reading_time": latest_reading.timestamp.isoformat() if latest_reading.timestamp else None
            })
        return data


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sensor_id = Column(Integer, ForeignKey("sensors.id", ondelete="CASCADE"), nullable=False, index=True)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    pressure = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=utcnow, nullable=False, index=True)
    is_anomaly = Column(Boolean, default=False, nullable=False, index=True)
    anomaly_score = Column(Float, default=0.0, nullable=False)

    sensor = relationship("Sensor", back_populates="readings")
    anomalies = relationship("Anomaly", back_populates="reading", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "sensor_id": self.sensor_id,
            "device_id": self.sensor.device_id if self.sensor else None,
            "sensor_name": self.sensor.name if self.sensor else None,
            "location": self.sensor.location if self.sensor else None,
            "temperature": round(self.temperature, 2),
            "humidity": round(self.humidity, 2),
            "pressure": round(self.pressure, 2),
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "is_anomaly": self.is_anomaly,
            "anomaly_score": round(self.anomaly_score, 4)
        }

Index("ix_readings_sensor_timestamp", SensorReading.sensor_id, SensorReading.timestamp)
Index("ix_readings_sensor_anomaly", SensorReading.sensor_id, SensorReading.is_anomaly)
Index("ix_readings_timestamp_anomaly", SensorReading.timestamp, SensorReading.is_anomaly)


class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sensor_id = Column(Integer, ForeignKey("sensors.id", ondelete="CASCADE"), nullable=False, index=True)
    reading_id = Column(Integer, ForeignKey("sensor_readings.id", ondelete="CASCADE"), nullable=True, index=True)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    pressure = Column(Float, nullable=False)
    anomaly_score = Column(Float, nullable=False)
    severity = Column(String(20), default="MEDIUM", nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    reason = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=utcnow, nullable=False, index=True)
    acknowledged = Column(Boolean, default=False, nullable=False)

    sensor = relationship("Sensor", back_populates="anomalies")
    reading = relationship("SensorReading", back_populates="anomalies")

    def to_dict(self):
        return {
            "id": self.id,
            "sensor_id": self.sensor_id,
            "device_id": self.sensor.device_id if self.sensor else None,
            "sensor_name": self.sensor.name if self.sensor else None,
            "location": self.sensor.location if self.sensor else None,
            "reading_id": self.reading_id,
            "temperature": round(self.temperature, 2),
            "humidity": round(self.humidity, 2),
            "pressure": round(self.pressure, 2),
            "anomaly_score": round(self.anomaly_score, 4),
            "severity": self.severity,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "acknowledged": self.acknowledged
        }

Index("ix_anomalies_sensor_timestamp", Anomaly.sensor_id, Anomaly.timestamp)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sensor_id = Column(Integer, ForeignKey("sensors.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(50), nullable=False)  # e.g., "TEMPERATURE_SPIKE", "PRESSURE_DROP", "HUMIDITY_ANOMALY"
    severity = Column(String(20), default="MEDIUM", nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    message = Column(Text, nullable=False)
    status = Column(String(20), default="ACTIVE", nullable=False)  # ACTIVE, RESOLVED
    created_at = Column(DateTime, default=utcnow, nullable=False, index=True)
    resolved_at = Column(DateTime, nullable=True)

    sensor = relationship("Sensor", back_populates="alerts")

    def to_dict(self):
        return {
            "id": self.id,
            "sensor_id": self.sensor_id,
            "device_id": self.sensor.device_id if self.sensor else None,
            "sensor_name": self.sensor.name if self.sensor else None,
            "location": self.sensor.location if self.sensor else None,
            "type": self.type,
            "severity": self.severity,
            "message": self.message,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }

Index("ix_alerts_status_created_at", Alert.status, Alert.created_at)
Index("ix_alerts_sensor_status", Alert.sensor_id, Alert.status)


class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    level = Column(String(20), default="INFO", nullable=False)  # INFO, WARNING, ERROR, CRITICAL
    source = Column(String(50), default="SYSTEM", nullable=False)  # MQTT, ML, API, SIMULATOR, AUTH
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=utcnow, nullable=False, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "level": self.level,
            "source": self.source,
            "message": self.message,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }
