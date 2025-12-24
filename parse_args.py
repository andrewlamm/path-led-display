import argparse
from get_train_data import STATIONS

stations_string = ", ".join(STATIONS.keys())

def parse_args():
  parser = argparse.ArgumentParser()

  parser.add_argument(
    "station",
    choices=STATIONS.keys(),
    help=f"Station to display. Must be one of: {stations_string}"
  )

  parser.add_argument(
    "--ny",
    action="store_true",
    help="Display trains going towards NY"
  )

  parser.add_argument(
    "--nj",
    action="store_true",
    help="Display trains going towards NJ"
  )

  # parser.add_argument(
  #   "r",
  #   type=int,
  #   help="red"
  # )

  # parser.add_argument(
  #   "g",
  #   type=int,
  #   help="green"
  # )

  # parser.add_argument(
  #   "b",
  #   type=int,
  #   help="blue"
  # )

  args = parser.parse_args()

  if not args.ny and not args.nj:
    parser.error("You must provide at least one of --ny or --nj")

  return args

