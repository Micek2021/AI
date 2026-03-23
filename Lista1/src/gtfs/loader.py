# loading models from data

import csv
from gtfs.models import *
from pathlib import Path

data_dir = Path('data')

def parse_time(s: str) -> int :
    h, m, _ = s.split(':')
    return int(h) * 60 + int(m) 

def load_routes(file_path: str) -> dict[str, Route]:
    routes = {}
    with open(file_path, 'r', encoding='utf-8') as file:
        for row in csv.DictReader(file):
            route = Route(
                route_id=row['route_id'],
                route_short_name=row['route_short_name'],
                route_long_name=row['route_long_name']
            )
            routes[route.route_id] = route
    return routes 


def load_stops(file_path: str) -> dict[str, Stop]:
    stops = {}
    with open(file_path, 'r', encoding='utf-8') as file:
        for row in csv.DictReader(file):
            stop = Stop(
                stop_id=row['stop_id'],
                stop_name=row['stop_name'],
                stop_lat=float(row['stop_lat']),
                stop_lon=float(row['stop_lon']),
                location_type=int(row['location_type']),
                parent_station=row.get('parent_station') or None,
                platform_code=row.get('platform_code') or None
            )
            stops[stop.stop_id] = stop            
    return stops        
       
       
def load_trips(file_path: str) -> dict[str, Trip]:
    trips = {}
    with open(file_path, 'r', encoding='utf-8') as file:
        for row in csv.DictReader(file):
            trip = Trip(
                route_id=row['route_id'],
                service_id=row['service_id'],
                trip_id=row['trip_id'],
                trip_headsign=row['trip_headsign']
            )
            trips[trip.trip_id] = trip            
    return trips

def load_stop_times(file_path: str) -> dict[str, list[StopTime]]:
    stop_times = {}
    with open(file_path, 'r', encoding='utf-8') as file:
        for row in csv.DictReader(file):
            stop_time = StopTime(
                trip_id=row['trip_id'],
                arrival_time=parse_time(row['arrival_time']),
                departure_time=parse_time(row['departure_time']),
                stop_id=row['stop_id'],
                stop_sequence=int(row['stop_sequence']),
                pickup_type=int(row['pickup_type']),
            )
            if stop_time.trip_id not in stop_times:
                stop_times[stop_time.trip_id] = []
            stop_times[stop_time.trip_id].append(stop_time)
    return stop_times
            
def load_calendars(file_path: str) -> dict[str, Calendar]:
    calendars = {}
    with open(file_path, 'r', encoding='utf-8') as file:
        for row in csv.DictReader(file):
            calendar = Calendar(
                service_id=row['service_id'],
                monday=bool(int(row['monday'])),
                tuesday=bool(int(row['tuesday'])),
                wednesday=bool(int(row['wednesday'])),
                thursday=bool(int(row['thursday'])),
                friday=bool(int(row['friday'])),
                saturday=bool(int(row['saturday'])),
                sunday=bool(int(row['sunday'])),
                start_date=row['start_date'],
                end_date=row['end_date']
            )
            calendars[calendar.service_id] = calendar
    return calendars          

def load_calendar_dates(file_path: str) -> dict[str, list[CalendarDate]]:
    calendar_dates = {}
    with open(file_path, 'r', encoding='utf-8') as file:
        for row in csv.DictReader(file):
            calendar_date = CalendarDate(
                service_id=row['service_id'],
                date=row['date'],
                exception_type=int(row['exception_type'])
            )
            if calendar_date.service_id not in calendar_dates:
                calendar_dates[calendar_date.service_id] = []
            calendar_dates[calendar_date.service_id].append(calendar_date)
    return calendar_dates
        
def load_all(data_dir: Path):
    return (
        load_routes(data_dir / 'routes.txt'),
        load_stops(data_dir / 'stops.txt'),
        load_trips(data_dir / 'trips.txt'),
        load_stop_times(data_dir / 'stop_times.txt'),
        load_calendars(data_dir / 'calendar.txt'),
        load_calendar_dates(data_dir / 'calendar_dates.txt')
    )