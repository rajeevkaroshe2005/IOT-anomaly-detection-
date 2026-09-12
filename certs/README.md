# X.509 TLS Certificates Directory (`certs/`)

This directory is designated for storing AWS IoT Core X.509 certificates, private keys, and Amazon Root CA authority certificates used by the **AWS Cloud Mode** telemetry pipeline.

---

## Security Policy

> [!CAUTION]
> **NEVER COMMIT REAL CERTIFICATES OR PRIVATE KEYS TO VERSION CONTROL.**
> The root `.gitignore` is configured to ignore all `*.pem`, `*.crt`, `*.key`, and `*.csr` files inside this directory. Only `README.md` and `.gitkeep` are tracked.

---

## Required Files for AWS Cloud Mode

When configuring `MQTT_PROVIDER=aws`, download or generate the following credentials and place them in this folder:

| File Name | Purpose | Source |
|---|---|---|
| `AmazonRootCA1.pem` | Amazon Root Certificate Authority | [Amazon Trust Services](https://www.amazontrust.com/repository/AmazonRootCA1.pem) |
| `SENSOR-001.cert.pem` | Device X.509 Certificate (per sensor or shared) | AWS IoT Core Console $\rightarrow$ Things $\rightarrow$ SENSOR-001 $\rightarrow$ Certificates |
| `SENSOR-001.private.key` | Device Private Key | AWS IoT Core Console (generated during cert creation) |
| `backend-consumer.cert.pem` | Backend Subscriber Certificate | AWS IoT Core Console $\rightarrow$ Certificates |
| `backend-consumer.private.key` | Backend Subscriber Private Key | AWS IoT Core Console (generated during cert creation) |

---

## File Permission Hardening (Linux / macOS / WSL)

On POSIX-compliant environments, ensure the private keys have restricted read permissions:

```bash
chmod 600 certs/*.private.key
chmod 644 certs/*.cert.pem
chmod 644 certs/AmazonRootCA1.pem
```

---

## Downloading Amazon Root CA 1

You can download the Amazon Root CA 1 certificate using `curl` or `Invoke-WebRequest`:

### PowerShell (Windows):
```powershell
Invoke-WebRequest -Uri "https://www.amazontrust.com/repository/AmazonRootCA1.pem" -OutFile "certs/AmazonRootCA1.pem"
```

### cURL (Linux / macOS):
```bash
curl -o certs/AmazonRootCA1.pem https://www.amazontrust.com/repository/AmazonRootCA1.pem
```

---

## Reference in Environment Variables

Configure your local `.env` file to reference these certificate paths:

```dotenv
MQTT_PROVIDER=aws
AWS_REGION=us-east-1
AWS_IOT_ENDPOINT=your-ats-endpoint-prefix-ats.iot.us-east-1.amazonaws.com
AWS_IOT_ROOT_CA_PATH=certs/AmazonRootCA1.pem
AWS_IOT_CERT_PATH=certs/SENSOR-001.cert.pem
AWS_IOT_PRIVATE_KEY_PATH=certs/SENSOR-001.private.key
AWS_IOT_BACKEND_CERT_PATH=certs/backend-consumer.cert.pem
AWS_IOT_BACKEND_PRIVATE_KEY_PATH=certs/backend-consumer.private.key
```
