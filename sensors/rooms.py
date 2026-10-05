"""Shared settings: the three library rooms and the Ditto connection."""
import os

ROOMS = {
    "R01": {"name": "Reading Hall",    "floor": 0, "capacity": 80, "sensorSerial": "LIB-SN-0001"},
    "R02": {"name": "Computer Lab",    "floor": 1, "capacity": 40, "sensorSerial": "LIB-SN-0002"},
    "R03": {"name": "Discussion Room", "floor": 1, "capacity": 12, "sensorSerial": "LIB-SN-0003"},
}

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

DITTO_URL = os.getenv("DITTO_URL", "http://localhost:8080")
DITTO_AUTH = ("ditto", "ditto")          # basic auth handled by nginx
NAMESPACE = "library"


def thing_id(room):
    return f"{NAMESPACE}:{room}"
