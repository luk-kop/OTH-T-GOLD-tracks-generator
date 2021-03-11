from pyproj import Geod
from typing import Dict
import re
import argparse


def coords_regex(arg_value):
    """
    Position validator for argparse 'coords' parameter.
    Coordinates desired format: 5430N-01920E
    """
    pattern = re.compile('^(([0-8]\d[0-5]\d|9000)(N|S)-(([0-1][0-7]\d[0-5]\d)|(0[0-9]\d[0-5]\d)|18000)(E|W))$')
    if not pattern.match(arg_value):
        raise argparse.ArgumentTypeError
    return arg_value


def position_to_geod_format(position: Dict[str, str]):
    """
    Convert position to format compatible with 'Geod.fwd' func.
    Input format: 5430N 01920E
    Output format: 54.5 19.333
    """
    latitude_dir = position['latitude_dir']
    longitude_dir = position['longitude_dir']
    latitude_init = position['latitude']
    longitude_init = position['longitude']
    if latitude_dir == 'N':
        latitude_formatted = float(latitude_init[:2]) + (float(latitude_init[2:]) / 60)
    else:
        latitude_formatted = - float(latitude_init[:2]) - (float(latitude_init[2:]) / 60)
    if longitude_dir == 'E':
        longitude_formatted = float(longitude_init[:3]) + (float(longitude_init[3:]) / 60)
    else:
        longitude_formatted= - float(longitude_init[:3]) - (float(longitude_init[3:]) / 60)
    return latitude_formatted, longitude_formatted


def calculated_position(latitude_start: float, longitude_start: float, distance: int, direction: int):
    """
    Calculates the new position based on the given azimuth and distance
    Returns position in format: ('542959', 'N', '0192915', 'E')
    """
    geo = Geod(ellps='WGS84')
    # Forward transformation - returns longitude, latitude, back azimuth of terminus points
    lon_new, lat_new, back_azimuth = geo.fwd(longitude_start, latitude_start, direction, distance)
    if lat_new >= 0:
        lat_dir = 'N'
    else:
        lat_dir = 'S'
    if lon_new >= 0:
        lon_dir = 'E'
    else:
        lon_dir = 'W'
    lon_new, lat_new = abs(lon_new), abs(lat_new)

    # New GPS position after calculation.
    cords_new = []
    for cord in [lat_new, lon_new]:
        cord_degrees = int(cord)
        try:
            cord_minutes = round(cord % int(cord) * 60, 3)
        except ZeroDivisionError:
            cord_minutes = round(cord * 60, 3)
        if cord_minutes == 60:
            cord_degrees += 1
            cord_minutes = 0
        cord_seconds = int((cord_minutes % 1) * 60)
        cords_new.append((cord_degrees, cord_minutes, cord_seconds))
    lat_tuple, lon_tuple = cords_new
    lat_degrees, lat_minutes, lat_seconds = lat_tuple
    lon_degrees, lon_minutes, lon_seconds = lon_tuple
    # Render the position data into the correct format
    latitude_calculated = f'{lat_degrees:02}{int(lat_minutes):02}{lat_seconds:02}'
    latitude_dir_calculated = f'{lat_dir}'
    longitude_calculated = f'{lon_degrees:03}{int(lon_minutes):02}{lon_seconds:02}'
    longitude_dir_calculated = f'{lon_dir}'
    return latitude_calculated, latitude_dir_calculated, longitude_calculated, longitude_dir_calculated