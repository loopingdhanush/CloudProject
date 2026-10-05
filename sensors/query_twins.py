"""Read the room twins back from Ditto (GET by id + search)."""
import json

import requests

from rooms import DITTO_AUTH, DITTO_URL, ROOMS, thing_id


def main():
    print("=== GET each room twin ===")
    for room in ROOMS:
        r = requests.get(f"{DITTO_URL}/api/2/things/{thing_id(room)}", auth=DITTO_AUTH, timeout=10)
        t = r.json()
        f = t.get("features", {})
        p = lambda feat, key: f.get(feat, {}).get("properties", {}).get(key, "-")
        print(f"{room} {t['attributes']['name']:<16} status={p('status', 'value'):<8} "
              f"occupancy={p('occupancy', 'average')}/{t['attributes']['capacity']} "
              f"({p('occupancy', 'percent')}%) temp={p('environment', 'temperature')}C "
              f"hum={p('environment', 'humidity')}% faults={p('equipment', 'faults')} "
              f"seats={p('SeatAvailability', 'value')}")

    print("\n=== SEARCH: rooms that are not NORMAL ===")
    r = requests.get(f"{DITTO_URL}/api/2/search/things", auth=DITTO_AUTH, timeout=10, params={
        "filter": 'and(eq(attributes/type,"room"),ne(features/status/properties/value,"NORMAL"))',
        "fields": "thingId,features/status/properties"})
    print(json.dumps(r.json().get("items", []), indent=2))


if __name__ == "__main__":
    main()
