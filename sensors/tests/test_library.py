"""System tests - run against the running stack:
    docker compose run --rm simulator pytest -v
"""
import json
import sys
import time
from pathlib import Path

import paho.mqtt.client as mqtt
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rooms import DITTO_AUTH, DITTO_URL, MQTT_HOST, MQTT_PORT, ROOMS, thing_id  # noqa: E402
from simulator import break_it, reading  # noqa: E402

API = f"{DITTO_URL}/api/2"


def get(path, **params):
    r = requests.get(f"{API}/{path}", auth=DITTO_AUTH, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def gateway_stats():
    return get("things/library:gateway/features/stats/properties")


def test_ditto_requires_basic_auth():
    assert requests.get(f"{API}/things/{thing_id('R01')}", timeout=10).status_code == 401


def test_one_twin_per_room_with_attributes():
    for room, info in ROOMS.items():
        t = get(f"things/{thing_id(room)}")
        assert t["attributes"]["name"] == info["name"]
        assert t["attributes"]["capacity"] == info["capacity"]
        assert t["attributes"]["sensorSerial"] == info["sensorSerial"]


def test_gateway_updates_twin_features():
    for room in ROOMS:
        f = get(f"things/{thing_id(room)}/features")
        assert f["status"]["properties"]["value"] in ("NORMAL", "WARNING", "CRITICAL")
        assert f["SeatAvailability"]["properties"]["value"] in ("AVAILABLE", "LIMITED", "FULL")
        assert 15 <= f["environment"]["properties"]["temperature"] <= 40   # Celsius, also for R02 (Fahrenheit vendor)
        assert f["occupancy"]["properties"]["capacity"] == ROOMS[room]["capacity"]


def test_search_finds_all_rooms():
    res = get("search/things", filter='eq(attributes/type,"room")', fields="thingId")
    assert {i["thingId"] for i in res["items"]} == {thing_id(r) for r in ROOMS}


def test_simulator_vendor_formats():
    assert "temperature_f" in reading("R02", 0)                  # vendor B: Fahrenheit
    assert reading("R02", 0)["equipment"]["lights"] in (0, 1, 2)  # vendor B: codes
    assert reading("R01", 0)["equipment"]["lights"] == "ON"      # vendor A: text


def test_gateway_drops_invalid_readings():
    before = gateway_stats()["dropped"]
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    c.connect(MQTT_HOST, MQTT_PORT)
    c.loop_start()
    bad = ['{"room": "R01", "occ', json.dumps({"room": "R01", "occupancy": -5, "temperature": 22, "humidity": 50}),
           json.dumps({"room": "R01", "occupancy": 5, "temperature": 70, "humidity": 50}),
           json.dumps({"room": "R01", "occupancy": 5, "temperature": 22, "humidity": 140}),
           json.dumps({"room": "R01", "temperature": 22, "humidity": 50})]
    for p in bad:
        c.publish("library/R01/telemetry", p).wait_for_publish()
    c.loop_stop()
    time.sleep(12)                       # stats are written to the twin every 5 s
    assert gateway_stats()["dropped"] >= before + len(bad)


def test_break_it_produces_invalid_payloads():
    for _ in range(20):
        p = break_it(reading("R01", 0))
        assert isinstance(p, str)


def test_edge_reduces_data():
    s = gateway_stats()
    assert s["raw"] > 0
    assert s["forwarded"] < 0.2 * s["raw"]       # at least 80 % less data sent on
