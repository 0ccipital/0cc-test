# Comprehensive Radio Frequency Monitoring & Security Analysis Platform
## Complete Implementation Guide

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture & Design](#architecture--design)
3. [Hardware Requirements](#hardware-requirements)
4. [Software Stack](#software-stack)
5. [Step-by-Step Implementation](#step-by-step-implementation)
6. [Machine Learning Integration](#machine-learning-integration)
7. [Operational Procedures](#operational-procedures)
8. [Security & Maintenance](#security--maintenance)
9. [Advanced Capabilities](#advanced-capabilities)
10. [Troubleshooting & Support](#troubleshooting--support)

---

## Project Overview

### What This System Does

This comprehensive platform creates a multi-layered radio frequency monitoring and security analysis system that provides unprecedented visibility into your electromagnetic environment. By combining enterprise-grade WiFi monitoring, dedicated RF scanning, portable investigation tools, and advanced machine learning analysis, you'll have professional-level capabilities for:

- **Continuous RF Environment Monitoring** across WiFi, ISM bands, and Bluetooth
- **Automated Threat Detection** using correlation analysis across multiple radio bands
- **Active Investigation Capabilities** for unknown or suspicious signals
- **Machine Learning-Based Anomaly Detection** for sophisticated attack identification
- **Comprehensive Security Assessment** of your radio frequency environment

### Why This Approach Works

**Multi-Band Coverage:** Different attack vectors use different frequency bands. WiFi attacks operate in 2.4/5GHz, while many IoT exploits use 433MHz, 868MHz, or 915MHz ISM bands. This system monitors all simultaneously.

**Correlation Analysis:** Sophisticated attacks often coordinate across multiple bands. By correlating events across WiFi, SubGHz, and Bluetooth, you can detect attacks that would be invisible to single-band monitoring.

**Active Investigation:** Passive monitoring can only detect known patterns. The Flipper Zero provides active investigation capabilities to analyze unknown signals and test security assumptions.

**Professional-Grade Infrastructure:** Using UniFi enterprise equipment provides calibrated, reliable baseline monitoring that consumer equipment cannot match.

---

## Architecture & Design

### System Components & Roles

#### UniFi Network Infrastructure (Detection Layer)
**Primary Function:** Enterprise-grade WiFi monitoring and baseline establishment

**Capabilities:**
- Continuous spectrum analysis on 2.4GHz and 5GHz bands
- Automatic rogue AP detection using signature analysis
- Client device tracking and behavioral analysis
- Real-time interference detection and source identification
- Precise timing for correlation with other monitoring systems

**Why UniFi:** Professional RF hardware with calibrated antennas, proven enterprise monitoring capabilities, and comprehensive API access for automation.

#### Unraid Server (Processing Hub)
**Primary Function:** Data aggregation, analysis, and long-term storage

**Capabilities:**
- Centralized database for all RF monitoring data
- Machine learning pipeline for pattern recognition
- Historical analysis for trend identification
- Alert correlation across all monitoring sources
- Web-based dashboards for unified system view

**Why Unraid:** Docker-based service deployment, high storage capacity, always-on availability, and excellent community support for monitoring applications.

#### Raspberry Pi 4 (Dedicated Monitor)
**Primary Function:** Specialized RF monitoring and real-time processing

**Capabilities:**
- RTL-SDR integration for ISM band monitoring (433MHz, 868MHz, 915MHz)
- Bluetooth Low Energy scanning for IoT device discovery
- Real-time signal processing with immediate alerting
- Protocol analysis for unknown signals
- Bridge between Flipper Zero and server infrastructure

**Why Raspberry Pi:** Low power consumption for 24/7 operation, GPIO capabilities for hardware integration, dedicated hardware prevents interference with main server operations.

#### Flipper Zero with WiFi Dev Board (Investigation Platform)
**Primary Function:** Active investigation and signal analysis

**Capabilities:**
- On-demand deep scanning triggered by automated alerts
- Protocol reverse engineering for unknown signals
- Active signal injection for security testing
- Mobile deployment for investigating remote signals
- Real-time collaboration with fixed monitoring infrastructure

**Why Flipper Zero:** Momentum firmware provides extended capabilities, portable form factor, active transmission abilities, and strong community support for custom applications.

### Data Flow Architecture

```
[UniFi APs] → [UniFi Controller] → [Syslog] → [Unraid Server]
     ↓                                            ↑
[Spectrum Data] ────────────────────────────────────┘

[RTL-SDR] → [Raspberry Pi] → [MQTT] → [Unraid Server]
     ↓                                      ↑
[ISM Band Data] ──────────────────────────────┘

[Flipper Zero] → [WiFi Dev Board] → [HTTP/MQTT] → [Unraid Server]
     ↓                                              ↑
[Investigation Data] ─────────────────────────────────┘

[Unraid Server] → [ML Analysis] → [Alerts] → [Investigation Triggers]
     ↓                                              ↓
[Dashboard] ←─────────────────────────────────── [Flipper Zero]
```

---

## Hardware Requirements

### UniFi Network Equipment

**UniFi Dream Machine (UDM) or Cloud Key**
- Minimum: UDM Standard or Cloud Key Gen2+
- Recommended: UDM Pro for advanced features
- Purpose: Network controller and data processing

**Access Points (Minimum 2)**
- Minimum: UniFi AP AC Lite or newer
- Recommended: UniFi AP WiFi 6 Pro for advanced spectrum analysis
- Placement: Opposite ends of property for triangulation
- Features needed: Spectrum analysis, rogue AP detection

**Network Infrastructure**
- Gigabit Ethernet to each AP
- PoE+ capability for AP power
- Managed switch with VLAN support (recommended)

### Unraid Server Specifications

**Minimum Requirements:**
- CPU: Intel i5 or AMD Ryzen 5 (4+ cores)
- RAM: 16GB (32GB recommended for ML workloads)
- Storage: 500GB SSD for applications, 2TB+ HDD for data
- Network: Gigabit Ethernet

**Recommended Configuration:**
- CPU: Intel i7/i9 or AMD Ryzen 7/9 for ML processing
- RAM: 32-64GB for large dataset analysis
- Storage: 1TB NVMe SSD + 4TB+ HDD array
- GPU: NVIDIA GPU for ML acceleration (optional)

### Raspberry Pi Setup

**Hardware:**
- Raspberry Pi 4 Model B (4GB RAM minimum, 8GB recommended)
- 64GB+ microSD card (Class 10 or better)
- Official Raspberry Pi Power Supply
- Ethernet cable for reliable connectivity

**RF Hardware:**
- RTL-SDR Blog V3 dongle
- Wideband antenna (discone or similar)
- USB extension cable for antenna placement
- Optional: GPS module for timing synchronization

### Flipper Zero Configuration

**Required:**
- Flipper Zero with Momentum firmware
- WiFi Developer Board (ESP32-S2)
- 64GB+ microSD card for data storage

**Optional Enhancements:**
- External antenna for improved range
- Protective case for mobile deployment
- Charging dock for automated operation

---

## Software Stack

### Unraid Server Applications

#### Core Infrastructure (Docker Containers)

**Data Storage:**
- **InfluxDB 2.x** - Time-series database for RF data
  - Container: `influxdb:2.7-alpine`
  - Purpose: High-performance storage for time-stamped RF measurements
  - Configuration: 90-day retention policy, automated backups

- **Elasticsearch** - Log analysis and search
  - Container: `elasticsearch:8.8.0`
  - Purpose: Structured log storage and complex queries
  - Configuration: Single-node cluster, 30-day retention

**Message Broker:**
- **Eclipse Mosquitto** - MQTT broker
  - Container: `eclipse-mosquitto:2.0`
  - Purpose: Real-time data streaming between devices
  - Configuration: Authentication enabled, persistent sessions

#### Visualization & Analysis

**Dashboards:**
- **Grafana** - Primary visualization platform
  - Container: `grafana/grafana:10.0.0`
  - Purpose: Real-time dashboards and alerting
  - Plugins: InfluxDB, Elasticsearch, MQTT data sources

- **Kibana** - Log analysis interface
  - Container: `kibana:8.8.0`
  - Purpose: Log search and analysis
  - Configuration: Connected to Elasticsearch

**Data Processing:**
- **Node-RED** - Flow-based programming
  - Container: `nodered/node-red:3.0`
  - Purpose: Data correlation and automation
  - Nodes: InfluxDB, MQTT, HTTP request nodes

#### Machine Learning Platform

**MLflow** - ML lifecycle management
- Container: `mlflow/mlflow:2.5.0`
- Purpose: Experiment tracking and model deployment
- Configuration: PostgreSQL backend, S3-compatible storage

**Jupyter Lab** - Interactive analysis
- Container: `jupyter/scipy-notebook:latest`
- Purpose: Data analysis and model development
- Libraries: scikit-learn, TensorFlow, PyTorch

### Raspberry Pi Software

#### Operating System
**Raspberry Pi OS Lite (64-bit)**
- Minimal installation for better performance
- SSH enabled for remote management
- Automatic updates configured

#### RF Monitoring Tools

**RTL-SDR Software:**
```bash
# Core RTL-SDR tools
sudo apt install rtl-sdr

# rtl_433 for protocol decoding
git clone https://github.com/merbanan/rtl_433.git
cd rtl_433 && mkdir build && cd build
cmake .. && make && sudo make install

# Additional tools
sudo apt install gqrx-sdr dump1090-mutability
```

**Bluetooth Monitoring:**
```bash
# Bluetooth stack
sudo apt install bluetooth bluez bluez-tools

# Python libraries
pip3 install bleak paho-mqtt influxdb-client
```

**System Monitoring:**
```bash
# Prometheus Node Exporter
wget https://github.com/prometheus/node_exporter/releases/download/v1.6.1/node_exporter-1.6.1.linux-armv7.tar.gz
tar xvfz node_exporter-1.6.1.linux-armv7.tar.gz
sudo cp node_exporter-1.6.1.linux-armv7/node_exporter /usr/local/bin/
```

### Flipper Zero Software

#### Firmware
**Momentum Firmware**
- Latest stable release from GitHub
- Extended frequency range unlocked
- Custom applications support enabled

#### WiFi Dev Board
**MicroPython Firmware**
- ESP32-S2 compatible version
- WebREPL enabled for remote access
- Custom libraries for MQTT and HTTP communication

---

## Step-by-Step Implementation

### Phase 1: Network Infrastructure Setup

#### Step 1: UniFi Controller Installation

**On Unraid Server:**
1. Open Community Applications
2. Search for "UniFi-Controller" by LinuxServer.io
3. Configure container settings:
   ```
   Container Name: unifi-controller
   Network Type: Bridge
   Port Mappings:
   - 8080:8080 (Device communication)
   - 8443:8443 (Web interface)
   - 3478:3478/udp (STUN)
   - 10001:10001/udp (Device discovery)
   
   Volume Mappings:
   - /mnt/user/appdata/unifi:/config
   ```
4. Start container and wait for initialization

**Initial Configuration:**
1. Access web interface at `https://server-ip:8443`
2. Complete setup wizard
3. Create admin account for API access
4. Configure site settings and network

#### Step 2: Access Point Deployment

**Physical Installation:**
1. Mount APs at opposite ends of property
2. Run Ethernet cables with PoE+ capability
3. Power on APs and wait for adoption

**UniFi Configuration:**
1. Adopt APs in UniFi Controller
2. Configure WiFi networks and VLANs
3. Enable advanced features:
   - Spectrum analysis
   - Rogue AP detection
   - Client device tracking
   - Band steering and load balancing

**Monitoring Setup:**
1. Settings → System → Logging
2. Enable "Remote Syslog Server"
3. Set server IP to Unraid server
4. Configure log level: "Informational"

#### Step 3: API Access Configuration

**Create API User:**
1. Settings → Admins
2. Add new admin user: `api-monitor`
3. Role: "Super Administrator"
4. Enable "Local Access"
5. Note credentials for later use

**Test API Access:**
```bash
# Test connection
curl -k -X POST https://unifi-controller:8443/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"api-monitor","password":"your-password"}'
```

### Phase 2: Data Infrastructure Setup

#### Step 4: Core Services Installation

**InfluxDB Setup:**
1. Install InfluxDB container from Community Applications
2. Access web UI at `http://server-ip:8086`
3. Complete initial setup:
   - Organization: "RadioMonitoring"
   - Bucket: "rf_data"
   - Retention: 90 days
   - Generate API token

**MQTT Broker Setup:**
1. Install Eclipse Mosquitto container
2. Create configuration file:
   ```
   # /mnt/user/appdata/mosquitto/config/mosquitto.conf
   listener 1883
   allow_anonymous true
   log_type all
   log_dest file /mosquitto/log/mosquitto.log
   persistence true
   persistence_location /mosquitto/data/
   ```
3. Restart container to apply configuration

**Grafana Setup:**
1. Install Grafana container
2. Access web UI at `http://server-ip:3000`
3. Login with admin/admin, change password
4. Add data sources:
   - InfluxDB: `http://influxdb:8086`
   - Elasticsearch: `http://elasticsearch:9200`

#### Step 5: Data Processing Pipeline

**Node-RED Installation:**
1. Install Node-RED container
2. Access editor at `http://server-ip:1880`
3. Install additional nodes:
   ```
   node-red-contrib-influxdb
   node-red-contrib-mqtt-broker
   node-red-dashboard
   ```

**Basic Flow Creation:**
1. Create MQTT input nodes for each data source
2. Add function nodes for data processing
3. Connect InfluxDB output nodes
4. Deploy flows and test data flow

### Phase 3: Raspberry Pi Configuration

#### Step 6: Operating System Setup

**Initial Installation:**
1. Flash Raspberry Pi OS Lite to SD card
2. Enable SSH by creating empty `ssh` file in boot partition
3. Configure WiFi (if needed) in `wpa_supplicant.conf`
4. Boot Pi and connect via SSH

**System Updates:**
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install git python3-pip cmake build-essential
```

#### Step 7: RTL-SDR Configuration

**Hardware Setup:**
1. Connect RTL-SDR dongle to USB port
2. Connect antenna to RTL-SDR
3. Position antenna for optimal reception

**Software Installation:**
```bash
# Install RTL-SDR tools
sudo apt install rtl-sdr

# Blacklist DVB drivers
echo 'blacklist dvb_usb_rtl28xxu' | sudo tee -a /etc/modprobe.d/blacklist-rtl.conf

# Test RTL-SDR
rtl_test

# Install rtl_433
git clone https://github.com/merbanan/rtl_433.git
cd rtl_433 && mkdir build && cd build
cmake .. && make && sudo make install
```

**Configuration Testing:**
```bash
# Test 433MHz reception
rtl_433 -f 433920000 -s 1024000

# Test MQTT output
rtl_433 -F "mqtt://mqtt-server:1883,retain=0,events=radio/rtlsdr"
```

#### Step 8: Bluetooth Monitoring Setup

**Software Installation:**
```bash
sudo apt install bluetooth bluez bluez-tools
pip3 install bleak paho-mqtt influxdb-client
```

**Service Configuration:**
```bash
# Enable Bluetooth service
sudo systemctl enable bluetooth
sudo systemctl start bluetooth

# Test Bluetooth scanning
sudo hcitool lescan
```

#### Step 9: Monitoring Scripts Creation

**RTL-SDR Monitoring Service:**
```bash
# Create systemd service file
sudo nano /etc/systemd/system/rtl433-monitor.service

[Unit]
Description=RTL433 RF Monitor
After=network.target

[Service]
Type=simple
User=pi
ExecStart=/