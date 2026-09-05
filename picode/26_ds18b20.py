#!/usr/bin/env python
from __future__ import print_function
import os
import sys
import glob
import time
import json
from datetime import datetime
from google.auth import jwt
from google.cloud import pubsub_v1

PROJECT_ID = "thetechrambler-177118"
TOPIC_ID = "office-temp"
KEY_PATH = "/home/pi/Documents/SunFounder_SensorKit_for_RPi2/Python/sunfounder_probe.json"
INTERVAL_SECONDS = 300  # 5 minutes

ds18b20 = ""

def find_sensor():
    """Locate the 1-Wire DS18B20 sensor address."""
    global ds18b20
    devices = glob.glob("/sys/bus/w1/devices/28-*")
    if devices:
        ds18b20 = os.path.basename(devices[0])
    else:
        # Fallback to known hardware ID
        ds18b20 = "28-00000a691f27"
    print("[{}] Detected sensor: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ds18b20))

def read_sensor(max_retries=3):
    """Read temperature in Celsius from 1-Wire slave with CRC validation."""
    location = "/sys/bus/w1/devices/" + ds18b20 + "/w1_slave"
    for attempt in range(max_retries):
        try:
            with open(location, "r") as f:
                lines = f.readlines()
            if len(lines) >= 2 and lines[0].strip().endswith("YES"):
                pos = lines[1].find("t=")
                if pos != -1:
                    raw_temp = lines[1][pos + 2:].strip()
                    return float(raw_temp) / 1000.0
        except Exception as e:
            print("[{}] Sensor read attempt {} failed: {}".format(
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"), attempt + 1, e
            ))
        time.sleep(0.5)
    return None

def init_publisher():
    """Initialize GCP Pub/Sub publisher client."""
    if not os.path.exists(KEY_PATH):
        raise RuntimeError("Service account key not found at: " + KEY_PATH)
    
    with open(KEY_PATH, "r") as f:
        service_account_info = json.load(f)
    
    audience = "https://pubsub.googleapis.com/google.pubsub.v1.Publisher"
    credentials = jwt.Credentials.from_service_account_info(
        service_account_info, audience=audience
    )
    publisher = pubsub_v1.PublisherClient(credentials=credentials)
    topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)
    return publisher, topic_path

def publish_reading(publisher, topic_path, temperature):
    """Publish temperature reading to Pub/Sub matching original schema."""
    now = datetime.now()
    dt_string = now.strftime("%Y-%m-%d %H:%M:%S")

    # Match original message payload format: "{temp}:{dt_string}"
    payload = u"{}:{}".format(temperature, dt_string)
    data = payload.encode("utf-8")

    future = publisher.publish(
        topic_path,
        data,
        origin="Barrys office",
        username="gcp"
    )
    message_id = future.result(timeout=15)
    print("[{}] Temperature: {:0.3f} C | Published Message ID: {}".format(
        dt_string, temperature, message_id
    ))
    sys.stdout.flush()

def main():
    find_sensor()
    print("[{}] Initializing Pub/Sub publisher...".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    publisher, topic_path = init_publisher()
    print("[{}] Publishing to: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), topic_path))
    sys.stdout.flush()

    while True:
        try:
            temp = read_sensor()
            if temp is not None:
                publish_reading(publisher, topic_path, temp)
            else:
                print("[{}] Warning: Failed to obtain valid temperature from sensor.".format(
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))
                sys.stdout.flush()
        except Exception as e:
            print("[{}] Error publishing reading: {}".format(
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"), e
            ))
            sys.stdout.flush()

        time.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting on KeyboardInterrupt.")
