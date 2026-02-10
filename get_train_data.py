import requests
from dateutil.parser import isoparse
from station_deltas import STATION_DELTAS
import time

TRAIN_DATA = 'https://www.panynj.gov/bin/portauthority/ridepath.json'
ALERTS_DATA = 'https://www.panynj.gov/bin/portauthority/everbridge/incidents?status=All&department=Path'

STATIONS = {
  'NWK': {'name': 'Newark', 'direction': 2},
  'HAR': {'name': 'Harrison', 'direction': 0},
  'JSQ': {'name': 'Journal Square', 'direction': 0},
  'GRV': {'name': 'Grove Street', 'direction': 0},
  'NEW': {'name': 'Newport', 'direction': 0},
  'EXP': {'name': 'Exchange Place', 'direction': 0},
  'HOB': {'name': 'Hoboken', 'direction': 0},
  'WTC': {'name': 'World Trade Center', 'direction': 1},
  'CHR': {'name': 'Christopher Street', 'direction': 0},
  '09S': {'name': '9th Street', 'direction': 0},
  '14S': {'name': '14th Street', 'direction': 0},
  '23S': {'name': '23rd Street', 'direction': 0},
  '33S': {'name': '33rd Street', 'direction': 1},
}

def get_estimate_buffer(curr_arrival):
  if curr_arrival >= 1200:
    # If train is more than 20m away, buffer of 5m
    return 120
  # Otherwise if more than 15m away, buffer of 3m
  if curr_arrival >= 900:
    return 90
  # Otherwise buffer of 2m
  return 120

def get_trains():
  resp = requests.get(TRAIN_DATA)
  return resp.json()

def get_alerts():
  resp = requests.get(ALERTS_DATA)
  return resp.json()

def estimate_trains(response):
  response_stations = {}

  for station in response["results"]:
    response_stations[station["consideredStation"]] = station

  for station_short_name in STATIONS:
    station = response_stations.get(station_short_name)
    if station is None:
      continue

    for  destination in station["destinations"]:
      direction_label = destination["label"]

      for train in destination["messages"]:
        target = (
            f"{train['target']}/HOB"
            if "via Hoboken" in train["headSign"]
            else train["target"]
        )

        updated = isoparse(train["lastUpdated"])
        curr_estimated = int(train["secondsToArrival"])

        next_stations = STATION_DELTAS[station_short_name].get(target)
        if next_stations is None:
          print(f"No next stations for {station_short_name} to {target}")
          continue

        for next_station, delta in next_stations.items():
          if next_station == target:
            continue
          if next_station not in response_stations:
            continue

          estimated_arrival = updated.timestamp() + delta + curr_estimated

          found = False

          for dest in response_stations[next_station]["destinations"]:
            for msg in dest["messages"]:
              msg_target = (
                f"{msg['target']}/HOB"
                if "via Hoboken" in msg["headSign"]
                else msg["target"]
              )

              if msg_target != target:
                continue

              msg_arrival = isoparse(msg["lastUpdated"]).timestamp() + int(msg["secondsToArrival"])

              estimate_buffer = get_estimate_buffer(int(msg["secondsToArrival"]))
              if abs(msg_arrival - estimated_arrival) <= estimate_buffer and ("stationsEstimatedFrom" not in msg or station_short_name not in msg["stationsEstimatedFrom"]):
                if msg.get("estimated") and msg["estimated"] > delta:
                  if "stationsEstimatedFrom" not in msg:
                    msg["stationsEstimatedFrom"] = []
                  msg["stationsEstimatedFrom"].append(station_short_name)

                  msg["estimated"] = delta
                  msg["estimatedStation"] = STATIONS[station_short_name]["name"]
                  msg["secondsToArrival"] = curr_estimated + delta
                found = True
                break

            if found:
              break

          # If no match found, add an estimated train message
          if not found:
            for dest in response_stations[next_station]["destinations"]:
              if dest["label"] == direction_label:
                new_msg = dict(train)
                new_msg.update({
                  "secondsToArrival": curr_estimated + delta,
                  "lastUpdated": updated.isoformat(),
                  "arrivalTimeMessage": f"Est from {STATIONS[station_short_name]['name']}",
                  "target": train["target"],
                  "lineColor": train["lineColor"],
                  "stationsEstimatedFrom": [station_short_name],
                  "estimatedStation": STATIONS[station_short_name]["name"],
                  "estimated": delta,
                })
                dest["messages"].append(new_msg)

  return response_stations

def get_data():
  try:
    train_data = get_trains()
    alerts_data = get_alerts()
    estimated_trains = estimate_trains(train_data)

    return (estimated_trains, alerts_data)
  except Exception as e:
    print(f"Error fetching data: {e}")
    return (None, None)

