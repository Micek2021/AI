from algorithms.dijkstra import dijkstra
from gtfs.loader import load_all
from pathlib import Path
from gtfs.graph_builder import build_graph, edges_to_adjacency_list, print_graph_edges
from algorithms.astar import astar_time, astar_transfer
from algorithms.tabu_search import (
    tabu_search_time_basic, tabu_search_time_variable_t, tabu_search_time_aspiration, tabu_search_time_sampling,
    tabu_search_transfer_basic, tabu_search_transfer_variable_t, tabu_search_transfer_aspiration, tabu_search_transfer_sampling
)
import time as time_module
import argparse
import sys
import datetime

routes, stops, trips, stop_times, calendars, calendar_dates = load_all(Path('data'))

def parse_time(time_str: str) -> int:
    try:
        h, m = map(int, time_str.split(':'))
        return h * 60 + m
    except:
        print(f"Błędny format czasu: '{time_str}'. Użyj formatu HH:MM")
        sys.exit(1)

def parse_date(date_str: str) -> str:
    try:
        date_obj = datetime.datetime.strptime(date_str, '%Y%m%d')
        return date_str
    except:
        print(f"Błędny format daty: '{date_str}'. Użyj formatu YYYYMMDD (np. 20260326)")
        sys.exit(1)

def convert_time(minutes: int) -> str:
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"

def resolve_stop_name(stop_name_or_id: str) -> str | None:
    if stop_name_or_id in stops:
        return stop_name_or_id
    
    search_term = stop_name_or_id.lower()
    matches = []
    
    for stop_id, stop in stops.items():
        if search_term in stop.stop_name.lower():
            matches.append((stop_id, stop))
    
    if len(matches) == 0:
        return None
    elif len(matches) == 1:
        return matches[0][0]
    else:
        for stop_id, stop in matches:
            if stop.stop_name.lower() == search_term:
                return stop_id
        return matches[0][0]


def run_dijkstra_mode(start_name: str, end_name: str, start_time: int, date_str: str):    
    start_id = resolve_stop_name(start_name)
    end_id = resolve_stop_name(end_name)
    
    if not start_id:
        print(f"Nie znaleziono przystanku: '{start_name}'")
        sys.exit(1)
    if not end_id:
        print(f"Nie znaleziono przystanku: '{end_name}'")
        sys.exit(1)
    
    graph = edges_to_adjacency_list(build_graph(routes, stops, trips, stop_times, calendars, calendar_dates, date_str))
    
    date_obj = datetime.datetime.strptime(date_str, '%Y%m%d')
    date_display = date_obj.strftime('%Y-%m-%d (%A)')
    
    print(f"\n{'='*80}")
    print(f"DIJKSTRA: {stops[start_id].stop_name} -> {stops[end_id].stop_name}")
    print(f"Kryteria: Minimalizacja czasu")
    print(f"Data: {date_display}")
    print(f"Rozpoczęcie: {convert_time(start_time)}")
    print(f"{'='*80}\n")
    
    start = time_module.time()
    
    path, arrival_time, transfers = dijkstra(graph, start_id, end_id, start_time)
    
    elapsed = time_module.time() - start
    
    if not path:
        print("Nie znaleziono drogi!")
        return
    
    print_graph_edges(path, stops, trips)
    
    print(f"  Czas przybycia: {convert_time(arrival_time)}", file=sys.stderr)
    print(f"  Liczba przesiadek: {transfers}", file=sys.stderr)
    print(f"  Czas obliczeń: {elapsed:.3f}s", file=sys.stderr)

def run_astar_mode(start_name: str, end_name: str, criteria: str, start_time: int, date_str: str):
    start_id = resolve_stop_name(start_name)
    end_id = resolve_stop_name(end_name)
    
    if not start_id:
        print(f"Nie znaleziono przystanku: '{start_name}'")
        sys.exit(1)
    if not end_id:
        print(f"Nie znaleziono przystanku: '{end_name}'")
        sys.exit(1)
    
    graph = edges_to_adjacency_list(build_graph(routes, stops, trips, stop_times, calendars, calendar_dates, date_str))
    
    date_obj = datetime.datetime.strptime(date_str, '%Y%m%d')
    date_display = date_obj.strftime('%Y-%m-%d (%A)')
    
    print(f"\n{'='*80}")
    print(f"A* (ASTAR): {stops[start_id].stop_name} -> {stops[end_id].stop_name}")
    print(f"Kryteria: {'Minimalizacja czasu' if criteria == 't' else 'Minimalizacja przesiadek'}")
    print(f"Data: {date_display}")
    print(f"Rozpoczęcie: {convert_time(start_time)}")
    print(f"{'='*80}\n")
    
    start = time_module.time()
    
    if criteria == 't':
        result = astar_time(graph, start_id, end_id, start_time, stops)
        final_time = result[-1].arrival_time if result else float('inf')
        num_transfers = sum(1 for i in range(1, len(result)) if result[i].trip_id != result[i-1].trip_id) if result else float('inf')
    else:
        result, final_time, num_transfers = astar_transfer(graph, start_id, end_id, start_time)
    
    elapsed = time_module.time() - start
    
    if not result:
        print("  Nie znaleziono drogi!")
        return
    
    print_graph_edges(result, stops, trips)
    
    if result:
        print(f"  Czas przybycia: {convert_time(final_time)}", file=sys.stderr)
        print(f"  Liczba przesiadek: {num_transfers}", file=sys.stderr)
        print(f"  Czas obliczeń: {elapsed:.3f}s", file=sys.stderr)

def run_tabu_search_mode(start_name: str, targets_str: str, criteria: str, start_time: int, date_str: str):
    start_id = resolve_stop_name(start_name)
    if not start_id:
        print(f"Nie znaleziono przystanku: '{start_name}'")
        sys.exit(1)
    
    target_names = [t.strip() for t in targets_str.split(';')]
    targets = []
    for target_name in target_names:
        target_id = resolve_stop_name(target_name)
        if not target_id:
            print(f"Nie znaleziono przystanku: '{target_name}'")
            sys.exit(1)
        targets.append(target_id)
    
    graph = edges_to_adjacency_list(build_graph(routes, stops, trips, stop_times, calendars, calendar_dates, date_str))
    
    date_obj = datetime.datetime.strptime(date_str, '%Y%m%d')
    date_display = date_obj.strftime('%Y-%m-%d (%A)')

    criterion = 'czas' if criteria == 't' else 'przesiadki'
    print("---------------------------------------------------------------------------------------------------")
    print(f"Tabu | start: {stops[start_id].stop_name} | cele: {', '.join(stops[t].stop_name for t in targets)}")
    print(f"Tabu | kryterium: {criterion} | {date_display} | {convert_time(start_time)}")
    print("---------------------------------------------------------------------------------------------------\n")
    
    if criteria == 't':
        variants = [
            ("(a) Bez limitu T", tabu_search_time_basic),
            ("(b) Zmienny T", tabu_search_time_variable_t),
            ("(c) Z aspiracją", tabu_search_time_aspiration),
            ("(d) Z próbkowaniem", tabu_search_time_sampling),
        ]
    else:
        variants = [
            ("(a) Bez limitu T", tabu_search_transfer_basic),
            ("(b) Zmienny T", tabu_search_transfer_variable_t),
            ("(c) Z aspiracją", tabu_search_transfer_aspiration),
            ("(d) Z próbkowaniem", tabu_search_transfer_sampling),
        ]
    
    for variant_name, algo in variants:
        start = time_module.time()
        
        if criteria == 't':
            route, time_cost, transfers = algo(graph, start_id, targets, start_time, max_iterations=50)
            elapsed = time_module.time() - start
            print(f"{variant_name} | {' -> '.join(stops[s].stop_name for s in route)}")
            print(f"Wynik | Czas: {time_cost} min | Przesiadki: {transfers} | Czas obliczen: {elapsed:.3f}s\n", file=sys.stderr)
        else:
            route, transfers, time_cost = algo(graph, start_id, targets, start_time, max_iterations=50)
            elapsed = time_module.time() - start
            print(f"{variant_name} | {' -> '.join(stops[s].stop_name for s in route)}")
            print(f"Wynik | Przesiadki: {transfers} | Czas: {time_cost} min | Czas obliczen: {elapsed:.3f}s\n", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(
        description='Szukanie optymalnych tras w systemie transportu publicznego',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
PRZYKŁADY UŻYCIA:

  1. Dijkstra (minimalizacja czasu):
     python main.py dijkstra --start 1413291 --end 1413182 --time 08:00

  2. A* z minimalizacją czasu:
     python main.py astar --start 1413291 --end 1413182 --criteria t --time 08:00

  3. A* z minimalizacją przesiadek:
     python main.py astar --start 1413291 --end 1413182 --criteria p --time 08:00

  4. Tabu Search - odwiedzenie przystanków (minimalizacja czasu):
     python main.py tabu_search --start 1413291 --targets "1413182;1413145;1413141" --criteria t --time 08:00

  5. Tabu Search - odwiedzenie przystanków (minimalizacja przesiadek):
     python main.py tabu_search --start 1413291 --targets "1413182;1413145" --criteria p --time 10:30
        """
    )
    
    subparsers = parser.add_subparsers(dest='mode', help='Algorytm do użycia')
    
    # Królestwa północy - Dijkstra (mam nadzieję, że bez złamanego kolana)
    dijkstra_parser = subparsers.add_parser('dijkstra', help='Szukanie ścieżki A→B (minimalizacja czasu)')
    dijkstra_parser.add_argument('--start', required=True, help='ID przystanku początkowego A')
    dijkstra_parser.add_argument('--end', required=True, help='ID przystanku końcowego B')
    dijkstra_parser.add_argument('--date', required=False, help='Data (format YYYYMMDD, domyślnie dzisiaj)')
    dijkstra_parser.add_argument('--time', required=True, help='Czas rozpoczęcia (format HH:MM)')
    
    # Astar
    astar_parser = subparsers.add_parser('astar', help='Szukanie ścieżki A→B (A* z heurystyką)')
    astar_parser.add_argument('--start', required=True, help='ID przystanku początkowego A')
    astar_parser.add_argument('--end', required=True, help='ID przystanku końcowego B')
    astar_parser.add_argument('--criteria', required=True, choices=['t', 'p'],
                              help='t = minimalizacja czasu, p = minimalizacja przesiadek')
    astar_parser.add_argument('--date', required=False, help='Data (format YYYYMMDD, domyślnie dzisiaj)')
    astar_parser.add_argument('--time', required=True, help='Czas rozpoczęcia (format HH:MM)')
    
    # Tabu Search
    tabu_parser = subparsers.add_parser('tabu_search', help='Odwiedzenie listy przystanków (TSP)')
    tabu_parser.add_argument('--start', required=True, help='ID przystanku początkowego A')
    tabu_parser.add_argument('--targets', required=True, help='Lista przystanków oddzielona średnikami (A;B;C)')
    tabu_parser.add_argument('--criteria', required=True, choices=['t', 'p'],
                             help='t = minimalizacja czasu, p = minimalizacja przesiadek')
    tabu_parser.add_argument('--date', required=False, help='Data (format YYYYMMDD, domyślnie dzisiaj)')
    tabu_parser.add_argument('--time', required=True, help='Czas rozpoczęcia (format HH:MM)')
    
    args = parser.parse_args()
    
    if not args.mode:
        parser.print_help()
        sys.exit(0)
    
    start_time = parse_time(args.time)
    
    if args.date:
        date_str = parse_date(args.date)
    else:
        today = datetime.datetime.now()
        date_str = today.strftime('%Y%m%d')
    
    if args.mode == 'dijkstra':
        run_dijkstra_mode(args.start, args.end, start_time, date_str)
    elif args.mode == 'astar':
        run_astar_mode(args.start, args.end, args.criteria, start_time, date_str)
    elif args.mode == 'tabu_search':
        run_tabu_search_mode(args.start, args.targets, args.criteria, start_time, date_str)

if __name__ == '__main__':
    main()
