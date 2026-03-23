from dataclasses import dataclass

# GTFS Models

#standardowe przystanek początkowy, przystanek końcowy, nazwa wykorzystanej linii, czar rozpoczęcia, czas zakończenia
#błędów wartość minimalizowanego kryterium i czas potrzebny do obliczenia najkrótszej ścieżki
#klasy zostały ograniczone do atrybutów potrzebnych do wykonania zadania
@dataclass        
class Route:
    route_id: str 
    route_short_name: str 
    route_long_name: str 
     

@dataclass
class Stop:
    stop_id: str 
    stop_name: str 
    stop_lat: float 
    stop_lon: float 
    location_type: int 
    parent_station: str | None
    platform_code: str | None
        
@dataclass
class Trip:
    route_id: str 
    service_id: str 
    trip_id: str 
    trip_headsign: str 
            
@dataclass
class StopTime:
    trip_id: str 
    arrival_time: int 
    departure_time: int 
    stop_id: str 
    stop_sequence: int 
    pickup_type: int 

@dataclass        
class Calendar:
    service_id: str 
    monday: bool 
    tuesday: bool 
    wednesday: bool 
    thursday: bool 
    friday: bool 
    saturday: bool 
    sunday: bool 
    start_date: str 
    end_date: str 

@dataclass        
class CalendarDate:
    service_id: str 
    date: str 
    exception_type: int 

                      