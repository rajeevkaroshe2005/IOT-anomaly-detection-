"""
Optional AWS Lambda Event Handler: Telemetry Event Notifier
Invoked via AWS IoT Topic Rule (aws/iot/rules/lambda-trigger-rule.json).
Demonstrates event-driven AWS serverless architecture by logging critical events
and publishing operational metrics to Amazon CloudWatch.
NOTE: The core multivariate Isolation Forest anomaly detection pipeline remains
in the primary application stream processor.
"""

import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Handles event-driven sensor telemetry alerts routed from AWS IoT Core.
    """
    logger.info(f"Received IoT event: {json.dumps(event)}")

    device_id = event.get("device_id", "UNKNOWN_DEVICE")
    temperature = event.get("temperature")
    humidity = event.get("humidity")
    pressure = event.get("pressure")
    timestamp = event.get("timestamp", datetime.now(timezone.utc).isoformat())

    # Formulate alert details
    anomaly_reasons = []
    if temperature is not None and temperature > 50.0:
        anomaly_reasons.append(f"High Temperature ({temperature}°C > 50.0°C)")
    if humidity is not None and humidity < 20.0:
        anomaly_reasons.append(f"Low Humidity ({humidity}% < 20.0%)")
    if pressure is not None and pressure < 950.0:
        anomaly_reasons.append(f"Low Pressure ({pressure}hPa < 950.0hPa)")

    # CloudWatch Structured EMF Metric Log
    cloudwatch_metric = {
        "_aws": {
            "Timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
            "CloudWatchMetrics": [
                {
                    "Namespace": "IndustrialIoT/Sensors",
                    "Dimensions": [["DeviceId"]],
                    "Metrics": [{"Name": "ThresholdBreachCount", "Unit": "Count"}]
                }
            ]
        },
        "DeviceId": device_id,
        "ThresholdBreachCount": 1,
        "Temperature": temperature,
        "Humidity": humidity,
        "Pressure": pressure,
        "AlertReasons": anomaly_reasons
    }
    print(json.dumps(cloudwatch_metric))

    logger.info(f"Alert processed for {device_id}: {'; '.join(anomaly_reasons)}")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "status": "PROCESSED",
            "device_id": device_id,
            "timestamp": timestamp,
            "reasons": anomaly_reasons
        })
    }
