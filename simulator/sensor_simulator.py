"""
Industrial IoT Sensor Fleet Simulator
Simulates real-world industrial IoT edge devices publishing to MQTT.
Supports autonomous environmental drift, Gaussian noise, and stochastic anomaly injection.
Supports two operating modes:
  1. LOCAL: Edge Simulator -> Mosquitto (port 1883) -> iot/sensors/{device_id}
  2. AWS:   Edge Simulator -> AWS IoT Core (port 8883, TLS v1.2, X.509) -> industrial/sensors/{device_id}/telemetry
"""

import os
import sys
import time
import json
import random
import argparse
from datetime import datetime, timezone
import paho.mqtt.client as mqtt

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from simulator.aws_iot_client import AWSIoTClient
except ImportError:
    try:
        from aws_iot_client import AWSIoTClient
    except ImportError:
        AWSIoTClient = None

try:
    import requests
except ImportError:
    requests = None

# Baseline specifications for the 5 industrial monitoring locations
SENSOR_PROFILES = [
    {
        "device_id": "SENSOR-001",
        "name": "Main Assembly Line 1",
        "location": "Production Floor",
        "base_temp": 28.5,
        "base_hum": 52.0,
        "base_press": 1013.25
    },
    {
        "device_id": "SENSOR-002",
        "name": "Cold Storage Unit 3",
        "location": "Warehouse",
        "base_temp": 22.0,
        "base_hum": 58.0,
        "base_press": 1012.0
    },
    {
        "device_id": "SENSOR-003",
        "name": "Steam Boiler Reactor",
        "location": "Boiler Room",
        "base_temp": 38.0,
        "base_hum": 40.0,
        "base_press": 1011.0
    },
    {
        "device_id": "SENSOR-004",
        "name": "Packaging Conveyor B",
        "location": "Assembly Line",
        "base_temp": 26.5,
        "base_hum": 50.0,
        "base_press": 1014.0
    },
    {
        "device_id": "SENSOR-005",
        "name": "Raw Chemical Silo",
        "location": "Storage Area",
        "base_temp": 24.0,
        "base_hum": 48.0,
        "base_press": 1012.5
    }
]

class IoTSensorSimulator:
    def __init__(
        self,
        broker="localhost",
        port=1883,
        interval=1.5,
        anomaly_rate=0.10,
        api_fallback_url="http://localhost:8000/api/readings/ingest",
        username=None,
        password=None,
        provider=None,
        aws_endpoint=None,
        aws_port=8883,
        root_ca_path=None,
        cert_path=None,
        private_key_path=None,
        device_filter=None
    ):
        self.provider = (provider or os.getenv("MQTT_PROVIDER", "local")).lower().strip()
        if self.provider not in ("local", "aws"):
            raise ValueError(f"Invalid MQTT_PROVIDER: '{self.provider}'. Must be 'local' or 'aws'.")

        self.broker = broker
        self.port = port
        self.interval = interval
        self.anomaly_rate = anomaly_rate
        self.api_fallback_url = api_fallback_url
        self.username = username if username is not None else os.getenv("MQTT_USERNAME", "iot_simulator").strip()
        self.password = password if password is not None else os.getenv("MQTT_PASSWORD", "").strip()
        self.device_filter = device_filter

        # AWS IoT Core configuration
        self.aws_endpoint = (aws_endpoint or os.getenv("AWS_IOT_ENDPOINT", "")).strip()
        self.aws_port = int(aws_port or os.getenv("AWS_IOT_PORT", "8883"))
        self.root_ca_path = (root_ca_path or os.getenv("AWS_IOT_ROOT_CA_PATH", "")).strip()
        self.cert_path = (cert_path or os.getenv("AWS_IOT_CERT_PATH", "")).strip()
        self.private_key_path = (private_key_path or os.getenv("AWS_IOT_PRIVATE_KEY_PATH", "")).strip()

        self.mqtt_connected = False
        self.is_running = False
        self.total_published = 0
        self.total_anomalies = 0

        # Current continuous drift state
        self.drift_state = {
            s["device_id"]: {
                "temp": s["base_temp"],
                "hum": s["base_hum"],
                "press": s["base_press"]
            } for s in SENSOR_PROFILES
        }

        self.client = None
        self.aws_clients = {}

        if self.provider == "aws":
            self._init_aws_iot()
        else:
            self._init_local_mqtt()

    def _init_local_mqtt(self):
        """Initializes standard local Mosquitto MQTT publisher."""
        try:
            if hasattr(mqtt, "CallbackAPIVersion"):
                self.client = mqtt.Client(
                    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                    client_id="iot_simulator_publisher"
                )
            else:
                self.client = mqtt.Client(client_id="iot_simulator_publisher")

            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)

            self.client.on_connect = self._on_local_connect
            self.client.on_disconnect = self._on_local_disconnect
            
            # Non-blocking connection attempt
            try:
                self.client.connect(self.broker, self.port, 60)
                self.client.loop_start()
            except Exception as conn_err:
                print(f"[SIMULATOR] Note: MQTT Broker at {self.broker}:{self.port} not reachable ({conn_err}). Will use HTTP Ingest Bridge.")
        except Exception as e:
            print(f"[SIMULATOR] Local MQTT initialization error: {e}")

    def _init_aws_iot(self):
        """Initializes dedicated AWS IoT Core TLS client with strict validation."""
        if not AWSIoTClient:
            raise RuntimeError("AWSIoTClient module unavailable. Check simulator/aws_iot_client.py.")

        # Strict validation: Fail fast if configuration is missing
        missing = []
        if not self.aws_endpoint:
            missing.append("AWS_IOT_ENDPOINT is not set.")
        if not self.root_ca_path or not os.path.exists(self.root_ca_path):
            missing.append(f"Root CA not found: {self.root_ca_path}")
        if not self.cert_path or not os.path.exists(self.cert_path):
            missing.append(f"Device certificate not found: {self.cert_path}")
        if not self.private_key_path or not os.path.exists(self.private_key_path):
            missing.append(f"Private key not found: {self.private_key_path}")

        if missing:
            raise RuntimeError(
                "MQTT_PROVIDER='aws' configuration validation failed:\n  "
                + "\n  ".join(missing)
                + "\n\nVerify certs exist in certs/ and environment variables are set in .env."
            )

        print(f"[SIMULATOR] Initializing AWS IoT Core client for endpoint: {self.aws_endpoint}:{self.aws_port}")

        # Determine sensors to initialize
        sensors = [s for s in SENSOR_PROFILES if not self.device_filter or s["device_id"] == self.device_filter]

        for s in sensors:
            dev_id = s["device_id"]
            client_id = f"iot-simulator-{dev_id}"

            # Allow per-device certificate if present, or fallback to the provided cert_path
            dev_cert = self.cert_path
            dev_key = self.private_key_path
            cert_dir = os.path.dirname(self.cert_path)
            candidate_cert = os.path.join(cert_dir, f"{dev_id}.cert.pem")
            candidate_key = os.path.join(cert_dir, f"{dev_id}.private.key")
            if os.path.exists(candidate_cert) and os.path.exists(candidate_key):
                dev_cert = candidate_cert
                dev_key = candidate_key

            aws_client = AWSIoTClient(
                endpoint=self.aws_endpoint,
                port=self.aws_port,
                root_ca_path=self.root_ca_path,
                cert_path=dev_cert,
                private_key_path=dev_key,
                client_id=client_id
            )
            try:
                aws_client.connect(timeout=60)
                self.aws_clients[dev_id] = aws_client
            except Exception as e:
                print(f"[SIMULATOR] Could not connect AWS IoT client for {dev_id}: {e}")

        self.mqtt_connected = any(c.is_connected for c in self.aws_clients.values())

    def _on_local_connect(self, client, userdata, flags, rc, *args):
        rc_val = getattr(rc, "value", rc)
        if rc_val == 0:
            self.mqtt_connected = True
            print(f"[SIMULATOR] Connected to local MQTT broker at {self.broker}:{self.port}")
        else:
            self.mqtt_connected = False
            print(f"[SIMULATOR] MQTT Connection returned code: {rc_val}")

    def _on_local_disconnect(self, client, userdata, rc, *args):
        self.mqtt_connected = False
        print("[SIMULATOR] Disconnected from local MQTT broker.")

    def generate_reading(self, sensor_profile: dict, force_anomaly: bool = False) -> dict:
        dev_id = sensor_profile["device_id"]
        state = self.drift_state[dev_id]

        # Environmental random walk (Markovian drift)
        state["temp"] += random.uniform(-0.35, 0.35)
        state["hum"] += random.uniform(-0.5, 0.5)
        state["press"] += random.uniform(-0.4, 0.4)

        # Pull gently towards baseline
        state["temp"] = 0.95 * state["temp"] + 0.05 * sensor_profile["base_temp"]
        state["hum"] = 0.95 * state["hum"] + 0.05 * sensor_profile["base_hum"]
        state["press"] = 0.95 * state["press"] + 0.05 * sensor_profile["base_press"]

        # Keep normal bounds (Temp: 20-40, Hum: 30-80, Press: 990-1030)
        t = round(float(state["temp"]), 2)
        h = round(float(state["hum"]), 2)
        p = round(float(state["press"]), 2)

        # Check for anomaly injection
        inject_anomaly = force_anomaly or (random.random() < self.anomaly_rate)

        if inject_anomaly:
            self.total_anomalies += 1
            anomaly_flavor = random.choice(["extreme_heat", "extreme_freeze", "desiccation", "depressurization", "pressure_surge"])
            if anomaly_flavor == "extreme_heat":
                t = round(random.uniform(82.0, 98.5), 2)
            elif anomaly_flavor == "extreme_freeze":
                t = round(random.uniform(-5.0, 8.0), 2)
            elif anomaly_flavor == "desiccation":
                h = round(random.uniform(5.0, 14.5), 2)
            elif anomaly_flavor == "depressurization":
                p = round(random.uniform(820.0, 895.0), 2)
            elif anomaly_flavor == "pressure_surge":
                p = round(random.uniform(1065.0, 1110.0), 2)

        timestamp_iso = datetime.now(timezone.utc).isoformat()

        reading = {
            "device_id": dev_id,
            "temperature": t,
            "humidity": h,
            "pressure": p,
            "timestamp": timestamp_iso
        }
        return reading

    def publish_single(self, reading: dict) -> bool:
        payload_str = json.dumps(reading)
        dev_id = reading["device_id"]
        published = False

        if self.provider == "aws":
            # AWS Cloud Mode: Publish to industrial/sensors/{device_id}/telemetry
            topic = f"industrial/sensors/{dev_id}/telemetry"
            client = self.aws_clients.get(dev_id)
            if client and client.is_connected:
                published = client.publish(topic, payload_str, qos=1)
            elif client:
                # Attempt publish if client exists
                published = client.publish(topic, payload_str, qos=1)
        else:
            # Local Development Mode: Publish to iot/sensors/{device_id}
            topic = f"iot/sensors/{dev_id}"
            if self.mqtt_connected and self.client:
                try:
                    res = self.client.publish(topic, payload_str, qos=1)
                    published = (res.rc == 0)
                except Exception:
                    published = False

            # Local fallback to direct HTTP Ingestion API if Mosquitto is offline
            if not published and requests:
                try:
                    resp = requests.post(self.api_fallback_url, json=reading, timeout=1.5)
                    published = (resp.status_code == 200)
                except Exception:
                    published = False

        if published:
            self.total_published += 1
        return published

    def run(self, max_readings=None):
        self.is_running = True
        sensors = [s for s in SENSOR_PROFILES if not self.device_filter or s["device_id"] == self.device_filter]

        mode_label = "AWS CLOUD MODE (AWS IoT Core)" if self.provider == "aws" else "LOCAL DEV MODE (Mosquitto)"
        print(f"[SIMULATOR] Starting Sensor Fleet Simulator [{mode_label}]")
        print(f"[SIMULATOR] Interval: {self.interval}s | Anomaly Rate: {self.anomaly_rate*100:.1f}%")
        print(f"[SIMULATOR] Emulating {len(sensors)} device(s): {[s['device_id'] for s in sensors]}")
        print("-" * 75)

        count = 0
        try:
            while self.is_running:
                for sensor in sensors:
                    reading = self.generate_reading(sensor)
                    success = self.publish_single(reading)
                    
                    status_flag = "[ANOMALY]" if (reading["temperature"] > 50 or reading["humidity"] < 20 or reading["pressure"] < 950) else "[NORMAL] "
                    transport = f"AWS-MQTT" if self.provider == "aws" else ("MQTT" if self.mqtt_connected else "HTTP")
                    print(f"[{reading['timestamp'][11:19]}] {status_flag} {reading['device_id']} | T={reading['temperature']:>5.1f}°C | H={reading['humidity']:>5.1f}% | P={reading['pressure']:>6.1f}hPa | Via: {transport} ({'OK' if success else 'WAIT'})")
                    time.sleep(self.interval / len(sensors))

                count += 1
                if max_readings and count >= max_readings:
                    break

        except KeyboardInterrupt:
            print("\n[SIMULATOR] Simulation stopped by user.")
        finally:
            self.stop()

    def stop(self):
        self.is_running = False
        if self.provider == "aws":
            for client in self.aws_clients.values():
                try:
                    client.disconnect()
                except Exception:
                    pass
            self.aws_clients.clear()
        else:
            if self.client:
                try:
                    self.client.loop_stop()
                    self.client.disconnect()
                except Exception:
                    pass
        print(f"[SIMULATOR] Total Published: {self.total_published} | Anomalies Injected: {self.total_anomalies}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Industrial IoT Sensor Fleet Simulator")
    parser.add_argument("--provider", choices=["local", "aws"], default=os.getenv("MQTT_PROVIDER", "local"), help="MQTT Provider: 'local' (Mosquitto) or 'aws' (AWS IoT Core)")
    parser.add_argument("--broker", default=os.getenv("MQTT_BROKER", "localhost"), help="Local MQTT Broker hostname")
    parser.add_argument("--port", type=int, default=int(os.getenv("MQTT_PORT", 1883)), help="Local MQTT Broker port")
    parser.add_argument("--interval", type=float, default=1.5, help="Publish interval in seconds")
    parser.add_argument("--anomaly-rate", type=float, default=0.10, help="Probability of anomaly (0.0 to 1.0)")
    parser.add_argument("--count", type=int, default=None, help="Maximum number of cycles to run")
    parser.add_argument("--username", default=None, help="Local MQTT username")
    parser.add_argument("--password", default=None, help="Local MQTT password")
    parser.add_argument("--aws-endpoint", default=os.getenv("AWS_IOT_ENDPOINT", None), help="AWS IoT Core ATS endpoint URL")
    parser.add_argument("--aws-port", type=int, default=int(os.getenv("AWS_IOT_PORT", 8883)), help="AWS IoT Core port (default: 8883)")
    parser.add_argument("--root-ca", default=os.getenv("AWS_IOT_ROOT_CA_PATH", None), help="Path to AmazonRootCA1.pem")
    parser.add_argument("--cert", default=os.getenv("AWS_IOT_CERT_PATH", None), help="Path to device certificate (.cert.pem)")
    parser.add_argument("--key", default=os.getenv("AWS_IOT_PRIVATE_KEY_PATH", None), help="Path to device private key (.private.key)")
    parser.add_argument("--device", default=None, help="Target specific device ID (e.g. SENSOR-001)")
    args = parser.parse_args()

    sim = IoTSensorSimulator(
        provider=args.provider,
        broker=args.broker,
        port=args.port,
        interval=args.interval,
        anomaly_rate=args.anomaly_rate,
        username=args.username,
        password=args.password,
        aws_endpoint=args.aws_endpoint,
        aws_port=args.aws_port,
        root_ca_path=args.root_ca,
        cert_path=args.cert,
        private_key_path=args.key,
        device_filter=args.device
    )
    sim.run(max_readings=args.count)
