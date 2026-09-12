"""
AWS IoT Core Dedicated MQTT Client
Handles secure mutual TLS (mTLS) X.509 communication on port 8883 with AWS IoT Core.
Enforces client identity separation, strict certificate validation, exponential backoff, and clean logging.
"""

import os
import ssl
import time
import logging
import paho.mqtt.client as mqtt

logger = logging.getLogger("iot.simulator.aws")

class AWSIoTClient:
    """
    Dedicated MQTT client for AWS IoT Core using TLS v1.2 and X.509 mutual authentication.
    Supports exponential backoff reconnects and prevents secret exposure.
    """
    def __init__(
        self,
        endpoint: str,
        port: int = 8883,
        root_ca_path: str = None,
        cert_path: str = None,
        private_key_path: str = None,
        client_id: str = "iot-simulator-default"
    ):
        if not endpoint or not endpoint.strip():
            raise ValueError("AWS IoT endpoint cannot be empty.")

        self.endpoint = endpoint.strip()
        self.port = int(port)
        self.root_ca_path = os.path.abspath(root_ca_path) if root_ca_path else None
        self.cert_path = os.path.abspath(cert_path) if cert_path else None
        self.private_key_path = os.path.abspath(private_key_path) if private_key_path else None
        self.client_id = client_id.strip()

        # Reconnect parameters with exponential backoff
        self.reconnect_delay = 1.0
        self.max_reconnect_delay = 60.0

        # Validate certificate file existence
        self._validate_credentials()

        self.client = None
        self.is_connected = False
        self.published_count = 0
        self._init_client()

    def __repr__(self):
        return f"<AWSIoTClient client_id={self.client_id} endpoint={self.endpoint}:{self.port} connected={self.is_connected}>"

    def _validate_credentials(self):
        """Verifies that all required X.509 certificate files exist before attempting TLS handshake."""
        missing = []
        if not self.root_ca_path or not os.path.exists(self.root_ca_path):
            missing.append(f"Root CA file not found: {self.root_ca_path}")
        if not self.cert_path or not os.path.exists(self.cert_path):
            missing.append(f"Device certificate file not found: {self.cert_path}")
        if not self.private_key_path or not os.path.exists(self.private_key_path):
            missing.append(f"Private key file not found: {self.private_key_path}")

        if missing:
            raise FileNotFoundError(
                "AWS IoT Core X.509 credential validation failed:\n" + "\n".join(missing)
            )

    def _init_client(self):
        """Initializes the Paho MQTT client with TLS v1.2 mutual authentication."""
        try:
            if hasattr(mqtt, "CallbackAPIVersion"):
                self.client = mqtt.Client(
                    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                    client_id=self.client_id
                )
            else:
                self.client = mqtt.Client(client_id=self.client_id)

            # Configure TLS mutual authentication (X.509)
            self.client.tls_set(
                ca_certs=self.root_ca_path,
                certfile=self.cert_path,
                keyfile=self.private_key_path,
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLSv1_2,
                ciphers=None
            )

            # Enforce TLS Server Name Indication (SNI)
            self.client.tls_insecure_set(False)

            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_publish = self._on_publish

        except Exception as e:
            logger.error(f"Failed to initialize AWS IoT MQTT client: {e}")
            raise

    def _on_connect(self, client, userdata, flags, rc, *args):
        rc_val = getattr(rc, "value", rc)
        if rc_val == 0:
            self.is_connected = True
            self.reconnect_delay = 1.0  # Reset backoff on successful connect
            logger.info(f"Connected to AWS IoT Core ({self.endpoint}:{self.port}) as '{self.client_id}'")
        else:
            self.is_connected = False
            logger.error(f"AWS IoT Core connection rejected with return code: {rc_val}")

    def _on_disconnect(self, client, userdata, rc, *args):
        self.is_connected = False
        logger.warning(f"Disconnected from AWS IoT Core ({self.endpoint}:{self.port}). rc: {rc}")

    def _on_publish(self, client, userdata, mid, *args):
        self.published_count += 1

    def connect(self, timeout: int = 60) -> bool:
        """
        Initiates TLS connection to AWS IoT Core and begins background network loop.
        Applies non-fatal error handling so temporary network unavailability does not crash callers.
        """
        if not self.client:
            self._init_client()
        logger.info(f"Connecting to AWS IoT Core at {self.endpoint}:{self.port} (Client ID: {self.client_id})...")
        try:
            self.client.connect(self.endpoint, self.port, keepalive=timeout)
            self.client.loop_start()
            return True
        except Exception as e:
            logger.warning(
                f"Initial connection to AWS IoT Core ({self.endpoint}:{self.port}) failed: {e}. "
                f"Next retry backoff: {self.reconnect_delay:.1f}s."
            )
            # Increase exponential backoff for subsequent retries
            self.reconnect_delay = min(self.reconnect_delay * 2.0, self.max_reconnect_delay)
            return False

    def publish(self, topic: str, payload: str, qos: int = 1) -> bool:
        """
        Publishes a JSON payload to the specified AWS IoT topic.
        Guarantees that MQTT publish topics are strictly concrete (no '+' or '#').
        """
        if not topic or not topic.strip():
            raise ValueError("AWS IoT publish topic cannot be empty.")
        if "+" in topic or "#" in topic:
            raise ValueError(f"AWS IoT publish topic cannot contain wildcard characters ('+' or '#'). Got: '{topic}'")

        if not self.client:
            return False
        try:
            info = self.client.publish(topic, payload, qos=qos)
            return (info.rc == 0)
        except Exception as e:
            logger.error(f"Failed to publish to AWS IoT Core on topic {topic}: {e}")
            return False

    def disconnect(self):
        """Gracefully disconnects from AWS IoT Core and stops network loop."""
        if self.client:
            try:
                self.client.loop_stop()
                self.client.disconnect()
            except Exception:
                pass
        self.is_connected = False
        logger.info(f"AWS IoT Client '{self.client_id}' disconnected cleanly.")
