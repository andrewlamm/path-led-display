# PATH LED Display

Python code that displays upcoming PATH train arrivals and alerts on LED matrix display. 

Run `sudo python3 led-display.py station [--ny] [--nj]` where `station` is the station to display arrivals for. Use `--ny` to show trains in the New York direction and `--nj` to show trains in the New Jersey direction. If both are provided, an arrow indicating direction will be shown next to each train arrival.

The `station` argument must be one of: `NWK`, `HAR`, `JSQ`, `GRV`, `EXP`, `WTC`, `NEW`, `HOB`, `CHR`, `09S`, `14S`, `23S`, or `33S`.

- `led-display.py` contains the main display logic. Assumes we are using Adafruit RGB HAT for `hardware-mapping` argument. Also assumes that we are using three 64x32 LED matrices chained together. Most configurable parameters are at the top of the file.
- `parse_args.py` contains command line argument parsing logic.
- `get_train_data.py` contains functions that fetch train arrival and alert data from Path API.
- `station_deltas.py` contains a dictionary mapping estimated travel times between one station to another.
- `mta-font.bdf` is a BDF font that resembles the MTA font used in their LED displays. Font was taken from [here](https://github.com/osresearch/LEDscape/blob/master/src/mta/mta-font.c) and converted into BDF. Certain characters (K, Q, q to name a few) were added as well. 

