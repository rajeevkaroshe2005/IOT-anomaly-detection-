"""
Simulator MQTT Client Factory & Interface
Provides a unified abstraction for obtaining either the local Mosquitto MQTT client
or the AWS IoT Core TLS X.509 client based on the configured MQTT_PROVIDER.
"""

import os
import logging
from simulator.local_mqtt_client import LocalMQTTClient
from simulator.aws_iot_client import AWSIoTClient

logger = logging.getLogger("iot.simulator.factory")

def get_simulator_mqtt_client(
    provider: str = None,
    broker: str = "localhost",
    port: int = 1883,
    username: str = None,
    password: str = None,
    client_id: str = "iot-simulator-default",
    aws_endpoint: str = None,
    aws_port: int = 8883,
    root_ca_path: str = None,
    cert_path: str = None,
    private_key_path: str = None
):
    """
    Factory function returning the appropriate MQTT client instance.
    - provider='local': Returns LocalMQTTClient targeting Mosquitto.
    - provider='aws': Returns AWSIoTClient targeting AWS IoT Core with mTLS X.509.
    """
    active_provider = (provider or os.getenv("MQTT_PROVIDER", "local")).lower().strip()

    if active_provider == "aws":
        endpoint = aws_endpoint or os.getenv("AWS_IOT_ENDPOINT", "")
        if not endpoint:
            raise RuntimeError(
                "MQTT_PROVIDER is set to 'aws' but AWS_IOT_ENDPOINT is not defined in environment or arguments."
            )
        return AWSIoTClient(
            endpoint=endpoint,
            port=aws_port or int(os.getenv("AWS_IOT_PORT", "8883")),
            root_ca_path=root_ca_path or os.getenv("AWS_IOT_ROOT_CA_PATH", ""),
            cert_path=cert_path or os.getenv("AWS_IOT_CERT_PATH", ""),
            private_key_path=private_key_path or os.getenv("AWS_IOT_PRIVATE_KEY_PATH", ""),
            client_id=client_id
        )

    elif active_provider == "local":
        return LocalMQTTClient(
            broker=broker or os.getenv("MQTT_BROKER", "localhost"),
            port=port or int(os.getenv("MQTT_PORT", "1883")),
            username=username,
            password=password,
            client_id=client_id
        )

    else:
        raise ValueError(
            f"Unsupported MQTT provider '{active_provider}'. Supported values: 'local', 'aws'."
        )

__all__ = ["get_simulator_mqtt_client", "LocalMQTTClient", "AWSIoTClient"]
