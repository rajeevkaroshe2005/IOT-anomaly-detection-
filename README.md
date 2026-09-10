# Cloud-Based Real-Time IoT Sensor Monitoring & Anomaly Detection System

A complete, production-grade, cloud-architected industrial telemetry and anomaly detection web application. Built for academic excellence (10-mark evaluation) and real-world industrial monitoring.

![System Architecture](https://raw.githubusercontent.com/username/project/main/docs/architecture_banner.png)

---

## 1. Project Overview & Problem Statement

Modern manufacturing, chemical processing, and energy facilities rely on thousands of edge IoT sensors monitoring critical environmental parameters. Traditional threshold-based monitoring triggers false alarms during seasonal temperature swings or fails to identify subtle multivariate correlations (e.g., normal temperature paired with abnormal pressure drop indicating a reactor seal breach).

This project designs and implements an end-to-end, event-driven cyber-physical system that:
1. Ingests high-frequency sensor telemetry via **MQTT**.
2. Cleanses and sanitizes data through a modular stream processing pipeline.
3. Employs an **Isolation Forest** Machine Learning algorithm to score multivariate anomalies in real time.
4. Stores telemetry, detected anomalies, and alerts in an ACID-compliant database.
5. Broadcasts live updates via **WebSockets** to an industrial SCADA dashboard.
6. Allows operators to view and resolve incidents with zero page reloads.

---

## 2. Core System Architecture & Data Flow

```
                      +-------------------+
                      |    IoT Sensors    |
                      | Temperature       |
                      | Humidity          |
                      | Pressure          |
                      +---------+---------+
                                |
                                | MQTT (iot/sensors/+)
                                v
                      +-------------------+
                      |    IoT Gateway    |
                      | Authentication    |
                      +---------+---------+
                                |
                                v
                      +-------------------+
                      |   Message Broker  |
                      | MQTT (Mosquitto)  |
                      +---------+---------+
                                |
                                v
                      +-------------------+
                      | Stream Processing |
                      | Validation        |
                      | Transformation    |
                      +---------+---------+
                                |
                      +---------+---------+
                      v                   v
            +------------------+ +-----------------+
            | ML Anomaly Model | | Cloud Database  |
            | Isolation Forest | | Sensor History  |
            +--------+---------+ +--------+--------+
                     |                    |
                     +---------+----------+
                               |
                               v
                      +-------------------+
                      |  FastAPI Backend  |
                      | REST + WebSocket  |
                      +---------+---------+
                                |
                                v
                      +-------------------+
                      |   Web Dashboard   |
                      | Live Monitoring   |
                      | Charts & Alerts   |
                      +-------------------+
```

### Complete End-to-End Data Flow

1. **IoT Sensor Simulator** (`simulator/sensor_simulator.py`) generates multi-sensor telemetry every 1.5 seconds with Markovian drift and occasional stochastic anomalies.
2. Telemetry packets are published to MQTT broker topic `iot/sensors/<device_id>`.
3. **Paho MQTT Ingestion Client** (`backend/mqtt/mqtt_client.py`) receives packets asynchronously.
4. **Stream Processor** (`backend/services/stream_processor.py`) parses JSON, validates missing values, and assembles the feature vector $[T, H, P]$.
5. **Isolation Forest Model** (`backend/ml/ml_model.py`) evaluates the vector, computing normalized anomaly scores and severity.
6. Readings, anomalies, and active alerts are committed to **Database** (`backend/database/`).
7. **WebSocket Manager** (`backend/services/websocket_manager.py`) broadcasts events to all active browser sessions.
8. **React SCADA Dashboard** automatically updates KPI counters, charts, and alert banners in real time.

---

## 3. Technology Stack

### Frontend
- **Framework:** React 18 (Vite Bundler)
- **Styling:** Tailwind CSS (Strict Industrial Control Room Aesthetic)
- **Charts:** Recharts (Real-Time Oscilloscope Telemetry)
- **Icons:** Lucide React
- **Routing:** React Router v6
- **Real-Time Client:** Persistent WebSocket with automatic reconnection backoff

### Backend & API
- **Language:** Python 3.14 / 3.11+
- **Framework:** FastAPI
- **Web Server:** Uvicorn (ASGI AsyncIO)
- **Data Modeling:** Pydantic v2
- **Authentication:** Stateless JWT (HS256) + PBKDF2 Password Hashing
- **Security:** Role-Based Access Control (`ADMIN` and `VIEWER`)

### Database
- **Primary:** PostgreSQL 16 (Cloud-Ready)
- **Embedded Fallback:** SQLite with WAL mode (Zero-config local execution)
- **ORM:** SQLAlchemy 2.0 with indexed composite keys

### Machine Learning
- **Algorithm:** Isolation Forest (`n_estimators=150`, `contamination=0.05`, `random_state=42`)
- **Libraries:** Scikit-Learn, NumPy, Pandas, Joblib
- **Outputs:** Anomaly Classification (`NORMAL` / `ANOMALY`), Normalized Anomaly Score (0.00 to 1.00), Severity (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), and classification reason

### IoT & Transport
- **Protocol:** MQTT (ISO/IEC 20922)
- **Client Library:** Paho MQTT v2
- **Local Broker:** Eclipse Mosquitto 2.0
- **Cloud Ready:** AWS IoT Core, Azure IoT Hub, Google Cloud Pub/Sub

---

## 4. Industrial SCADA Color Palette & UI Design

In strict compliance with modern industrial ergonomics, this application **avoids all generic AI purple/blue gradients, glassmorphism, and neon aesthetics**:

| Category | Token Name | Hex Code | Visual Application |
| :--- | :--- | :--- | :--- |
| **Primary** | Deep Forest Green | `#16423C` | Sidebar, Top Branding, Primary Action Buttons |
| **Primary** | Dark Teal | `#1F5C54` | Secondary Headers, Table Accents |
| **Secondary** | Warm Amber | `#D99A2B` | Navigation Active Marker, Warning Badges |
| **Secondary** | Burnt Orange | `#C96B32` | **Temperature Chart Line & Badges** |
| **Background** | Warm Off-White | `#F5F1E8` | Main Workspace Background |
| **Background** | Soft Beige | `#E9E2D3` | Card Borders, Subtle Dividers |
| **Surface** | Pure White | `#FFFFFF` | SCADA Cards, Metric Panels |
| **Status** | Normal Green | `#2E7D32` | Normal Status Badges, System Online |
| **Status** | Warning Amber | `#D99A2B` | Medium / Warning Alert State |
| **Status** | Anomaly Dark Red | `#B23A2F` | **Critical Alerts, Outlier Chart Points** |
| **Status** | Offline Gray | `#6B6B6B` | Offline Nodes, Inactive Devices |

---

## 5. Quick Start & Installation

### Option A: Local Development (Zero Third-Party Broker Requirement)

The platform is designed to run seamlessly out of the box using SQLite and direct stream pipeline bridging if Mosquitto is not installed locally.

#### Prerequisites
- Python 3.10+ (Tested on Python 3.11 - 3.14)
- Node.js 18+ and npm

#### 1. Setup Backend
```bash
# In the project root:
python -m pip install -r requirements.txt

# Train baseline ML model (pre-trained model is already included):
python ml/train_model.py

# Start FastAPI backend:
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
*The database (`iot_sensor.db`) is automatically initialized on first boot with 5 demo sensors, admin/viewer users, and 150+ realistic readings.*

#### 2. Setup Frontend
```bash
# In another terminal:
cd frontend
npm install
npm run dev
```
Open **http://localhost:5173** in your browser.

#### 3. Default Demo Credentials
| Role | Username | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `admin123` | Full CRUD on sensors, resolve alerts, start/stop simulator |
| **Viewer** | `viewer` | `viewer123` | View monitoring dashboard, telemetry charts, and logs |

---

### Option B: Docker Compose (Production Environment)

To run the complete production stack (React Frontend, FastAPI Backend, PostgreSQL 16, and Eclipse Mosquitto):

```bash
docker compose up --build
```

- **Web Dashboard:** `http://localhost:3000`
- **FastAPI Documentation:** `http://localhost:8000/docs`
- **MQTT Broker:** `localhost:1883`
- **PostgreSQL:** `localhost:5432`

---

## 6. Real-Time Sensor Simulator

The simulator emulates 5 industrial sensor nodes:
- `SENSOR-001`: Main Assembly Line 1 (Production Floor)
- `SENSOR-002`: Cold Storage Unit 3 (Warehouse)
- `SENSOR-003`: Steam Boiler Reactor (Boiler Room)
- `SENSOR-004`: Packaging Conveyor B (Assembly Line)
- `SENSOR-005`: Raw Chemical Silo (Storage Area)

### How to Run the Simulator:
1. **Via Web Dashboard (Turnkey):** Simply click the **"START SIMULATION"** button located in the top navigation bar or the Admin Control Deck.
2. **Via Standalone CLI:**
```bash
python simulator/sensor_simulator.py --interval 1.5 --anomaly-rate 0.10
```

---

## 7. REST API Documentation

The FastAPI backend automatically generates interactive Swagger/OpenAPI documentation at `http://localhost:8000/docs`.

### Key Endpoints

| Method | Endpoint | Description | Role Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/login` | Authenticate and issue JWT bearer token | Public |
| `GET` | `/api/auth/me` | Retrieve active operator profile | Authenticated |
| `GET` | `/api/sensors` | List all sensors with live latest readings | Public |
| `POST` | `/api/sensors` | Register a new industrial sensor node | ADMIN |
| `GET` | `/api/sensors/{id}` | Retrieve detailed sensor telemetry specs | Public |
| `PUT` | `/api/sensors/{id}` | Modify sensor name, location, or status | ADMIN |
| `DELETE` | `/api/sensors/{id}` | Delete sensor node from inventory | ADMIN |
| `POST` | `/api/sensors/{id}/toggle` | Enable or disable sensor stream | ADMIN |
| `GET` | `/api/readings` | Query historical sensor telemetry readings | Public |
| `GET` | `/api/readings/{sensor_id}` | Filter readings by timeframe (`1m`, `5m`, `30m`, `1h`) | Public |
| `POST` | `/api/readings/ingest` | Direct HTTP fallback ingestion bridge | Public |
| `GET` | `/api/anomalies` | Query machine learning detected outliers | Public |
| `GET` | `/api/alerts` | Query active and resolved industrial alerts | Public |
| `PUT` | `/api/alerts/{id}/resolve` | Mark an alert incident as resolved | ADMIN |
| `DELETE` | `/api/alerts/{id}` | Delete alert record | ADMIN |
| `GET` | `/api/dashboard/stats` | Retrieve dynamic system metrics and KPI counters | Public |
| `GET` | `/api/system/health` | Query health probes for all 6 subsystems | Public |
| `GET` | `/api/predictive/analytics` | Fleet-wide predictive drift ($dT/dt, dP/dt$) & RUL analysis | Public |
| `GET` | `/api/predictive/sensor/{id}` | Single sensor degradation trajectory & breach forecast | Public |
| `GET` | `/api/readings/export/csv` | Stream telemetry readings as CSV spreadsheet | Public |
| `GET` | `/api/anomalies/export/csv` | Stream anomaly audit log as CSV spreadsheet | Public |
| `POST` | `/api/simulator/start` | Start background sensor fleet simulation | Public / ADMIN |
| `POST` | `/api/simulator/stop` | Stop background sensor fleet simulation | Public / ADMIN |
| `POST` | `/api/simulator/force-anomaly`| Instantly inject an outlier for live evaluation | Public / ADMIN |
| `WS` | `/ws/sensor-data` | Persistent bidirectional WebSocket telemetry stream | Public |

---

## 8. Advanced SCADA & Portfolio Enhancements

Beyond standard telemetry dashboards, this system integrates enterprise-grade industrial features:
1. **Interactive 2D Digital Twin Plant Map (`/plant-map`):**
   - Spatial layout of industrial zones (Production Floor, Warehouse, Boiler Reactor, Assembly, Storage).
   - Real-time pulsating radar beacons with live telemetry overlays and zone hazard flares.
2. **Predictive Maintenance & Time-to-Failure (RUL) Engine:**
   - Linear drift rate estimation ($\frac{dT}{dt}$ °C/min, $\frac{dP}{dt}$ hPa/min) over rolling time windows.
   - Dynamic threshold breach extrapolation calculating exact minutes before catastrophic thermal/pressure limits are crossed.
   - Component health degradation index ($0\%-100\%$) with prescriptive operational action advisories.
3. **Synthesized Web Audio API SCADA Alarm Buzzer:**
   - Dual-tone ($880\text{ Hz} \leftrightarrow 440\text{ Hz}$) pulsing audio alert triggered automatically on critical anomaly detection.
   - Global mute/unmute control in the application header with persistent sound settings.
4. **One-Click Telemetry & Incident CSV Exporter:**
   - Direct streaming CSV export for both sensor telemetry readings and ML anomaly audit logs.
5. **Automated GitHub Actions CI/CD Pipeline (`.github/workflows/ci.yml`):**
   - Automated continuous integration running backend diagnostics, ML model loading checks, and frontend Vite production builds.

---

## 9. Academic Project Demonstration Script (14-Step Flow)

To execute the live 10-mark examination demonstration:

1. **Step 1 - Open Dashboard:** Navigate to `http://localhost:5173`. Point out the dynamic KPI counters (Total Sensors: 05, Online Sensors, Total Readings, Anomalies, System Health).
2. **Step 2 - Architecture Page:** Click `ARCHITECTURE` in the sidebar. Show the interactive 11-stage logical diagram, component breakdowns, and multi-cloud deployment mapping.
3. **Step 3 - Sensors Inventory:** Open `Sensors`. Demonstrate the 5 industrial sensors across Production Floor, Warehouse, Boiler Room, Assembly Line, and Storage Area.
4. **Step 4 - Start Simulator:** Click the **"START SIMULATION"** button in the header. Observe the status toggle to green.
5. **Step 5 - Live Values Changing:** Return to the Dashboard or Sensors table. Point out live values changing every 1.5 seconds without page reloading.
6. **Step 6 - Live Monitoring:** Open `Live Monitoring`. Show real-time Recharts oscilloscope lines.
7. **Step 7 - Verify Chart Colors:** Confirm:
   - Temperature is **Burnt Orange (`#C96B32`)**
   - Humidity is **Deep Teal (`#1F5C54`)**
   - Pressure is **Forest Green (`#16423C`)**
8. **Step 8 & 9 - Anomaly Injection & Detection:** Click `Admin` -> **"FORCE ANOMALY INJECTION"**. Observe the Isolation Forest model detecting the outlier.
9. **Step 10 - Dashboard Notification:** Watch the red banner toast appear immediately with device ID, score, and reason.
10. **Step 11 - Alert Generation:** Show the alert count incrementing in the top pill and in the Recent Alerts widget.
11. **Step 12 - Anomalies Page:** Open `Anomalies`. Inspect the table with timestamp, readings, score, and severity.
12. **Step 13 - Scalability Explanation:** Reference Section 18 of the Architecture page; explain Kafka partitions, horizontal pod scaling, and time-series hypertables.
13. **Step 14 - Security Explanation:** Highlight JWT token generation, role segregation (Admin vs Viewer), parameterized queries, and TLS encryption.

---

## 9. License & Academic Attribution

Developed for academic demonstration and industrial IoT research. Released under the MIT License.
