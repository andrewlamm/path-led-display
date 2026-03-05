#!/usr/bin/env python3
from get_train_data import get_data
from parse_args import parse_args
from dateutil.parser import isoparse
import datetime
import time
import threading
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
import math
import random
import re

args = parse_args()

STATION_TO_DISPLAY = args.station
DIRECTIONS_TO_DISPLAY = []
if args.ny:
  DIRECTIONS_TO_DISPLAY.append("ToNY")
if args.nj:
  DIRECTIONS_TO_DISPLAY.append("ToNJ")

MATRIX_COLS = 64
MATRIX_ROWS = 32
MATRIX_CHAIN_LENGTH = 3
DISPLAY_LENGTH = MATRIX_COLS * MATRIX_CHAIN_LENGTH
MATRIX_BRIGHTNESS = 50

ROWS_PER_TRAIN = 16
TRAINS_TO_DISPLAY = MATRIX_ROWS // ROWS_PER_TRAIN

REDRAW_LOOP_SECONDS = 0.01

ARRIVAL_FLICKER_SECONDS = 1
DELAY_FLICKER_SECONDS = 1
DISPLAY_TRAIN_SECONDS = 3
ALERT_COOLDOWN = 60
ALERT_MIN_X_VALUE = -20

STALE_SECONDS = 600

ALERT_SCROLL_SPEED = 1.5

HEADSIGN_TO_TEXT = {
  'World Trade Center': 'World Trade Center',
  'Newark': 'Newark',
  'Journal Square': 'Journal Square',
  '33rd Street': '33rd Street',
  'Hoboken': 'Hoboken',
  '33rd Street via Hoboken': '33rd Street via HOB',
  'Journal Square via Hoboken': 'Journal Sq via HOB',
}

HEADSIGN_TO_TEXT = {
  'World Trade Center': 'World Trade Center',
  'Newark': 'Newark',
  'Journal Square': 'Journal Square',
  '33rd Street': '33rd Street',
  'Hoboken': 'Hoboken',
  '33rd Street via Hoboken': '33rd Street via HOB',
  'Journal Square via Hoboken': 'Journal Sq via HOB',
}

EDITED_COLOR_MAPPING = {
  '#D93A30': graphics.Color(184, 6, 17),
  '#4D92FB': graphics.Color(77, 146, 251),
  '#FF9900': graphics.Color(255, 153, 0),
  '#65C100': graphics.Color(101, 193, 0),
}

DIRECTION_TO_TEXT = {
  "ToNY": "<",
  "ToNJ": ">",
}

ARRIVAL_THRESHOLD_SECONDS = 15

FONT_FILE = "mta-font.bdf"

ARRIVAL_FLICKER_CYCLE = int(ARRIVAL_FLICKER_SECONDS / REDRAW_LOOP_SECONDS)
ARRIVAL_FLICKER_TOTAL_CYCLES = int(ARRIVAL_FLICKER_CYCLE * 2)

DELAY_FLICKER_CYCLE = int(DELAY_FLICKER_SECONDS / REDRAW_LOOP_SECONDS)
DELAY_FLICKER_TOTAL_CYCLES = int(DELAY_FLICKER_CYCLE * 2)

ALERT_COOLDOWN_CYCLES = int(ALERT_COOLDOWN / REDRAW_LOOP_SECONDS)

TEXT_HEIGHT = 12

RIGHT_X_PADDING = 1
LEFT_X_PADDING = 1

TEXT_BASELINE_Y = (ROWS_PER_TRAIN - TEXT_HEIGHT) // 2 + TEXT_HEIGHT

GREEN_TEXT_COLOR = graphics.Color(115, 145, 7)
GRAY_TEXT_COLOR = graphics.Color(110, 110, 110)
ORANGE_TEXT_COLOR = graphics.Color(222, 86, 7)
DELAY_TEXT_COLOR = graphics.Color(255, 0, 0)
DELAY_STRING = "Delay"

MAX_DISPLAY_TRAINS = 4 if len(DIRECTIONS_TO_DISPLAY) == 1 else 6
DISPLAY_TRAIN_CYCLE = int(DISPLAY_TRAIN_SECONDS / REDRAW_LOOP_SECONDS)
DISPLAY_TRAIN_TOTAL_CYCLES = int(DISPLAY_TRAIN_CYCLE * (MAX_DISPLAY_TRAINS - 1))

display_trains = []
display_alerts = []

def update_display_trains(estimated_trains):
  global display_trains

  train_data = estimated_trains[STATION_TO_DISPLAY]
  arrivals = []

  for direction in train_data["destinations"]:
    if direction["label"] in DIRECTIONS_TO_DISPLAY:
      for train in direction["messages"]:
         train["direction"] = direction["label"]
         arrivals.append(train)

  for train in arrivals:
    last_updated = isoparse(train["lastUpdated"])
    estimated_arrival = last_updated.timestamp() + int(train["secondsToArrival"])
    estimated_arrival_seconds = int(estimated_arrival - time.time())
    train["estimatedArrivalSeconds"] = estimated_arrival_seconds

  arrivals.sort(key=lambda m: int(m["estimatedArrivalSeconds"]))

  display_trains = arrivals

def update_display_alerts(alerts_data):
  global display_alerts

  def remove_timestamp(s):
    return re.sub(r'^\s*\d{1,2}(?::\d{2})?\s*(AM|PM)\s*:\s*', '', s, flags=re.IGNORECASE)

  def form_variables_contains_name(alert_message, name):
    if "formVariableItems" not in alert_message:
      return False

    for variable in alert_message["formVariableItems"]:
      if "variableName" in variable and name in variable["variableName"]:
        return True
    return False

  alerts_data = alerts_data["data"]

  display_alerts = []
  for alert in alerts_data:
    alert_message = alert["incidentMessage"]
    if "Elevator" in alert_message["subject"]:
      pass
    elif "Bridge & Tunnel Alert" in alert_message["subject"]:
      pass
    elif "Newark Airport Info-Alert" in alert_message["subject"]:
      pass
    elif "MBT Carrier Alert" in alert_message["subject"]:
      pass
    elif form_variables_contains_name(alert_message, "PABT General Incident"):
      pass
    else:
      message = remove_timestamp(alert_message["preMessage"]).replace('PATHAlert:', '').replace('@', 'at').replace('&', 'and').strip()
      display_alerts.append(message)

  if len(display_alerts) == 0:
    if random.random() < 0.01:
      display_alerts = ["Have a great day!"]


def update_data():
  train_data, alerts_data = get_data()
  if train_data is not None:
    update_display_trains(train_data)
  if alerts_data is not None:
    update_display_alerts(alerts_data)

def all_trains_stale():
  for train in display_trains:
    if isoparse(train["lastUpdated"]).timestamp() > (datetime.datetime.now() - datetime.timedelta(seconds=STALE_SECONDS)).timestamp():
      return False
  return True

def remove_stale_trains():
  global display_trains

  display_trains = [train for train in display_trains if isoparse(train["lastUpdated"]).timestamp() > (datetime.datetime.now() - datetime.timedelta(seconds=STALE_SECONDS)).timestamp()]

def update_loop():
  while True:
    update_data()
    remove_stale_trains()
    print(display_trains)
    print(display_alerts)
    time.sleep(5)

thread = threading.Thread(target=update_loop, daemon=True)
thread.start()

options = RGBMatrixOptions()

options.rows = MATRIX_ROWS
options.cols = MATRIX_COLS
options.chain_length = MATRIX_CHAIN_LENGTH
options.parallel = 1
options.hardware_mapping = 'adafruit-hat'
options.brightness = MATRIX_BRIGHTNESS

matrix = RGBMatrix(options=options)

font = graphics.Font()
font.LoadFont(FONT_FILE)

canvas = matrix.CreateFrameCanvas()

def calc_length(s):
  length = 0
  for char in s:
    length += font.CharacterWidth(ord(char))
  return length

delay_length = calc_length(DELAY_STRING)

def hex_to_color(hex_str):
  hex_str = hex_str.lstrip('#')
  r = int(hex_str[0:2], 16)
  g = int(hex_str[2:4], 16)
  b = int(hex_str[4:6], 16)
  return graphics.Color(r, g, b)

def format_seconds(seconds):
  if seconds < ARRIVAL_THRESHOLD_SECONDS:
    return '0m'
  minutes = seconds // 60
  remaining_seconds = seconds % 60
  if remaining_seconds < 30 and minutes != 0:
    return f'{minutes}m'
  else:
    return f'{minutes + 1}m'

def draw_filled_circle(canvas, cx, cy, radius, color):
  geom_r = radius - 0.5
  geom_r2 = geom_r * geom_r

  for dy in range(-(radius - 1), (radius - 1) + 1):
    # Horizontal span using the geometric radius
    # dx^2 + dy^2 <= geom_r^2
    span = int(math.floor(math.sqrt(geom_r2 - dy * dy)))
    x_start = cx - span
    x_end = cx + span

    for x in range(x_start, x_end + 1):
      canvas.SetPixel(x, cy + dy, color.red, color.green, color.blue)


def draw_line_circle(colors, x, y):
  circle_offset = ROWS_PER_TRAIN - 2
  if len(colors) == 1:
    graphics.DrawText(canvas, font, x, y + circle_offset, colors[0], "_")
  elif len(colors) == 2:
    graphics.DrawText(canvas, font, x, y - 2 + circle_offset, colors[1], "`")
    graphics.DrawText(canvas, font, x + 2, y + circle_offset, colors[0], "`")
  # center_x = x + 8
  # center_y = y + (ROWS_PER_TRAIN // 2)
  # if len(colors) == 1:
  #   draw_filled_circle(canvas, center_x, center_y, 6, colors[0])
  # elif len(colors) == 2:
  #   draw_filled_circle(canvas, center_x - 1, center_y - 1, 5, colors[1])
  #   draw_filled_circle(canvas, center_x + 1, center_y + 1, 5, colors[0])

def draw_loop():
  global canvas

  arrival_flicker_count = 0
  delay_flicker_count = 0
  display_train_count = 0

  alert_to_display = None
  alert_length = None
  alert_x = None
  alert_cooldown_count = ALERT_COOLDOWN_CYCLES

  previous_cycle_had_arrival = False

  while True:
    arrival_flicker_count = (arrival_flicker_count + 1) % ARRIVAL_FLICKER_TOTAL_CYCLES
    delay_flicker_count = (delay_flicker_count + 1) % DELAY_FLICKER_TOTAL_CYCLES

    canvas.Clear()
    y = 0

    if len(display_trains) == 0:
      graphics.DrawText(canvas, font, LEFT_X_PADDING, y + TEXT_BASELINE_Y, GRAY_TEXT_COLOR, "No trains currently available.")
    elif all_trains_stale():
      graphics.DrawText(canvas, font, LEFT_X_PADDING, y + TEXT_BASELINE_Y, DELAY_TEXT_COLOR, "All train data is stale!")
    else:
      trains_to_display = TRAINS_TO_DISPLAY

      # Reset delay counter if we just started displaying a new train
      if arrival_flicker_count % DISPLAY_TRAIN_CYCLE == 0:
        delay_flicker_count = 0

      # Always display the next train along with any arrived trains
      locked_trains_amount = 1
      for trains in display_trains[1:]:
        if int(trains["estimatedArrivalSeconds"]) < ARRIVAL_THRESHOLD_SECONDS:
          locked_trains_amount += 1

      if alert_x is not None:
        if alert_x + alert_length < ALERT_MIN_X_VALUE:
          # Alert has scrolled off screen
          alert_cooldown_count = 0
          alert_to_display = None
          alert_length = None
          alert_x = None
        else:
          # Scroll alert left and display alert at the last train slot
          alert_x -= ALERT_SCROLL_SPEED
          trains_to_display -= 1

      if alert_x is None:
        alert_cooldown_count += 1
        if len(display_alerts) > 0 and alert_cooldown_count >= ALERT_COOLDOWN_CYCLES and locked_trains_amount < TRAINS_TO_DISPLAY:
          # very hacky way to not show "1 active incident: Have a great day!"
          if len(display_alerts) == 1 and display_alerts[0] == "Have a great day!":
            alert_to_display = "Have a great day!"
          else:
            # Start displaying a new alert since we have space for one and cooldown has passed
            # Note if a new train has arrived, alert will finish displaying first
            if len(display_alerts) == 1:
              alert_to_display = "1 active incident: "
            else:
              alert_to_display = f"{len(display_alerts)} active incidents: "

            alert_to_display += " ".join([f"Incident {i + 1}: {msg}" for i, msg in enumerate(display_alerts)])

          alert_length = calc_length(alert_to_display)
          alert_x = DISPLAY_LENGTH

      # Only increase train cycle clock if we are not displaying an alert
      if alert_to_display is None:
        display_train_count = (display_train_count + 1) % DISPLAY_TRAIN_TOTAL_CYCLES

      # Reset train cycle clock if screen is full of arrived trains
      if locked_trains_amount == TRAINS_TO_DISPLAY:
        display_train_count = 0

      has_train_arrival = False
      for trains in display_trains:
        if int(trains["estimatedArrivalSeconds"]) < ARRIVAL_THRESHOLD_SECONDS:
          has_train_arrival = True
          break

      if has_train_arrival and not previous_cycle_had_arrival:
        arrival_flicker_count = 0
      previous_cycle_had_arrival = has_train_arrival

      for iter_idx in range(trains_to_display):
        train_idx = None
        if iter_idx < locked_trains_amount:
          train_idx = iter_idx
        else:
          offset = int(display_train_count // DISPLAY_TRAIN_CYCLE)
          train_idx = iter_idx + (offset * (TRAINS_TO_DISPLAY - locked_trains_amount))

        if train_idx >= len(display_trains):
          display_train_count = 0
          train_idx = iter_idx

        train = display_trains[train_idx] if train_idx < len(display_trains) else None

        if train is None:
          break

        seconds_to_arrival = int(train["estimatedArrivalSeconds"])

        text_color = ORANGE_TEXT_COLOR if seconds_to_arrival < ARRIVAL_THRESHOLD_SECONDS else GREEN_TEXT_COLOR

        is_delayed = train["arrivalTimeMessage"] == 'Delayed'

        # Show direction arrow if multiple directions are displayed
        direction_padding = 0
        if len(DIRECTIONS_TO_DISPLAY) > 1:
          direction_padding = 10
          graphics.DrawText(canvas, font, LEFT_X_PADDING, y + TEXT_BASELINE_Y, text_color, DIRECTION_TO_TEXT.get(train["direction"], ""))

        # Draw # train
        graphics.DrawText(canvas, font, LEFT_X_PADDING + direction_padding, y + TEXT_BASELINE_Y, text_color, f"{train_idx + 1}.")

        # Draw circles
        line_colors = []
        for color in train["lineColor"].split(","):
          color = "#" + color
          if color in EDITED_COLOR_MAPPING:
            line_colors.append(EDITED_COLOR_MAPPING[color])
          else:
            line_colors.append(hex_to_color(color))
        draw_line_circle(line_colors, 12 + direction_padding, y)

        # Draw headsign text
        headsign_text = HEADSIGN_TO_TEXT.get(train["headSign"], train["headSign"])
        graphics.DrawText(canvas, font, LEFT_X_PADDING + direction_padding + 30, y + TEXT_BASELINE_Y, text_color, headsign_text)

        display_time_color = ORANGE_TEXT_COLOR if seconds_to_arrival < ARRIVAL_THRESHOLD_SECONDS else GRAY_TEXT_COLOR if train.get("estimated") is not None else GREEN_TEXT_COLOR
        arrival_str = format_seconds(seconds_to_arrival)
        arrival_length = calc_length(arrival_str)

        if seconds_to_arrival < ARRIVAL_THRESHOLD_SECONDS:
          # Only draw arrival time for arrived trains if within flicker threshold
          if arrival_flicker_count < ARRIVAL_FLICKER_CYCLE:
            graphics.DrawText(canvas, font, (options.cols * options.chain_length) - RIGHT_X_PADDING - arrival_length, y + TEXT_BASELINE_Y, display_time_color, arrival_str)
        else:
          # Check if we display delayed or not
          if not is_delayed or (delay_flicker_count < DELAY_FLICKER_CYCLE):
            graphics.DrawText(canvas, font, (options.cols * options.chain_length) - RIGHT_X_PADDING - arrival_length, y + TEXT_BASELINE_Y, display_time_color, arrival_str)
          else:
            graphics.DrawText(canvas, font, (options.cols * options.chain_length) - RIGHT_X_PADDING - delay_length, y + TEXT_BASELINE_Y, DELAY_TEXT_COLOR, DELAY_STRING)

        y += ROWS_PER_TRAIN

      if alert_to_display is not None:
        graphics.DrawText(canvas, font, alert_x, y + TEXT_BASELINE_Y, ORANGE_TEXT_COLOR, alert_to_display)

    canvas = matrix.SwapOnVSync(canvas)
    time.sleep(REDRAW_LOOP_SECONDS)

try:
  while True:
    draw_loop()

except KeyboardInterrupt:
  matrix.Clear()
  print("\nMatrix cleared. Exiting program.")

