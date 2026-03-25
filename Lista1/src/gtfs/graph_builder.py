# Graph Builder for GTFS Data

from dataclasses import dataclass
from datetime import datetime
from itertools import permutations
from gtfs.models import Route, Stop, Trip, StopTime, Calendar, CalendarDate

@dataclass
class GraphEdge:
    start_stop_id: str
    end_stop_id: str
    departure_time: int
    arrival_time: int
    travel_time: int
    route_name: str
    trip_id: str
    
def get_day_of_the_week(date_str: str) -> int:
    date = datetime.strptime(date_str, '%Y%m%d')
    return date.weekday()

def is_service_active(service_id: str, date_str: str, calendars: dict[str, Calendar], calendar_dates: dict[str, list[CalendarDate]]) -> bool:
    for calendar_date in calendar_dates.get(service_id, []):
        if calendar_date.date == date_str:
            return calendar_date.exception_type == 1

    calendar = calendars.get(service_id)
    if calendar and calendar.start_date <= date_str <= calendar.end_date:
        day_of_week = get_day_of_the_week(date_str)
        return getattr(calendar, ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'][day_of_week])
    
    return False


def build_transfer_edges(stops: dict[str, Stop]) -> list[GraphEdge]:
    platforms = {}
    for stop in stops.values():
        if stop.location_type == 0 and stop.parent_station:
            if stop.parent_station not in platforms:
                platforms[stop.parent_station] = []
            platforms[stop.parent_station].append(stop.stop_id)
    
    transfer_edges = []
    for parent, stop_ids in platforms.items():
        for a, b in permutations(stop_ids, 2):
            transfer_edges.append(GraphEdge(
                start_stop_id=a,
                end_stop_id=b,
                departure_time=0,
                arrival_time=0,
                travel_time=2,
                route_name="TRANSFER",
                trip_id=""
            ))
    return transfer_edges
    

    
def build_trip_edges(routes: dict[str, Route], trips: dict[str, Trip], stop_times: dict[str, list[StopTime]], calendars: dict[str, Calendar], calendar_dates: dict[str, list[CalendarDate]], date_str: str) -> list[GraphEdge]:
    trip_edges = []
    
    for trip_id, trip in trips.items():
        if not is_service_active(trip.service_id, date_str, calendars, calendar_dates):
            continue
        
        stops_in_trip = sorted(stop_times.get(trip_id, []), key=lambda st: st.stop_sequence)
        if len(stops_in_trip) < 2:
            continue
        
        route = routes.get(trip.route_id)
        if route is None:
            continue
        
        for i in range(len(stops_in_trip) - 1):
            start_stop_time = stops_in_trip[i]
            end_stop_time = stops_in_trip[i + 1]

            travel = end_stop_time.arrival_time - start_stop_time.departure_time
            if travel < 0:
                continue
            
            edge = GraphEdge(
                start_stop_id=start_stop_time.stop_id,
                end_stop_id=end_stop_time.stop_id,
                departure_time=start_stop_time.departure_time,
                arrival_time=end_stop_time.arrival_time,
                travel_time=travel,
                route_name=route.route_short_name or route.route_long_name or trip.route_id,
                trip_id=trip_id
            )
            trip_edges.append(edge)        
    return trip_edges

def build_graph(routes: dict[str, Route], stops: dict[str, Stop], trips: dict[str, Trip], stop_times: dict[str, list[StopTime]], calendars: dict[str, Calendar], calendar_dates: dict[str, list[CalendarDate]], date_str: str) -> list[GraphEdge]:
    trip_edges = build_trip_edges(routes, trips, stop_times, calendars, calendar_dates, date_str)
    transfer_edges = build_transfer_edges(stops)
    return trip_edges + transfer_edges

   

def convert_time(minutes: int) -> str:
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"
   
def get_direction(edge: GraphEdge, trips: dict[str, Trip]) -> str:
    trip = trips.get(edge.trip_id)
    return trip.trip_headsign if trip else ""

def print_graph_edges(graph: list[GraphEdge], stops: dict[str, Stop], trips: dict[str, Trip]) -> None:
    
    if not graph:
        print("No edges to display.")
        return

    for edge in graph:
        start_stop = stops.get(edge.start_stop_id)
        end_stop = stops.get(edge.end_stop_id)
        if not start_stop or not end_stop:
            continue
        print(f"{start_stop.stop_name}{' platform: ' + start_stop.platform_code if start_stop.platform_code else ''} -> {end_stop.stop_name}{' platform: ' + end_stop.platform_code if end_stop.platform_code else ''} | Departure: {convert_time(edge.departure_time)} | Arrival: {convert_time(edge.arrival_time)} | Travel Time: {convert_time(edge.travel_time)} | Route: {edge.route_name} | Trip ID: {edge.trip_id} | Direction: {get_direction(edge, trips)}")