"""
MQTT Client Ingestion Service
Supports dual operating modes:
  1. LOCAL: Subscribes to 'iot/sensors/+' on local Mosquitto broker (port 1883).
  2. AWS:   Subscribes to 'industrial/sensors/+/telemetry' on AWS IoT Core (port 8883, TLS v1.2, X.509 mTLS).
Validates credentials and connection parameters based on MQTT_PROVIDER.
Forwards incoming sensor payloads to the Stream Processing pipeline.
"""

import os
import ssl
import logging
import threading
import time
import json
import paho.mqtt.client as mqtt
from backend.services.stream_processor import stream_processor

logger = logging.getLogger("iot.mqtt")

def get_sensor_publish_topic(sensor_id: str, provider: str = "local") -> str:
    """
    Generates a concrete MQTT publish topic for a specific sensor ID.
    Enforces that MQTT wildcard characters ('+' or '#') are strictly forbidden in publish topics.
    """
    clean_id = (sensor_id or "").strip()
    if not clean_id:
        raise ValueError("Sensor ID cannot be empty.")
    if "+" in clean_id or "#" in clean_id:
        raise ValueError(f"Sensor ID '{clean_id}' cannot contain MQTT wildcards ('+' or '#').")

    if provider == "aws":
        template = os.getenv("AWS_IOT_PUBLISH_TOPIC_TEMPLATE", "industrial/sensors/{sensor_id}/telemetry")
        topic = template.format(sensor_id=clean_id)
    else:
        prefix = os.getenv("MQTT_TOPIC_PREFIX", "iot/sensors/").rstrip("/")
        topic = f"{prefix}/{clean_id}"

    if "+" in topic or "#" in topic:
        raise ValueError(f"MQTT publish topic '{topic}' cannot contain wildcard characters ('+' or '#').")
    return topic

class MQTTService:
    def __init__(self):
        self.provider = os.getenv("MQTT_PROVIDER", "local").lower().strip()
        if self.provider not in ("local", "aws"):
            logger.warning(f"Unknown MQTT_PROVIDER '{self.provider}', defaulting to 'local'.")
            self.provider = "local"

        if self.provider == "aws":
            self.broker = os.getenv("AWS_IOT_ENDPOINT", "").strip()
            self.port = int(os.getenv("AWS_IOT_PORT", "8883"))
            self.keepalive = int(os.getenv("AWS_IOT_KEEPALIVE", "60"))
            # Subscription topic filter (wildcards allowed only for subscribing)
            self.subscribe_topic = (
                os.getenv("AWS_IOT_SUBSCRIBE_TOPIC", "")
                or os.getenv("AWS_IOT_TOPIC", "")
                or "industrial/sensors/+/telemetry"
            ).strip()
            self.topic = self.subscribe_topic
            self.publish_topic_template = os.getenv(
                "AWS_IOT_PUBLISH_TOPIC_TEMPLATE",
                "industrial/sensors/{sensor_id}/telemetry"
            ).strip()
            self.client_id = os.getenv("AWS_IOT_BACKEND_CLIENT_ID", "iot-fastapi-backend-consumer").strip()
            self.root_ca_path = os.getenv("AWS_IOT_ROOT_CA_PATH", "").strip()
            self.cert_path = (os.getenv("AWS_IOT_BACKEND_CERT_PATH", "") or os.getenv("AWS_IOT_CERT_PATH", "")).strip()
            self.private_key_path = (os.getenv("AWS_IOT_BACKEND_PRIVATE_KEY_PATH", "") or os.getenv("AWS_IOT_PRIVATE_KEY_PATH", "")).strip()
            self.username = None
            self.password = None
            self.use_tls = True
        else:
            self.broker = os.getenv("MQTT_BROKER", "localhost").strip()
            self.port = int(os.getenv("MQTT_PORT", "1883"))
            self.keepalive = int(os.getenv("MQTT_KEEPALIVE", "60"))
            self.subscribe_topic = (os.getenv("MQTT_TOPIC_PREFIX", "iot/sensors/").rstrip("/") + "/+").strip()
            self.topic = self.subscribe_topic
            self.publish_topic_template = os.getenv("MQTT_TOPIC_PREFIX", "iot/sensors/").rstrip("/") + "/{sensor_id}"
            self.client_id = os.getenv("MQTT_CLIENT_ID", "iot_fastapi_backend_consumer").strip()
            self.username = os.getenv("MQTT_USERNAME", "").strip()
            self.password = os.getenv("MQTT_PASSWORD", "").strip()
            self.use_tls = os.getenv("MQTT_USE_TLS", "False").lower() in ("true", "1", "yes")
            self.root_ca_path = None
            self.cert_path = None
            self.private_key_path = None

        self.client = None
        self.is_connected = False
        self.last_message_time = None
        self.total_messages_received = 0
        self._thread = None
        self._running = False

    def validate_config(self):
        """
        Validates connection configuration.
        Fails fast if provider is 'aws' and required credentials or endpoints are missing.
        """
        if self.provider == "aws":
            missing = []
            if not self.broker:
                missing.append("AWS_IOT_ENDPOINT is not set.")
            if not self.root_ca_path or not os.path.exists(self.root_ca_path):
                missing.append(f"Root CA file not found: '{self.root_ca_path}'")
            if not self.cert_path or not os.path.exists(self.cert_path):
                missing.append(f"Backend certificate file not found: '{self.cert_path}'")
            if not self.private_key_path or not os.path.exists(self.private_key_path):
                missing.append(f"Backend private key file not found: '{self.private_key_path}'")

            if missing:
                err_msg = (
                    "AWS IoT Core backend ingestion validation failed:\n  "
                    + "\n  ".join(missing)
                    + "\n\nPlease check your .env settings and ensure certificates exist in certs/."
                )
                logger.critical(err_msg)
                raise RuntimeError(err_msg)

    def _setup_client(self):
        try:
            if self.provider == "aws":
                self.validate_config()

            # Handle Paho MQTT v2 vs v1 compatibility
            if hasattr(mqtt, "CallbackAPIVersion"):
                self.client = mqtt.Client(
                    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                    client_id=self.client_id
                )
            else:
                self.client = mqtt.Client(client_id=self.client_id)

            if self.provider == "aws":
                # Configure mutual TLS for AWS IoT Core
                self.client.tls_set(
                    ca_certs=os.path.abspath(self.root_ca_path),
                    certfile=os.path.abspath(self.cert_path),
                    keyfile=os.path.abspath(self.private_key_path),
                    cert_reqs=ssl.CERT_REQUIRED,
                    tls_version=ssl.PROTOCOL_TLSv1_2,
                    ciphers=None
                )
                self.client.tls_insecure_set(False)
            else:
                # Local Mosquitto configuration
                if self.username and self.password:
                    self.client.username_pw_set(self.username, self.password)

                if self.use_tls:
                    self.client.tls_set()

            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message

        except Exception as e:
            logger.error(f"Failed to initialize MQTT Client ({self.provider.upper()} mode): {e}", exc_info=True)
            if self.provider == "aws":
                raise

    def _on_connect(self, client, userdata, flags, rc, *args):
        rc_val = getattr(rc, "value", rc)
        if rc_val == 0:
            self.is_connected = True
            logger.info(f"Connected to MQTT Broker [{self.provider.upper()}] at {self.broker}:{self.port}. Subscribing to topic: {self.topic}")
            client.subscribe(self.topic, qos=1)
        else:
            self.is_connected = False
            logger.error(f"MQTT Connection failed ({self.provider.upper()} mode) with return code: {rc_val}")

    def _on_disconnect(self, client, userdata, rc, *args):
        self.is_connected = False
        logger.warning(f"Disconnected from MQTT Broker [{self.provider.upper()}] at {self.broker}:{self.port} (rc: {rc})")

    def _on_message(self, client, userdata, msg):
        try:
            self.total_messages_received += 1
            self.last_message_time = time.time()
            payload_str = msg.payload.decode("utf-8")
            logger.debug(f"Received MQTT payload on {msg.topic}: {payload_str[:80]}...")

            # If payload is JSON and device_id is missing, extract from topic hierarchy
            # E.g. industrial/sensors/{device_id}/telemetry or iot/sensors/{device_id}
            try:
                data = json.loads(payload_str)
                if isinstance(data, dict) and "device_id" not in data:
                    parts = msg.topic.strip("/").split("/")
                    if len(parts) >= 3 and parts[0] == "industrial" and parts[1] == "sensors":
                        data["device_id"] = parts[2]
                        payload_str = json.dumps(data)
                    elif len(parts) >= 2 and parts[0] == "iot" and parts[1] == "sensors":
                        data["device_id"] = parts[2]
                        payload_str = json.dumps(data)
            except Exception:
                pass

            stream_processor.process_raw_payload(payload_str)
        except Exception as e:
            logger.error(f"Error handling MQTT message on {msg.topic}: {e}", exc_info=True)

    def start(self):
        """Starts the MQTT loop in a resilient background daemon thread."""
        if self._running:
            return

        self._running = True
        try:
            self._setup_client()
        except Exception as e:
            if self.provider == "aws":
                logger.critical(f"AWS IoT Core startup aborted due to configuration error: {e}")
                self._running = False
                return
            logger.warning(f"MQTT setup warning: {e}")

        def run_loop():
            logger.info(f"MQTT Ingestion thread started [{self.provider.upper()} mode]. Target: {self.broker}:{self.port}")
            while self._running:
                try:
                    if not self.is_connected and self.client:
                        try:
                            self.client.connect(self.broker, self.port, self.keepalive)
                            self.client.loop_start()
                        except Exception as conn_err:
                            logger.info(f"MQTT Broker [{self.provider.upper()}] at {self.broker}:{self.port} not reachable: {conn_err}. Retrying in 10s...")
                            time.sleep(10)
                            continue
                    time.sleep(2)
                except Exception as e:
                    logger.warning(f"MQTT supervisor error: {e}")
                    time.sleep(5)

        self._thread = threading.Thread(target=run_loop, daemon=True, name="MQTT-Supervisor")
        self._thread.start()

    def stop(self):
        self._running = False
        if self.client and self.is_connected:
            try:
                self.client.loop_stop()
                self.client.disconnect()
            except Exception:
                pass
        self.is_connected = False
        logger.info(f"MQTT Service [{self.provider.upper()}] stopped.")

    def publish_reading(self, device_id: str, payload_str: str) -> bool:
        """Helper to publish telemetry to the broker if needed."""
        if self.client and self.is_connected:
            topic = get_sensor_publish_topic(device_id, provider=self.provider)
            self.client.publish(topic, payload_str, qos=1)
            return True
        return False

mqtt_service = MQTTService()
