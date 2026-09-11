"""
Predictive Maintenance & Remaining Useful Life (RUL) Service
Computes telemetry rate-of-change gradients (dT/dt, dP/dt) over recent historical windows
and estimates time-to-breach before an operating threshold is exceeded.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from backend.database.database import SessionLocal
from backend.database.models import Sensor, SensorReading

# Critical engineering failure boundaries
CRITICAL_THRESHOLDS = {
    "temp_max": 60.0,      # Industrial high-temp hazard (°C)
    "temp_extreme": 85.0,  # Catastrophic thermal run-away
    "press_min": 950.0,    # Depressurization threshold (hPa)
    "hum_min": 20.0,       # Extreme desiccation (%)
    "hum_max": 85.0        # Extreme condensation (%)
}

class PredictiveAnalyticsService:
    def analyze_sensor_trajectory(self, sensor_id: int, window_minutes: int = 15) -> Dict[str, Any]:
        """
        Analyzes the trajectory of a sensor over the specified time window.
        Returns drift velocity, trend direction, risk level, and estimated minutes to threshold breach.
        """
        db: Session = SessionLocal()
        try:
            sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()
            if not sensor:
                return {}

            now = datetime.now(timezone.utc)
            cutoff = now - timedelta(minutes=window_minutes)

            # Retrieve readings chronologically
            readings = (
                db.query(SensorReading)
                .filter(SensorReading.sensor_id == sensor_id, SensorReading.timestamp >= cutoff)
                .order_by(asc(SensorReading.timestamp))
                .all()
            )

            if len(readings) < 2:
                # Fallback: get the last 10 readings regardless of time
                readings = (
                    db.query(SensorReading)
                    .filter(SensorReading.sensor_id == sensor_id)
                    .order_by(desc(SensorReading.timestamp))
                    .limit(10)
                    .all()
                )
                readings.reverse()

            if len(readings) < 2:
                return {
                    "sensor_id": sensor.id,
                    "device_id": sensor.device_id,
                    "name": sensor.name,
                    "location": sensor.location,
                    "status": "INSUFFICIENT_DATA",
                    "risk_level": "LOW",
                    "temp_velocity": 0.0,
                    "press_velocity": 0.0,
                    "minutes_to_breach": None,
                    "health_index": 98.0,
                    "trajectory_summary": "Insufficient temporal telemetry to calculate velocity vector."
                }

            # Calculate time delta in minutes
            t_start = readings[0].timestamp
            t_end = readings[-1].timestamp
            
            # Ensure timezone awareness
            if t_start.tzinfo is None:
                t_start = t_start.replace(tzinfo=timezone.utc)
            if t_end.tzinfo is None:
                t_end = t_end.replace(tzinfo=timezone.utc)

            delta_seconds = max((t_end - t_start).total_seconds(), 1.0)
            delta_minutes = delta_seconds / 60.0

            # Calculate gradient (velocity)
            start_temp = readings[0].temperature
            end_temp = readings[-1].temperature
            temp_velocity = (end_temp - start_temp) / delta_minutes  # °C per minute

            start_press = readings[0].pressure
            end_press = readings[-1].pressure
            press_velocity = (end_press - start_press) / delta_minutes  # hPa per minute

            # Estimate Minutes to Breach
            minutes_to_temp_breach = None
            if temp_velocity > 0.15 and end_temp < CRITICAL_THRESHOLDS["temp_max"]:
                remaining_temp = CRITICAL_THRESHOLDS["temp_max"] - end_temp
                minutes_to_temp_breach = round(remaining_temp / temp_velocity, 1)

            minutes_to_press_breach = None
            if press_velocity < -0.2 and end_press > CRITICAL_THRESHOLDS["press_min"]:
                remaining_press = end_press - CRITICAL_THRESHOLDS["press_min"]
                minutes_to_press_breach = round(remaining_press / abs(press_velocity), 1)

            # Determine primary forecast
            forecast_breach = None
            risk_level = "LOW"
            hazard_factor = 0.0

            if end_temp >= CRITICAL_THRESHOLDS["temp_max"] or end_press <= CRITICAL_THRESHOLDS["press_min"]:
                risk_level = "CRITICAL"
                hazard_factor = 45.0
                trajectory_summary = f"Threshold breached! Node operating in active emergency zone (T={end_temp:.1f}°C, P={end_press:.1f}hPa)."
            elif minutes_to_temp_breach is not None and minutes_to_temp_breach < 20.0:
                risk_level = "HIGH"
                forecast_breach = minutes_to_temp_breach
                hazard_factor = 30.0
                trajectory_summary = f"High Thermal Acceleration: +{temp_velocity:.2f}°C/min. Estimated breach of {CRITICAL_THRESHOLDS['temp_max']}°C in ~{minutes_to_temp_breach} mins."
            elif minutes_to_press_breach is not None and minutes_to_press_breach < 25.0:
                risk_level = "HIGH"
                forecast_breach = minutes_to_press_breach
                hazard_factor = 25.0
                trajectory_summary = f"Rapid Depressurization: {press_velocity:.2f} hPa/min. Safe floor breach in ~{minutes_to_press_breach} mins."
            elif abs(temp_velocity) > 0.08 or abs(press_velocity) > 0.1:
                risk_level = "MODERATE"
                hazard_factor = 12.0
                trajectory_summary = f"Moderate environmental drift detected (dT/dt={temp_velocity:+.2f}°C/min, dP/dt={press_velocity:+.2f}hPa/min)."
            else:
                risk_level = "NOMINAL"
                hazard_factor = 2.0
                trajectory_summary = "Operating parameters demonstrate stationary equilibrium. Zero drift hazards detected."

            # Calculate Health Degradation Index (100% = Factory Fresh, 0% = Total Failure)
            anomaly_penalty = 15.0 if readings[-1].is_anomaly else 0.0
            health_index = max(10.0, min(100.0, 100.0 - (hazard_factor + anomaly_penalty)))

            return {
                "sensor_id": sensor.id,
                "device_id": sensor.device_id,
                "name": sensor.name,
                "location": sensor.location,
                "current_temp": round(end_temp, 2),
                "current_press": round(end_press, 2),
                "temp_velocity": round(temp_velocity, 3),
                "temp_velocity_c_per_min": round(temp_velocity, 3),
                "press_velocity": round(press_velocity, 3),
                "pressure_velocity_hpa_per_min": round(press_velocity, 3),
                "risk_level": risk_level,
                "minutes_to_breach": forecast_breach,
                "estimated_minutes_to_breach": forecast_breach,
                "health_index": round(health_index, 1),
                "trajectory_summary": trajectory_summary,
                "recommendation": trajectory_summary,
                "sample_count": len(readings),
                "evaluation_time": now.isoformat()
            }
        finally:
            db.close()

    def get_fleet_analytics(self) -> Dict[str, Any]:
        """Runs predictive trajectory analysis across all deployed edge sensors."""
        db: Session = SessionLocal()
        try:
            sensors = db.query(Sensor).all()
            sensor_ids = [s.id for s in sensors]
        finally:
            db.close()

        analytics_list = [self.analyze_sensor_trajectory(sid) for sid in sensor_ids]
        
        # Sort by highest risk
        risk_rank = {"CRITICAL": 0, "HIGH": 1, "MODERATE": 2, "NOMINAL": 3, "LOW": 4, "INSUFFICIENT_DATA": 5}
        analytics_list.sort(key=lambda x: risk_rank.get(x.get("risk_level", "LOW"), 99))

        highest_risk_node = analytics_list[0] if analytics_list else None
        fleet_health_avg = (
            sum(item.get("health_index", 100.0) for item in analytics_list) / len(analytics_list)
            if analytics_list else 100.0
        )
        fleet_risk = highest_risk_node.get("risk_level", "NOMINAL") if highest_risk_node else "NOMINAL"

        return {
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "fleet_health_avg": round(fleet_health_avg, 1),
            "fleet_risk_status": fleet_risk,
            "highest_risk_node": highest_risk_node,
            "sensor_forecasts": analytics_list
        }

predictive_service = PredictiveAnalyticsService()

# Backward-compatible alias for CI/CD pipeline and legacy imports
PredictiveEngine = PredictiveAnalyticsService
