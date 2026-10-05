"""Library sensor simulator.

Publishes one reading per room every INTERVAL seconds to  library/<room>/telemetry
  * R01, R03 (vendor A): Celsius, equipment as text  ON / OFF / FAULT
  * R02      (vendor B): Fahrenheit, equipment as codes 0=OFF 1=ON 2=FAULT
A few readings are deliberately broken (INVALID_RATE) so the gateway has something to clean.

Each room follows a repeating 240-step scenario so the demo shows every state:
  R01 Reading Hall    : normal -> too warm (WARNING) -> normal -> hot AND humid (CRITICAL)
  R02 Computer Lab    : normal -> busy 80-90 % (WARNING) -> a computer FAULT (CRITICAL)
  R03 Discussion Room : people keep coming in -> trend LIMITED -> over capacity (CRITICAL)
"""
import json
import os
import random
import time

import paho.mqtt.client as mqtt

from rooms import MQTT_HOST, MQTT_PORT, ROOMS

INTERVAL = float(os.getenv("INTERVAL", "1"))
INVALID_RATE = float(os.getenv("INVALID_RATE", "0.08"))
CYCLE = 240
START = {"R01": 90, "R02": 50, "R03": 60}      # offsets so rooms change at different times


def noise(spread):
    return random.uniform(-spread, spread)


def reading(room, step):
    s = (step + START[room]) % CYCLE
    devices = {"lights": "ON", "ac": "ON", "computers": "ON", "printer": "ON"}
    temp, hum = 23 + noise(1), 50 + noise(4)

    if room == "R01":
        occ = 42 + random.randint(-6, 6)
        if 100 <= s < 160:                       # too warm -> WARNING
            temp = 27.5 + noise(0.5)
        elif 200 <= s < 240:                     # hot + humid -> CRITICAL
            temp, hum = 31 + noise(0.5), 72 + noise(2)
    elif room == "R02":
        occ = 22 + random.randint(-4, 4)
        if 60 <= s < 100:                        # busy -> WARNING
            occ = 34 + random.randint(-1, 1)
        if 140 <= s < 190:                       # a computer breaks -> CRITICAL
            devices["computers"] = "FAULT"
    else:  # R03 - steadily filling up, then empties again
        occ = 3 + int(13 * s / CYCLE)

    msg = {"room": room, "sensor": ROOMS[room]["sensorSerial"], "occupancy": occ,
           "humidity": round(hum, 1), "ts": int(time.time() * 1000)}

    if room == "R02":                            # vendor B: Fahrenheit + numeric codes
        msg["temperature_f"] = round(temp * 9 / 5 + 32, 1)
        code = {"OFF": 0, "ON": 1, "FAULT": 2}
        msg["equipment"] = {k: code[v] for k, v in devices.items()}
    else:
        msg["temperature"] = round(temp, 1)
        msg["equipment"] = devices
    return msg


def break_it(msg):
    """Return a deliberately invalid payload (string)."""
    kind = random.choice(["negative", "hot", "humid", "missing", "text", "json"])
    if kind == "negative":
        msg["occupancy"] = -5
    elif kind == "hot":
        if "temperature" in msg:
            msg["temperature"] = 70
        else:
            msg["temperature_f"] = 158
    elif kind == "humid":
        msg["humidity"] = 140
    elif kind == "missing":
        msg.pop("occupancy")
    elif kind == "text":
        msg["humidity"] = "abc"
    else:
        return json.dumps(msg)[:25]              # broken JSON
    return json.dumps(msg)


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="library-simulator")
    while True:
        try:
            client.connect(MQTT_HOST, MQTT_PORT)
            break
        except OSError:
            print("waiting for MQTT broker ...", flush=True)
            time.sleep(2)
    client.loop_start()
    print(f"simulator started: {len(ROOMS)} rooms, every {INTERVAL}s, invalid rate {INVALID_RATE}", flush=True)

    step, sent, bad = 0, 0, 0
    while True:
        for room in ROOMS:
            msg = reading(room, step)
            if random.random() < INVALID_RATE:
                payload, bad = break_it(msg), bad + 1
            else:
                payload = json.dumps(msg)
            client.publish(f"library/{room}/telemetry", payload)
            sent += 1
        step += 1
        if step % 30 == 0:
            print(f"published {sent} readings ({bad} invalid on purpose)", flush=True)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
