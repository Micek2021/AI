# Graph Builder for GTFS Data

from dataclasses import dataclass
from datetime import datetime
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

    

    
def build_graph(routes: dict[str, Route], stops: dict[str, Stop], trips: dict[str, Trip], stop_times: dict[str, list[StopTime]], calendars: dict[str, Calendar], calendar_dates: dict[str, list[CalendarDate]], date_str: str) -> list[GraphEdge]:
    graph = []
    
    for trip_id, trip in trips.items():
        if not is_service_active(trip.service_id, date_str, calendars, calendar_dates):
            continue
        
        stops_in_trip = stop_times.get(trip_id, [])
        stops_in_trip.sort(key=lambda st: st.stop_sequence)
        
        for i in range(len(stops_in_trip) - 1):
            start_stop_time = stops_in_trip[i]
            end_stop_time = stops_in_trip[i + 1]
            route = routes[trip.route_id]
            edge = GraphEdge(
                start_stop_id=start_stop_time.stop_id,
                end_stop_id=end_stop_time.stop_id,
                departure_time=start_stop_time.departure_time,
                arrival_time=end_stop_time.arrival_time,
                travel_time=end_stop_time.arrival_time - start_stop_time.departure_time,
                route_name=route.route_short_name or route.route_long_name,
                trip_id=trip_id
            )
            graph.append(edge)
    return graph
   

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
        start_stop = stops[edge.start_stop_id]
        end_stop = stops[edge.end_stop_id]
        print(f"{start_stop.stop_name} -> {end_stop.stop_name} | Departure: {convert_time(edge.departure_time)} | Arrival: {convert_time(edge.arrival_time)} | Travel Time: {convert_time(edge.travel_time)} | Route: {edge.route_name} | Trip ID: {edge.trip_id} | Direction: {get_direction(edge, trips)}")