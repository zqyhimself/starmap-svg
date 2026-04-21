
import svgwrite
import random
import math
import argparse
import calendar

############ DEFAULT VALUES AND CONSTS ####################################

font_style = "font-size:10px; letter-spacing:0.7px; font-family:sans-serif; stroke-width:4;"
font_style2 = "font-size:2px; letter-spacing:0.7px; font-family:sans-serif; stroke-width:2;"

background_color = "rgb(45,59,98)"
line_color = "rgb(255,255,255)"
star_color = "rgb(255,255,255)"
constellation_color = "rgb(255,255,255)"

output_file = 'starmap.svg'

#Date & Time
date = '01.01.2000'
time = '12.00.00'
utc = 2
summertime = 'auto'

#Coordinates
coord = "60.186,24.959"

fullview = False
guides = False
constellation = False
planets = False

#placetext for leftdown corner
info = 'HELSINKI'

#Size of poster in mm
width = 200
height = 200

#empty space in left and right of the starmap
borders = 50

def mm_to_px(mm):
	px = mm*96/25.4
	return px

#Smaller the star bigger the magnitude
magnitude_limit = 6.5
aperture = 0.4 

############ STARDATAFILE ################################################

#Stars declination and hour data file "Yale Bright Star Catalog 5"
file1 = "datafiles/ybsc5.txt"
file2 = "datafiles/extradata.txt" #extra star data for magnitude 6,5 and higher
file3 = "datafiles/constellation_lines.txt"

data = []
constellation_lines = []

def hours_to_decimal(ra):##use this for ybsc5
	
	seconds  = float(ra[0:2])*60*60 	#hour
	seconds += float(ra[3:5])*60	#minute
	seconds += float(ra[5:7])		#seconds
	degree = seconds*360/(24*60*60)
	return degree


def read_ybsc5():
	global data
	with open(file1, 'rt') as f:
		for line in f:
			#RA,DEC,mag,constellation

			if line[75:83].isspace() is False:
				ra = line[75:77]+'.'+line[77:81]
				ra = hours_to_decimal(ra)
				dec = float(line[83:86]+'.'+line[87:90])
				mag = float(line[103:107])
				constellation = line[11:14]
				greek = line[7:10]
				data.append([ra,dec,mag,constellation,greek])
				

def read_extra_star_coordinate_file():
	global data
	with open(file2, 'rt') as f:
		for line in f:
			if (',' in line): 
				tmp = ([ n for n in line.strip().split(',')])
				if float(tmp[2]) > 6.5:
					tmp[0] = hours_to_decimal(tmp[0])
					data.append([float(tmp[0]), float(tmp[1]), float(tmp[2]), " "," "])


def read_constellation_file():
	with open(file3, 'rt') as f:
		for line in f:
			tmp = ([ n for n in line.strip().split(' ')])
			tmp[1] = float(tmp[1])*360/24
			tmp[2] = float(tmp[2])
			tmp[3] = float(tmp[3])*360/24
			tmp[4] = float(tmp[4])
			constellation_lines.append(tmp)






############ SUMMERTIME (DST) DETECTION ##################################

# Automated DST detection. Rules used:
#   Northern hemisphere — EU rule: last Sunday of March → last Sunday of October.
#   Southern hemisphere — approximate (AU-style): first Sunday of October →
#   first Sunday of April. Users with a different local rule can still pass
#   -summertime true / false explicitly.

def _last_sunday_of_month(year, month):
	_, last_day = calendar.monthrange(year, month)
	offset = (calendar.weekday(year, month, last_day) - calendar.SUNDAY) % 7
	return last_day - offset

def _first_sunday_of_month(year, month):
	first_wd = calendar.weekday(year, month, 1)
	offset = (calendar.SUNDAY - first_wd) % 7
	return 1 + offset

def _detect_summertime(date_str, latitude):
	day   = int(date_str[0:2])
	month = int(date_str[3:5])
	year  = int(date_str[6:10])

	if latitude >= 0:
		# Northern hemisphere — EU rule
		if month < 3 or month > 10:
			return False
		if 3 < month < 10:
			return True
		if month == 3:
			return day >= _last_sunday_of_month(year, 3)
		return day < _last_sunday_of_month(year, 10)  # month == 10
	else:
		# Southern hemisphere (AU-style)
		if month > 10 or month < 4:
			return True
		if 4 < month < 10:
			return False
		if month == 10:
			return day >= _first_sunday_of_month(year, 10)
		return day < _first_sunday_of_month(year, 4)  # month == 4

def _parse_summertime_arg(v):
	if v is None:
		return 'auto'
	s = str(v).strip().lower()
	if s in ('', 'auto'):
		return 'auto'
	if s in ('true', 'yes', '1', 'on'):
		return True
	if s in ('false', 'no', '0', 'off'):
		return False
	raise argparse.ArgumentTypeError("summertime must be auto/true/false")

def _parse_bool_arg(v):
	if v is None:
		return True
	s = str(v).strip().lower()
	if s in ('true', 'yes', '1', 'on', ''):
		return True
	if s in ('false', 'no', '0', 'off'):
		return False
	raise argparse.ArgumentTypeError("expected true/false")


############ SOLAR SYSTEM BODIES #########################################

# Keplerian orbital elements and daily rates from Paul Schlyter's
# "How to compute planetary positions" — http://stjarnhimlen.se/comp/ppcomp.html
# Entry format:
#   [N0, N_rate, i0, i_rate, w0, w_rate, a0, a_rate, e0, e_rate, M0, M_rate]
# where d is days since J2000.0 (2000 Jan 1, 0h UT, minus 1.5 per Schlyter).
# Sun element set represents the reflex (Earth's) orbit; Moon elements are
# already geocentric. Planets are heliocentric.

_ORBITAL_ELEMENTS = {
	'Sun':     [  0.0000,  0.0000000000,  0.0000,  0.000000e+00, 282.9404,  4.70935e-05,  1.000000,  0.00000e+00, 0.016709, -1.151e-09, 356.0470,  0.9856002585],
	'Moon':    [125.1228, -0.0529538083,  5.1454,  0.000000e+00, 318.0634,  0.1643573223, 60.266600,  0.00000e+00, 0.054900,  0.000e+00, 115.3654, 13.0649929509],
	'Mercury': [ 48.3313,  3.24587e-05,   7.0047,  5.000000e-08,  29.1241,  1.01444e-05,  0.387098,  0.00000e+00, 0.205635,  5.590e-10, 168.6562,  4.0923344368],
	'Venus':   [ 76.6799,  2.46590e-05,   3.3946,  2.750000e-08,  54.8910,  1.38374e-05,  0.723330,  0.00000e+00, 0.006773, -1.302e-09,  48.0052,  1.6021302244],
	'Mars':    [ 49.5574,  2.11081e-05,   1.8497, -1.780000e-08, 286.5016,  2.92961e-05,  1.523688,  0.00000e+00, 0.093405,  2.516e-09,  18.6021,  0.5240207766],
	'Jupiter': [100.4542,  2.76854e-05,   1.3030, -1.557000e-07, 273.8777,  1.64505e-05,  5.202560,  0.00000e+00, 0.048498,  4.469e-09,  19.8950,  0.0830853001],
	'Saturn':  [113.6634,  2.38980e-05,   2.4886, -1.081000e-07, 339.3939,  2.97661e-05,  9.554750,  0.00000e+00, 0.055546, -9.499e-09, 316.9670,  0.0334442282],
	'Uranus':  [ 74.0005,  1.39780e-05,   0.7733,  1.900000e-08,  96.6612,  3.05650e-05, 19.181710, -1.55000e-08, 0.047318,  7.450e-09, 142.5905,  0.0117258060],
	'Neptune': [131.7806,  3.01730e-05,   1.7700, -2.550000e-07, 272.8461, -6.02700e-06, 30.058260,  3.31300e-08, 0.008606,  2.150e-09, 260.2471,  0.0059951470],
}

# Display style — apparent size scaling and label color.
_PLANET_STYLE = {
	'Sun':     {'color': 'rgb(255,210, 80)', 'size': 3.0},
	'Moon':    {'color': 'rgb(230,230,230)', 'size': 2.6},
	'Mercury': {'color': 'rgb(190,190,190)', 'size': 1.3},
	'Venus':   {'color': 'rgb(255,240,180)', 'size': 1.8},
	'Mars':    {'color': 'rgb(255,120, 90)', 'size': 1.5},
	'Jupiter': {'color': 'rgb(255,200,140)', 'size': 2.0},
	'Saturn':  {'color': 'rgb(240,220,170)', 'size': 1.8},
	'Uranus':  {'color': 'rgb(170,220,230)', 'size': 1.3},
	'Neptune': {'color': 'rgb(140,170,230)', 'size': 1.3},
}

_PLANET_ORDER = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars',
                 'Jupiter', 'Saturn', 'Uranus', 'Neptune']


def _schlyter_day(date_str, time_str, utc_offset, dst_hour):
	"""Days since 2000 Jan 0.0 TDT (Schlyter's d), incl. fractional UT."""
	year  = int(date_str[6:10])
	month = int(date_str[3:5])
	day   = int(date_str[0:2])
	hour   = float(time_str[0:2])
	minute = float(time_str[3:5])
	second = float(time_str[6:8])

	d = (367*year
	     - 7*(year + (month + 9)//12)//4
	     + 275*month//9
	     + day - 730530)
	ut_hours = hour + minute/60.0 + second/3600.0 - utc_offset - dst_hour
	return d + ut_hours/24.0


def _solve_kepler(M_rad, e):
	"""Iteratively solve Kepler's equation E - e*sin(E) = M."""
	E = M_rad + e*math.sin(M_rad)*(1.0 + e*math.cos(M_rad))
	for _ in range(10):
		dE = (E - e*math.sin(E) - M_rad) / (1.0 - e*math.cos(E))
		E -= dE
		if abs(dE) < 1e-10:
			break
	return E


def _orbital_state(body, d):
	N0, Nr, i0, ir, w0, wr, a0, ar, e0, er, M0, Mr = _ORBITAL_ELEMENTS[body]
	N_deg = (N0 + Nr*d) % 360
	w_deg = (w0 + wr*d) % 360
	M_deg = (M0 + Mr*d) % 360
	N = math.radians(N_deg)
	i = math.radians(i0 + ir*d)
	w = math.radians(w_deg)
	a = a0 + ar*d
	e = e0 + er*d
	M = math.radians(M_deg)
	L = math.radians((N_deg + w_deg + M_deg) % 360)  # mean longitude
	return N, i, w, a, e, M, L


def _body_xyz(body, d):
	"""Ecliptic rectangular coords. Heliocentric for planets, geocentric for Sun/Moon."""
	N, i, w, a, e, M, _ = _orbital_state(body, d)
	E = _solve_kepler(M, e)
	xv = a*(math.cos(E) - e)
	yv = a*math.sqrt(1.0 - e*e)*math.sin(E)
	v = math.atan2(yv, xv)
	r = math.hypot(xv, yv)
	cos_vw = math.cos(v + w); sin_vw = math.sin(v + w)
	x = r*(math.cos(N)*cos_vw - math.sin(N)*sin_vw*math.cos(i))
	y = r*(math.sin(N)*cos_vw + math.cos(N)*sin_vw*math.cos(i))
	z = r*sin_vw*math.sin(i)
	return x, y, z


def _moon_xyz(d):
	"""Moon geocentric ecliptic xyz with Schlyter's main solar perturbations."""
	x, y, z = _body_xyz('Moon', d)
	lon  = math.atan2(y, x)
	lat  = math.atan2(z, math.hypot(x, y))
	dist = math.hypot(x, y, z)

	Nm, _, _, _, _, Mm, Lm = _orbital_state('Moon', d)
	_,  _, _, _, _, Ms, Ls = _orbital_state('Sun',  d)
	D = Lm - Ls
	F = Lm - Nm

	dlon_deg = (
		-1.274 * math.sin(Mm - 2*D)
		+ 0.658 * math.sin(2*D)
		- 0.186 * math.sin(Ms)
		- 0.059 * math.sin(2*Mm - 2*D)
		- 0.057 * math.sin(Mm - 2*D + Ms)
		+ 0.053 * math.sin(Mm + 2*D)
		+ 0.046 * math.sin(2*D - Ms)
		+ 0.041 * math.sin(Mm - Ms)
		- 0.035 * math.sin(D)
		- 0.031 * math.sin(Mm + Ms)
	)
	dlat_deg = (
		-0.173 * math.sin(F - 2*D)
		- 0.055 * math.sin(Mm - F - 2*D)
		- 0.046 * math.sin(Mm + F - 2*D)
		+ 0.033 * math.sin(F + 2*D)
		+ 0.017 * math.sin(2*Mm + F)
	)
	lon += math.radians(dlon_deg)
	lat += math.radians(dlat_deg)

	x = dist * math.cos(lat) * math.cos(lon)
	y = dist * math.cos(lat) * math.sin(lon)
	z = dist * math.sin(lat)
	return x, y, z


def solar_system_positions(d):
	"""Return {body: (ra_rad, dec_rad)} geocentric equatorial coords at day d."""
	sun = _body_xyz('Sun', d)
	ecl = math.radians(23.4393 - 3.563e-7 * d)
	cos_e = math.cos(ecl); sin_e = math.sin(ecl)

	positions = {}
	for name in _PLANET_ORDER:
		if name == 'Sun':
			x, y, z = sun
		elif name == 'Moon':
			x, y, z = _moon_xyz(d)
		else:
			xh, yh, zh = _body_xyz(name, d)
			# heliocentric -> geocentric
			x = xh + sun[0]; y = yh + sun[1]; z = zh + sun[2]

		xe = x
		ye = y*cos_e - z*sin_e
		ze = y*sin_e + z*cos_e
		ra  = math.atan2(ye, xe) % (2*math.pi)
		dec = math.atan2(ze, math.hypot(xe, ye))
		positions[name] = (ra, dec)
	return positions


############ ARGPARSER ###################################################

parser = argparse.ArgumentParser(description='Generate starmap svg file')
parser.add_argument('-coord','--coord', help='coordinates in format northern,eastern',default=coord )
parser.add_argument('-time','--time', help='time in format hour.minute.second',default=time)
parser.add_argument('-date','--date', help='date in format day.month.year', default=date)
parser.add_argument('-utc','--utc',nargs='?', help='utc of your location -12 to +12', type=int , default=utc)
parser.add_argument('-magn','--magn',nargs='?', help='magnitude limit 0.1-12.0',type=float, default=magnitude_limit)

parser.add_argument('-summertime','--summertime',nargs='?', help='summertime/DST: auto (default), true, false',type=_parse_summertime_arg, default=summertime, const='auto')
parser.add_argument('-guides','--guides',nargs='?', help='draw guides True/False',type=bool, default=guides )
parser.add_argument('-constellation','--constellation',nargs='?', help='show constellation True/False',type=bool, default=constellation )
parser.add_argument('-planets','--planets',nargs='?', help='draw planets, Sun and Moon True/False',type=_parse_bool_arg, default=planets, const=True)
parser.add_argument('-o','--output', help='output filename.svg',default='starmap.svg' )
parser.add_argument('-width','--width',nargs='?', help='width in mm',type=int, default=width)
parser.add_argument('-height','--height',nargs='?', help='height in mm',type=int, default=height)
parser.add_argument('-info','--info', help='Info text example eame of the place', default=info )


args = parser.parse_args()

coord = args.coord
time = args.time
date = args.date
utc = args.utc
info = args.info
output_file = args.output
guides = args.guides
magnitude_limit = args.magn
constellation = args.constellation
summertime = args.summertime
planets = args.planets

height = args.height
width = args.width

print("coordinates:",coord)
print("date:",date)
print("time",time)

#latitude and longitude
northern,eastern = map(float,coord.split(','))

#Resolve automated summertime once coordinates are known
if summertime == 'auto':
	summertime = _detect_summertime(date, northern)
	print("summertime (auto):", summertime)
else:
	print("summertime:", summertime)

########## DRAWING FUNCTIONS  ###########################################

# Generates random star shape to given coordinate and magnitude and color
def draw_star(x,y,mag,color):

	# randomize the number of points in star
	points = random.randint(4,8)
	points = points * 2
	angle = 2*math.pi/(points)

	# generate the path
	path = []
	for point in range(0,points,2):
		#point of star
		path.append(polar_to_cartesian(mag,angle*point,x,y))
		#point between two star points
		path.append(polar_to_cartesian(mag/2,angle*(point+1),x,y))
	
	#add object to svg
	stars = image.add(image.polygon(path,id ='star',stroke="none",fill=color))


def draw_dot(x,y,mag,color):
	image.add(image.circle((x,y),mag,id ='dot',stroke="none",fill=color))


def draw_line(x0,y0,x1,y1,color):
	image.add(image.line((x0,y0),(x1,y1),id ='line',stroke=color,stroke_width = "0.5"))


########## TIME CALCULATION  ###########################################

#date to days
def date_and_time_to_rad(date,time):

	#J2000 Epoch 01.01.2000 12.00.00
	epochyear = 2000.0
	epochhour = 12.0

	calculation_mistake = -5.1

	days_in_year = 365.2425
	months = [31,28,31,30,31,30,31,31,30,31,30,31] #Array of days in months

	year = int(date[6:10])
	month  = int(date[3:5])
	day    = int(date[0:2])
	hour   = float(time[0:2])
	minute = float(time[3:5])
	second = float(time[6:8])

	#years to days
	daycounter = (year-epochyear)*days_in_year
	#month to days
	daycounter  += sum(months[0:month-1])	
	#days
	daycounter += day-1				

	secondcounter  = (hour- epochhour+ calculation_mistake)*60*60
	secondcounter  += minute*60
	secondcounter += second			
	
	#Summertime
	if(summertime):
		secondcounter -= (60*60)
	
	#UTC
	secondcounter -= (60*60*utc)


	#calculate degree from days
	degree = -((daycounter)*360.0/days_in_year) % 360

	#calculate degree from seconds
	degree -= ((secondcounter)*360/(24*60*60)) % 360

	return math.radians(degree)


########## GEOMETRY CALCULATION  ###########################################

#change polar coordinates to cartesian coordinates
def polar_to_cartesian(radius,angle,centerx,centery):
	return [centerx + radius*math.cos(angle), centery + radius*math.sin(angle)]


def angle_between(north,east,dec_angle,ra_angle):
	delta_ra = ra_angle - east
	rad = math.acos(math.cos(delta_ra)*math.cos(north)*math.cos(dec_angle) + math.sin(north)*math.sin(dec_angle))
	return rad 

def right_ascension_to_rad(ra):
	return math.radians(float(ra))

def declination_to_rad(dec):
    return math.radians(float(dec))


########## PROJECTIONS  ######################################################

def stereographic(latitude0,longitude0, latitude, longitude, R):
	#http://mathworld.wolfram.com/StereographicProjection.html
	k = (2*R)/( 1 + math.sin(latitude0)*math.sin(latitude) + math.cos(latitude0)*math.cos(latitude)*math.cos(longitude-longitude0))
	x = k * math.cos(latitude) * math.sin(longitude-longitude0)
	y = k * (math.cos(latitude0)*math.sin(latitude) - math.sin(latitude0)*math.cos(latitude)*math.cos(longitude-longitude0))

	return x,y

########## STAR AND GUIDE GENERATION  ########################################

def generate_starmap(northern_N,eastern_E,date,time):

	#counter of stars drawn
	counter = 0

	N = math.radians(northern_N)
	E = math.radians(eastern_E)

	raddatetime = date_and_time_to_rad(date,time)
	
	if(guides is True):
		draw_guides = []
		
		for degrees in range(-3,3):
			for lines in range(0,360):
				draw_guides.append([degrees*30,lines])

		for hours in range(0,24):
			for lines in range(-160,160):
				draw_guides.append([lines/2.0,hours/24*360])

		for line in draw_guides:

			ascension = right_ascension_to_rad(line[1])+raddatetime
			declination = declination_to_rad(line[0])


			#magnitude of dot
			brightness = 1.1

			angle_from_viewpoint = angle_between(N,E,declination,ascension)
			x,y = stereographic(N,E, declination, ascension, width-(borders))

			#draw guides inside half sphere
			if ((angle_from_viewpoint <= math.radians(89)) or fullview):
				draw_dot(half_x-x,half_y-y,brightness*aperture,line_color)
				# if(line[0] == 30 and line[1] % 1 == 0):
				# 	image.add(image.text(str(line[1]), insert=(half_x-x,half_y-y), fill=line_color, style=font_style2))

	for line in data:
		if(line[2] < magnitude_limit):

			#star position from datafile
			ascension = right_ascension_to_rad(line[0])+raddatetime
			declination = declination_to_rad(line[1])

			x,y = stereographic(N,E, declination, ascension, width-(borders))

			angle_from_viewpoint = angle_between(N,E,declination,ascension)

			#size of the star in image
			magn = float(line[2])
			if(magn > 7.0):
				magn = 7.0
			brightness = 8-magn

			#draw only stars that are inside half sphere
			if ((angle_from_viewpoint <= math.radians(90)) or fullview):
				if (brightness < 2):
					draw_dot(half_x-x,half_y-y,brightness*aperture,star_color)
				else:
					draw_star(half_x-x,half_y-y,brightness*aperture,star_color)

				if(constellation is True):
					if(line[4].isspace() is False and magn < 3):
						image.add(image.text(line[4] , insert=(half_x-x+3,half_y-y+3), fill=line_color, style=font_style2))
			counter += 1
			if counter %1000 == 0:
				print(counter)


def generate_constellations(northern_N,eastern_E,date,time):
	N = math.radians(northern_N)
	E = math.radians(eastern_E)

	raddatetime = date_and_time_to_rad(date,time)
	
	for line in constellation_lines:
		ascension0 = right_ascension_to_rad(line[1])+raddatetime
		declination0 = declination_to_rad(line[2])
		x0,y0 = stereographic(N,E, declination0, ascension0, width-(borders))

		ascension1 = right_ascension_to_rad(line[3])+raddatetime
		declination1 = declination_to_rad(line[4])
		x1,y1 = stereographic(N,E, declination1, ascension1, width-(borders))

		angle_from_viewpoint1 = angle_between(N,E,declination0,ascension0)
		angle_from_viewpoint2 = angle_between(N,E,declination1,ascension1)

		if ((angle_from_viewpoint1 <= math.radians(90))  and (angle_from_viewpoint2 <= math.radians(90)) or fullview):
			draw_line(half_x-x0,half_y-y0,half_x-x1,half_y-y1,line_color)

def generate_planets(northern_N,eastern_E,date,time):
	"""Draw Sun, Moon and the classical + outer planets for the given moment."""
	N = math.radians(northern_N)
	E = math.radians(eastern_E)

	raddatetime = date_and_time_to_rad(date,time)

	# Schlyter's day number uses UT — match what date_and_time_to_rad does.
	dst_hour = 1 if summertime else 0
	d = _schlyter_day(date, time, utc, dst_hour)
	positions = solar_system_positions(d)

	for name in _PLANET_ORDER:
		ra, dec = positions[name]
		ascension   = ra + raddatetime
		declination = dec

		angle_from_viewpoint = angle_between(N,E,declination,ascension)
		if angle_from_viewpoint > math.radians(90) and not fullview:
			continue

		x,y = stereographic(N,E, declination, ascension, width-(borders))
		style = _PLANET_STYLE[name]

		image.add(image.circle(
			(half_x-x, half_y-y), style['size'],
			stroke=line_color, stroke_width="0.3", fill=style['color']))
		image.add(image.text(
			name,
			insert=(half_x-x + style['size'] + 1.5, half_y-y - style['size']),
			fill=style['color'], style=font_style2))


########## GENERATE SVG  ###########################################


if __name__ == '__main__':

	read_ybsc5()
	read_extra_star_coordinate_file()
	read_constellation_file()

	half_x = mm_to_px(width/2)
	half_y = mm_to_px(height/2)

	#Svgfile
	image = svgwrite.Drawing(output_file,size=(str(width)+'mm',str(height)+'mm'))

	#Background
	image.add(image.rect(insert=(0, 0),size=('100%', '100%'), rx=None, ry=None, fill=background_color))

	#Stars generation
	generate_starmap(northern,eastern,date,time)
	if constellation:
		generate_constellations(northern,eastern,date,time)
	if planets:
		generate_planets(northern,eastern,date,time)

	#Text in bottom corner
	image.add(image.text(info, insert=("20mm", str(height-21)+'mm'), fill=line_color, style=font_style))
	image.add(image.text(str(northern)+" N "+str(eastern)+" E " , insert=("20mm", str(height-17)+'mm'), fill=line_color, style=font_style))
	image.add(image.text(date +" "+ time+ " UTC " + str(utc), insert=("20mm", str(height-13)+'mm'), fill=line_color, style=font_style))

	image.save()
	print(output_file ," generated")

