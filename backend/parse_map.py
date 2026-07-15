import json, sys

with open("map_response.json", encoding="utf-8") as f:
    d = json.load(f)

ps = d.get("police_stations", [])
hs = d.get("hotspots", [])

print(f"POLICE STATIONS: {len(ps)}")
for p in ps:
    print(f"  {p['name'][:32]:32s}  lat={p['latitude']}  cases={p['cases']}")

print(f"\nHOTSPOTS (DBSCAN clusters): {len(hs)}")
for h in hs:
    center = h.get("center", {})
    if isinstance(center, dict):
        lat = center.get("latitude", "?")
        lng = center.get("longitude", "?")
    elif isinstance(center, list):
        lat, lng = center[0], center[1]
    else:
        lat = lng = "?"
    print(f"  cluster={h.get('cluster_id')}  lat={lat}  lng={lng}  cases={h['cases']}  district={h.get('district')}")
