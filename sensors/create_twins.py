"""Create one Ditto Thing per library room (+ one for the edge gateway statistics).

Fixed attributes: room name, floor, seating capacity, sensor serial number.
Features start empty - the Node-RED gateway fills them through the REST API.
"""
import sys
import time

import requests

from rooms import DITTO_AUTH, DITTO_URL, NAMESPACE, ROOMS, thing_id

API = f"{DITTO_URL}/api/2/things"


def wait_for_ditto(timeout=600):
    print(f"waiting for Ditto at {DITTO_URL} ...", flush=True)
    end = time.time() + timeout
    while time.time() < end:
        try:
            r = requests.get(API, params={"ids": thing_id("R01")}, auth=DITTO_AUTH, timeout=5)
            if r.status_code == 200:
                print("Ditto is ready", flush=True)
                return
        except requests.RequestException:
            pass
        time.sleep(5)
    sys.exit("Ditto did not become ready in time")


def put_thing(tid, attributes):
    url = f"{API}/{tid}"
    if requests.get(url, auth=DITTO_AUTH, timeout=10).status_code == 404:
        # new Thing; Ditto creates a default policy giving our user (nginx:ditto) full access
        r = requests.put(url, json={"attributes": attributes, "features": {}}, auth=DITTO_AUTH, timeout=10)
        print(f"created {tid}: HTTP {r.status_code}", flush=True)
    else:
        r = requests.put(f"{url}/attributes", json=attributes, auth=DITTO_AUTH, timeout=10)
        print(f"updated attributes of {tid}: HTTP {r.status_code}", flush=True)
    r.raise_for_status()


def main():
    wait_for_ditto()
    for room, info in ROOMS.items():
        put_thing(thing_id(room), {"type": "room", "roomId": room, **info})
    put_thing(f"{NAMESPACE}:gateway", {"type": "gateway", "name": "Node-RED edge gateway"})
    print("all twins ready", flush=True)


if __name__ == "__main__":
    main()
