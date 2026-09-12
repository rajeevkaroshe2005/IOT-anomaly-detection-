# AWS IoT Core Cloud Integration Guide

This guide details the complete process for deploying, configuring, and running the **Industrial IoT Sensor Monitoring & Anomaly Detection System** in **AWS Cloud Mode** using **AWS IoT Core**.

---

## 1. Operating Modes Overview

The architecture provides two runtime telemetry ingestion modes governed by `MQTT_PROVIDER`:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               OPERATING MODE ARCHITECTURE                               │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. LOCAL DEVELOPMENT MODE (Default: MQTT_PROVIDER=local)                               │
│    Edge Simulator ──(Port 1883)──> Mosquitto Broker ──> Stream Processor ──> ML/DB/UI  │
│                                                                                        │
│ 2. AWS CLOUD MODE (MQTT_PROVIDER=aws)                                                  │
│    Edge Simulator ──(Port 8883, TLS v1.2 mTLS)──> AWS IoT Core ──> Ingest Service ──> ML/DB/UI │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

Both modes feed into the identical unsupervised **Isolation Forest** machine learning engine, real-time alert cycle, SQLite/PostgreSQL storage layer, and React industrial dashboard.

---

## 2. Step-by-Step Setup Guide (13 Steps)

### Step 1: Select AWS Region
Select an AWS region with AWS IoT Core availability (e.g., `us-east-1`, `eu-west-1`, or `ap-south-1`).
```bash
export AWS_DEFAULT_REGION="us-east-1"
```

---

### Step 2: Create IoT Things
Create the 5 industrial sensor things in AWS IoT Core:
```bash
for id in SENSOR-001 SENSOR-002 SENSOR-003 SENSOR-004 SENSOR-005; do
  aws iot create-thing --thing-name "$id"
done
```

---

### Step 3: Generate X.509 Device Certificates & Private Keys
Generate an X.509 certificate and private key for each device (or use a shared certificate across the fleet for staging):
```bash
aws iot create-keys-and-certificate \
  --set-as-active \
  --certificate-pem-outfile "certs/SENSOR-001.cert.pem" \
  --public-key-outfile "certs/SENSOR-001.public.key" \
  --private-key-outfile "certs/SENSOR-001.private.key"
```
*(Save the returned `certificateArn` for policy attachment in Step 6).*

---

### Step 4: Download Amazon Root CA 1
Download the official Amazon Trust Services (ATS) Root CA certificate into `certs/`:

#### PowerShell:
```powershell
Invoke-WebRequest -Uri "https://www.amazontrust.com/repository/AmazonRootCA1.pem" -OutFile "certs/AmazonRootCA1.pem"
```

#### Linux / macOS:
```bash
curl -o certs/AmazonRootCA1.pem https://www.amazontrust.com/repository/AmazonRootCA1.pem
```

---

### Step 5: Create Parameterized Device Policy
Create the least-privilege device policy using `${iot:Connection.Thing.ThingName}`:
```bash
aws iot create-policy \
  --policy-name "IndustrialSensorThingPolicy" \
  --policy-document file://aws/iot/policies/sensor-thing-policy.json
```

---

### Step 6: Attach Device Policy & Certificate to Thing
Attach the policy and certificate to `SENSOR-001`:
```bash
# Attach policy to certificate
aws iot attach-policy \
  --policy-name "IndustrialSensorThingPolicy" \
  --target "<CERTIFICATE_ARN>"

# Attach certificate to Thing
aws iot attach-thing-principal \
  --thing-name "SENSOR-001" \
  --principal "<CERTIFICATE_ARN>"
```

---

### Step 7: Create Backend Consumer Certificate & Policy
The backend ingestion service requires subscriber credentials:
```bash
# Generate backend certificate
aws iot create-keys-and-certificate \
  --set-as-active \
  --certificate-pem-outfile "certs/backend-consumer.cert.pem" \
  --public-key-outfile "certs/backend-consumer.public.key" \
  --private-key-outfile "certs/backend-consumer.private.key"

# Create backend subscriber policy
aws iot create-policy \
  --policy-name "IndustrialBackendConsumerPolicy" \
  --policy-document file://aws/iot/policies/backend-consumer-policy.json

# Attach policy to backend certificate
aws iot attach-policy \
  --policy-name "IndustrialBackendConsumerPolicy" \
  --target "<BACKEND_CERTIFICATE_ARN>"
```

---

### Step 8: Retrieve ATS IoT Core Endpoint
Query your AWS account's Amazon Trust Services (ATS) data endpoint:
```bash
aws iot describe-endpoint --endpoint-type iot:Data-ATS
```
Output example:
```json
{
  "endpointAddress": "a1b2c3d4e5f6g7-ats.iot.us-east-1.amazonaws.com"
}
```

---

### Step 9: Place Certificates in `certs/` and Verify Permissions
Ensure files are located in `certs/`:
- `certs/AmazonRootCA1.pem`
- `certs/SENSOR-001.cert.pem`
- `certs/SENSOR-001.private.key`
- `certs/backend-consumer.cert.pem`
- `certs/backend-consumer.private.key`

On Linux/macOS:
```bash
chmod 600 certs/*.private.key
chmod 644 certs/*.cert.pem certs/AmazonRootCA1.pem
```

---

### Step 10: Configure `.env` for AWS Cloud Mode
Update your `.env` file:
```dotenv
MQTT_PROVIDER=aws
AWS_REGION=us-east-1
AWS_IOT_ENDPOINT=a1b2c3d4e5f6g7-ats.iot.us-east-1.amazonaws.com
AWS_IOT_PORT=8883
AWS_IOT_ROOT_CA_PATH=certs/AmazonRootCA1.pem
AWS_IOT_CERT_PATH=certs/SENSOR-001.cert.pem
AWS_IOT_PRIVATE_KEY_PATH=certs/SENSOR-001.private.key
AWS_IOT_BACKEND_CERT_PATH=certs/backend-consumer.cert.pem
AWS_IOT_BACKEND_PRIVATE_KEY_PATH=certs/backend-consumer.private.key
```

---

### Step 11: Start Backend Telemetry Ingestion Service
Start the FastAPI application:
```powershell
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
The backend automatically initializes `MQTTService` in AWS mode, validates certificate paths, and subscribes to `industrial/sensors/+/telemetry`.

---

### Step 12: Run Edge Simulator in AWS Mode
Launch the simulator configured for AWS IoT Core:
```powershell
python simulator/sensor_simulator.py --provider aws
```
Or target an individual device:
```powershell
python simulator/sensor_simulator.py --provider aws --device SENSOR-001
```

---

### Step 13: Verify Ingestion in AWS Console & Dashboard
1. Open the **AWS IoT Core Console** $\rightarrow$ **MQTT test client**.
2. Subscribe to topic: `industrial/sensors/+/telemetry`.
3. Verify incoming JSON telemetry packets.
4. Open the local dashboard at `http://localhost:5173`.
5. Check **System Health** $\rightarrow$ `AWS IoT Core Broker` displays **ONLINE**.
6. Check **Live Telemetry** and **Anomaly Radar** to view real-time inferences and automated alerts.

---

## 3. Developer IAM vs AWS IoT Device Policy

| Dimension | Developer / Operator Identity | Edge IoT Device Identity |
|---|---|---|
| **Mechanism** | AWS IAM User / Role / SSO | X.509 Client Certificate (mTLS) |
| **Credentials** | Access Key ID & Secret Access Key | Private Key (`.key`) & X.509 Cert (`.cert.pem`) |
| **Authentication Port** | HTTPS / 443 (REST API) | TLS / 8883 (MQTT over mTLS) |
| **Policy Type** | IAM Policy (JSON) | AWS IoT Policy (JSON) |
| **Context Variables** | `aws:PrincipalArn`, `aws:username` | `${iot:Connection.Thing.ThingName}`, `${iot:ClientId}` |
| **Security Rule** | Never embed in edge devices | Bound cryptographically to device private key |

> [!IMPORTANT]
> **Edge devices MUST NEVER store AWS IAM Access Keys.** AWS IoT Core uses X.509 client certificates verified by mutual TLS. The client certificate is attached to an AWS IoT Policy that restricts actions strictly to that device's telemetry topic.

---

## 4. Cost Safety & Free Tier Guidelines

1. **AWS Free Tier**: AWS IoT Core provides 250,000 free messages (published or delivered) per month for 12 months.
2. **Simulation Control**: Keep simulator interval $\ge 1.5$ seconds to avoid unnecessary message volume during testing.
3. **Keepalive Tuning**: Standard keepalive is set to 60 seconds.
4. **Shutdown**: When done testing, stop the simulator (`Ctrl+C`) to cease outbound message publication.
