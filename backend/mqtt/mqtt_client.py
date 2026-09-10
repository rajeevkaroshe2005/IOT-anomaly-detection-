"""
MQTT Client Ingestion Service
Subscribes to 'iot/sensors/+' using Paho MQTT.
Validates credentials and connection parameters from environment variables.
Forwards incoming sensor payloads to the Stream Processing pipeline.
"""

import os
import logging
import threading
import time
import paho.mqtt.client as mqtt
from backend.services.stream_processor import stream_processor

logger = logging.getLogger("iot.mqtt")

class MQTTService:
    def __init__(self):
        self.broker = os.getenv("MQTT_BROKER", "localhost")
        self.port = int(os.getenv("MQTT_PORT", "1883"))
        self.keepalive = int(os.getenv("MQTT_KEEPALIVE", "60"))
        self.topic = os.getenv("MQTT_TOPIC_PREFIX", "iot/sensors/") + "+"
        self.client_id = os.getenv("MQTT_CLIENT_ID", "iot_fastapi_backend_consumer")
        self.username = os.getenv("MQTT_USERNAME", "").strip()
        self.password = os.getenv("MQTT_PASSWORD", "").strip()
        self.use_tls = os.getenv("MQTT_USE_TLS", "False").lower() in ("true", "1", "yes")

        self.client = None
        self.is_connected = False
        self.last_message_time = None
        self.total_messages_received = 0
        self._thread = None
        self._running = False

    def _setup_client(self):
        try:
            # Handle Paho MQTT v2 vs v1 compatibility
            if hasattr(mqtt, "CallbackAPIVersion"):
                self.client = mqtt.Client(
                    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                    client_id=self.client_id
                )
            else:
                self.client = mqtt.Client(client_id=self.client_id)

            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)

            if self.use_tls:
                self.client.tls_set()

            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message

        except Exception as e:
            logger.error(f"Failed to initialize MQTT Client: {e}", exc_info=True)

    def _on_connect(self, client, userdata, flags, rc, *args):
        # In Paho v2, rc may be a ReasonCode object
        rc_val = getattr(rc, "value", rc)
        if rc_val == 0:
            self.is_connected = True
            logger.info(f"Connected to MQTT Broker at {self.broker}:{self.port}. Subscribing to topic: {self.topic}")
            client.subscribe(self.topic, qos=1)
        else:
            self.is_connected = False
            logger.error(f"MQTT Connection failed with return code {rc_val}")

    def _on_disconnect(self, client, userdata, rc, *args):
        self.is_connected = False
        logger.warning(f"Disconnected from MQTT Broker at {self.broker}:{self.port} (rc: {rc})")

    def _on_message(self, client, userdata, msg):
        try:
            self.total_messages_received += 1
            self.last_message_time = time.time()
            payload_str = msg.payload.decode("utf-8")
            logger.debug(f"Received MQTT payload on {msg.topic}: {payload_str[:80]}...")
            stream_processor.process_raw_payload(payload_str)
        except Exception as e:
            logger.error(f"Error handling MQTT message on {msg.topic}: {e}", exc_info=True)

    def start(self):
        """Starts the MQTT loop in a resilient background daemon thread."""
        if self._running:
            return

        self._running = True
        self._setup_client()

        def run_loop():
            logger.info(f"MQTT Ingestion thread started. Connecting to {self.broker}:{self.port}...")
            while self._running:
                try:
                    if not self.is_connected:
                        try:
                            self.client.connect(self.broker, self.port, self.keepalive)
                            self.client.loop_start()
                        except Exception as conn_err:
                            logger.info(f"MQTT Broker at {self.broker}:{self.port} not reachable: {conn_err}. Retrying in 10s...")
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
        logger.info("MQTT Service stopped.")

    def publish_reading(self, device_id: str, payload_str: str) -> bool:
        """Helper to publish telemetry to the broker if needed."""
        if self.client and self.is_connected:
            topic = f"iot/sensors/{device_id}"
            self.client.publish(topic, payload_str, qos=1)
            return True
        return False

mqtt_service = MQTTService()
