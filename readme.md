# Temperature Probe

Raspberry Pi DS18B20 digital temperature sensor telemetry pipeline publishing to Google Cloud Pub/Sub.

## Architecture

1. **Hardware:** DS18B20 1-Wire temperature sensor connected to GPIO Pin 7 (BCM 4) on Raspberry Pi.
2. **Edge Daemon:** `picode/26_ds18b20.py` managed by `systemd/temperature-probe.service`.
3. **Telemetry:** Reads sensor with 1-Wire CRC validation and publishes readings every 5 minutes to GCP Cloud Pub/Sub topic `office-temp`.
4. **Cloud Pipeline:** Pub/Sub triggers a Cloud Function (`bigqueryWrite-office-temp`) that streams records into BigQuery dataset `home_monitoring.office_temps`.

## Installation & Deployment

### 1. Requirements on Raspberry Pi
Enable 1-Wire in `/boot/config.txt`:
```bash
dtoverlay=w1-gpio
```

Install Google Cloud Pub/Sub libraries:
```bash
pip install google-cloud-pubsub
```

### 2. Service Account Setup
Place your Google Cloud service account key JSON with Pub/Sub Publisher permissions at:
```bash
/home/pi/Documents/SunFounder_SensorKit_for_RPi2/Python/sunfounder_probe.json
```

### 3. Systemd Service
Copy and enable the systemd service:
```bash
sudo cp systemd/temperature-probe.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now temperature-probe.service
```

Check status and logs:
```bash
sudo systemctl status temperature-probe.service
sudo journalctl -u temperature-probe.service -f
```
