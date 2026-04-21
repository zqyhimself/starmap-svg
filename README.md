# starmap-svg
for generating svg starmaps from selected coordinates and time

## Requirements

Python ≥ 3.8, with [`uv`](https://docs.astral.sh/uv/) managing the
dependencies:

	uv sync

Alternatively, `pip install svgwrite` still works for a manual setup.

## Usage
	uv run python starmap.py -h

	optional arguments:
	  -h, --help            show this help message and exit

	  -coord COORD, --coord COORD
	                        coordinates in format northern,eastern
	  -time TIME, --time TIME
	                        time in format hour.minute.second
	  -date DATE, --date DATE
	                        date in format day.month.year
	  -utc [UTC], --utc [UTC]
	                        utc of your location -12 to +12
	  -magn [MAGN], --magn [MAGN]
	                        magnitude limit 0.1-12.0
	  -summertime [SUMMERTIME], --summertime [SUMMERTIME]
	                        summertime/DST: auto (default), true, false
	  -guides [GUIDES], --guides [GUIDES]
	                        draw guides True/False
	  -constellation [CONSTELLATION], --constellation [CONSTELLATION]
	                        show constellation True/False
	  -constellation_names [CONSTELLATION_NAMES], --constellation_names [CONSTELLATION_NAMES]
	                        print constellation full names True/False
	  -planets [PLANETS], --planets [PLANETS]
	                        draw Sun, Moon and planets True/False
	  -o OUTPUT, --output OUTPUT
	                        output filename.svg
	  -width [WIDTH], --width [WIDTH]
	                        width in mm
	  -height [HEIGHT], --height [HEIGHT]
	                        height in mm
	  -info INFO, --info INFO
	                        Info text example eame of the place




## Example 1
	uv run python starmap.py -coord 60.186,24.959 -time 12.00.00 -date 01.01.2000 -utc +2 -constellation True

![image](https://github.com/skeletor-git/starmap-svg/blob/master/example/starmap.png)

## Example 2
	uv run python starmap.py -coord 35.684,139.728 -time 20.00.00 -date 15.07.2018 -utc +9 -info TOKYO -guides True -magn 10.0 -width 150 -height 220

![image](https://github.com/skeletor-git/starmap-svg/blob/master/example/starmap2.png)

## Example 3 — planets, constellation names, auto DST

	uv run python starmap.py -coord 60.186,24.959 -time 22.00.00 -date 22.07.2024 -utc +2 \
	    -constellation True -constellation_names True -planets True


## Info

Stars data: "Yale Bright Star Catalog ver5"
http://tdc-www.harvard.edu/catalogs/bsc5.html

Sky orientation uses the IAU 1982 low-precision GMST formula; the
J2000 star and constellation-line positions are precessed to the epoch
of the given date (Meeus, chapter 21).

Planet / Sun / Moon positions are computed with the simplified Keplerian
algorithm from Paul Schlyter's "How to compute planetary positions"
(http://stjarnhimlen.se/comp/ppcomp.html), including the main solar
perturbations of the Moon.

Automated summertime applies the EU rule in the northern hemisphere
(last Sunday of March → last Sunday of October) and the AU-style rule
in the southern hemisphere (first Sunday of October → first Sunday of
April). Pass `-summertime true|false` to override.