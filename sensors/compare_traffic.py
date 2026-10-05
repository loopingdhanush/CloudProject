"""Compare raw sensor messages vs messages forwarded by the edge gateway.

Listens on the broker for SECONDS (default 60) and counts:
  raw       : library/+/telemetry   (what the sensors send)
  forwarded : library/+/summary + library/alerts   (what the gateway sends on)
Also prints the gateway's own counters stored in the Ditto twin  library:gateway.
"""
import sys
import time

import paho.mqtt.client as mqtt
import requests

from rooms import DITTO_AUTH, DITTO_URL, MQTT_HOST, MQTT_PORT

counts = {"raw": 0, "summary": 0, "alert": 0}


def on_message(client, userdata, msg):
    if msg.topic.endswith("/telemetry"):
        counts["raw"] += 1
    elif msg.topic.endswith("/summary"):
        counts["summary"] += 1
    elif msg.topic == "library/alerts":
        counts["alert"] += 1


def main():
    seconds = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    c.on_message = on_message
    c.connect(MQTT_HOST, MQTT_PORT)
    c.subscribe([("library/+/telemetry", 0), ("library/+/summary", 0), ("library/alerts", 0)])
    c.loop_start()
    print(f"listening for {seconds} s ...")
    time.sleep(seconds)
    c.loop_stop()

    fwd = counts["summary"] + counts["alert"]
    raw = counts["raw"] or 1
    print(f"\nraw messages received from sensors : {counts['raw']}")
    print(f"messages forwarded by the gateway  : {fwd}  (summaries {counts['summary']}, alerts {counts['alert']})")
    print(f"data reduction at the edge         : {100 * (1 - fwd / raw):.1f} %")

    try:
        t = requests.get(f"{DITTO_URL}/api/2/things/library:gateway/features/stats/properties",
                         auth=DITTO_AUTH, timeout=5).json()
        print(f"\ngateway counters since start (from Ditto twin library:gateway): {t}")
    except Exception as e:  # noqa: BLE001 - informative only
        print(f"(could not read gateway twin: {e})")


if __name__ == "__main__":
    main()
