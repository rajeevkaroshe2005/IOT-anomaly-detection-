"""
Simulator Background Runner Service
Allows starting, stopping, and configuring the IoT simulation loop directly from the FastAPI backend.
"""

import threading
import time
import random
from datetime import datetime, timezone
import logging
from backend.services.stream_processor import stream_processor
from simulator.sensor_simulator import SENSOR_PROFILES

logger = logging.getLogger("iot.simulator_service")

class SimulatorService:
    def __init__(self):
        self.is_running = False
        self.interval_seconds = 1.5
        self.anomaly_probability = 0.10
        self.total_published = 0
        self.last_published_at = None
        self._thread = None
        self._stop_event = threading.Event()

        self.drift_state = {
            s["device_id"]: {
                "temp": s["base_temp"],
                "hum": s["base_hum"],
                "press": s["base_press"]
            } for s in SENSOR_PROFILES
        }

    def start(self, interval: float = None, anomaly_prob: float = None):
        if self.is_running:
            return {"status": "already_running", "message": "Simulator is already running."}

        if interval:
            self.interval_seconds = interval
        if anomaly_prob is not None:
            self.anomaly_probability = anomaly_prob

        self._stop_event.clear()
        self.is_running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="Backend-Simulator-Worker")
        self._thread.start()
        logger.info(f"Simulator started (interval={self.interval_seconds}s, anomaly_rate={self.anomaly_probability:.2f})")
        return {"status": "started", "interval": self.interval_seconds, "anomaly_rate": self.anomaly_probability}

    def stop(self):
        if not self.is_running:
            return {"status": "not_running", "message": "Simulator is not active."}

        self.is_running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        logger.info("Simulator stopped by API command.")
        return {"status": "stopped", "total_published": self.total_published}

    def get_status(self):
        return {
            "is_running": self.is_running,
            "interval_seconds": self.interval_seconds,
            "anomaly_probability": self.anomaly_probability,
            "total_published": self.total_published,
            "last_published_at": self.last_published_at
        }

    def trigger_forced_anomaly(self, device_id: str = None):
        """Forces an instantaneous anomaly injection for immediate live demonstration testing."""
        sensor = next((s for s in SENSOR_PROFILES if s["device_id"] == device_id), random.choice(SENSOR_PROFILES))
        anomaly_reading = {
            "device_id": sensor["device_id"],
            "temperature": round(random.uniform(88.0, 102.0), 2),
            "humidity": round(random.uniform(8.0, 14.0), 2),
            "pressure": round(random.uniform(820.0, 880.0), 2),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        res = stream_processor.process_reading(anomaly_reading)
        self.total_published += 1
        self.last_published_at = datetime.now(timezone.utc).isoformat()
        return res

    def _run_loop(self):
        while not self._stop_event.is_set():
            for sensor in SENSOR_PROFILES:
                if self._stop_event.is_set():
                    break

                dev_id = sensor["device_id"]
                state = self.drift_state[dev_id]

                # Drift
                state["temp"] += random.uniform(-0.4, 0.4)
                state["hum"] += random.uniform(-0.6, 0.6)
                state["press"] += random.uniform(-0.5, 0.5)

                # Regress to baseline
                state["temp"] = 0.94 * state["temp"] + 0.06 * sensor["base_temp"]
                state["hum"] = 0.94 * state["hum"] + 0.06 * sensor["base_hum"]
                state["press"] = 0.94 * state["press"] + 0.06 * sensor["base_press"]

                t = round(float(state["temp"]), 2)
                h = round(float(state["hum"]), 2)
                p = round(float(state["press"]), 2)

                # Stochastic Anomaly Injection
                if random.random() < self.anomaly_probability:
                    anomaly_type = random.choice(["heat", "dry", "drop"])
                    if anomaly_type == "heat":
                        t = round(random.uniform(85.0, 99.0), 2)
                    elif anomaly_type == "dry":
                        h = round(random.uniform(6.0, 14.0), 2)
                    else:
                        p = round(random.uniform(810.0, 890.0), 2)

                reading_payload = {
                    "device_id": dev_id,
                    "temperature": t,
                    "humidity": h,
                    "pressure": p,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

                # Feed directly to stream processing pipeline
                try:
                    stream_processor.process_reading(reading_payload)
                    self.total_published += 1
                    self.last_published_at = reading_payload["timestamp"]
                except Exception as e:
                    logger.error(f"Simulator pipeline feeding error: {e}")

                time.sleep(self.interval_seconds / len(SENSOR_PROFILES))

simulator_service = SimulatorService()
