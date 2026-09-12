"""
Local MQTT Client for Edge Sensor Simulator
Connects to local Eclipse Mosquitto broker over standard unencrypted MQTT (port 1883).
Supports password authentication, non-blocking connection attempts, and automatic reconnects.
"""

import os
import logging
import paho.mqtt.client as mqtt

logger = logging.getLogger("iot.simulator.local")

class LocalMQTTClient:
    """
    Dedicated MQTT client for local Mosquitto message broker.
    """
    def __init__(
        self,
        broker: str = "localhost",
        port: int = 1883,
        username: str = None,
        password: str = None,
        client_id: str = "iot_simulator_publisher"
    ):
        self.broker = broker
        self.port = int(port)
        self.username = username or os.getenv("MQTT_USERNAME", "iot_simulator").strip()
        self.password = password or os.getenv("MQTT_PASSWORD", "").strip()
        self.client_id = client_id

        self.client = None
        self.is_connected = False
        self.total_published = 0
        self._init_client()

    def _init_client(self):
        try:
            if hasattr(mqtt, "CallbackAPIVersion"):
                self.client = mqtt.Client(
                    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                    client_id=self.client_id
                )
            else:
                self.client = mqtt.Client(client_id=self.client_id)

            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)

            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect

        except Exception as e:
            logger.error(f"Failed to initialize local MQTT client: {e}")

    def _on_connect(self, client, userdata, flags, rc, *args):
        rc_val = getattr(rc, "value", rc)
        if rc_val == 0:
            self.is_connected = True
            logger.info(f"Connected to local MQTT broker at {self.broker}:{self.port}")
        else:
            self.is_connected = False
            logger.warning(f"Local MQTT connection returned code: {rc_val}")

    def _on_disconnect(self, client, userdata, rc, *args):
        self.is_connected = False
        logger.info(f"Disconnected from local MQTT broker at {self.broker}:{self.port}")

    def connect(self, timeout: int = 60):
        """Non-blocking connection attempt to the local broker."""
        if not self.client:
            self._init_client()
        try:
            self.client.connect(self.broker, self.port, timeout)
            self.client.loop_start()
        except Exception as conn_err:
            logger.info(f"Local broker at {self.broker}:{self.port} not currently reachable ({conn_err}).")

    def publish(self, topic: str, payload: str, qos: int = 1) -> bool:
        """Publishes a payload to the given topic."""
        if not self.client:
            return False
        try:
            res = self.client.publish(topic, payload, qos=qos)
            if res.rc == 0:
                self.total_published += 1
                return True
            return False
        except Exception as e:
            logger.error(f"Error publishing to local MQTT: {e}")
            return False

    def disconnect(self):
        """Gracefully disconnects and stops background network loop."""
        if self.client:
            try:
                self.client.loop_stop()
                self.client.disconnect()
            except Exception:
                pass
        self.is_connected = False
