# AWS IoT Core Certificates Reference (`aws/certs/`)

This directory is an informational reference guide for placing X.509 device certificates and private keys when configuring **AWS Cloud Mode**.

---

## Security Warning

> [!CAUTION]
> **DO NOT COMMIT REAL CERTIFICATES OR PRIVATE KEYS TO VERSION CONTROL.**
> The repository `.gitignore` strictly ignores `*.pem`, `*.crt`, `*.key`, and `certs/*`.

---

## Directory Setup & Placement

By default, the application and simulator look for certificates in the project root's `certs/` directory:

```
certs/
├── AmazonRootCA1.pem          # Amazon Trust Services Root CA
├── SENSOR-001.cert.pem        # Device X.509 certificate for SENSOR-001
├── SENSOR-001.private.key     # Device private key for SENSOR-001
├── backend-consumer.cert.pem  # FastAPI backend subscriber certificate
└── backend-consumer.private.key # FastAPI backend subscriber private key
```

---

## File Permissions (POSIX / Linux / macOS)

Before launching the simulator or backend service in AWS mode, restrict private key file permissions:

```bash
chmod 600 certs/*.private.key
chmod 644 certs/*.cert.pem certs/AmazonRootCA1.pem
```

---

## Root CA Download

Download the Amazon Root CA 1 file directly:

```bash
curl -o certs/AmazonRootCA1.pem https://www.amazontrust.com/repository/AmazonRootCA1.pem
```
Or via PowerShell:
```powershell
Invoke-WebRequest -Uri "https://www.amazontrust.com/repository/AmazonRootCA1.pem" -OutFile "certs/AmazonRootCA1.pem"
```
