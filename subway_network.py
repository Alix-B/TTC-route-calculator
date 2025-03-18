import networkx as nx
import random


TTC = nx.DiGraph()


def generate_valid_random_path(graph, start=None):
    """
    Generates a random path through the subway system.

    :param graph: NetworkX graph of the TTC system
    :param start: (Optional) Starting station; defaults to a random valid node.
    :return: A list of stations.
    """
    if start is None:
        start = random.choice(list(graph.nodes))  # Pick a random starting station

    visited = {start}
    path = [start]
    current_stop = start

    while len(visited) < len(graph.nodes):
        neighbors = list(graph.neighbors(current_stop))

        unvisited_neighbors = [n for n in neighbors if n not in visited]

        if unvisited_neighbors:
            next_stop = random.choice(unvisited_neighbors)  # Prefer unvisited stations
        else:
            next_stop = random.choice(neighbors)

        path.append(next_stop)
        visited.add(next_stop)
        current_stop = next_stop

    return path


# Base travel times (https://whitelabel.triplinx.ca/)
edges = [
    ("VMC", "Pioneer Village", 4, 1), ("Pioneer Village", "VMC", 4, 1),
    ("Pioneer Village", "Finch-West", 4, 1), ("Finch-West", "Pioneer Village", 4, 1),
    ("Finch-West", "Sheppard-West", 5, 1), ("Sheppard-West", "Finch-West", 5, 1),
    ("Sheppard-West", "Eglinton-West", 10, 1), ("Eglinton-West", "Sheppard-West", 10, 1),
    ("Eglinton-West", "Spadina", 9, 1), ("Spadina", "Eglinton-West", 9, 1),
    ("Spadina", "St George", 2, 1), ("St George", "Spadina", 2, 1),
    ("St George", "St Patrick", 4, 1), ("St Patrick", "St George", 4, 1),
    ("St Patrick", "Union", 4, 1), ("Union", "St Patrick", 4, 1),
    ("Union", "Dundas", 4, 1), ("Dundas", "Union", 4, 1),
    ("Dundas", "Bloor-Yonge", 4, 1), ("Bloor-Yonge", "Dundas", 4, 1),
    ("Bloor-Yonge", "Eglinton", 9, 1), ("Eglinton", "Bloor-Yonge", 9, 1),
    ("Eglinton", "Sheppard-Yonge", 10, 1), ("Eglinton", "Sheppard-Yonge", 10, 1),
    ("Sheppard-Yonge", "Finch", 5, 1), ("Finch", "Sheppard-Yonge", 5, 1),
    ("Kipling", "Spadina", 23, 2), ("Spadina", "Kipling", 23, 2),
    ("St George", "Bay", 3, 2), ("Bay", "St George", 3, 2),
    ("Bay", "Bloor-Yonge", 1, 2), ("Bloor-Yonge", "Bay", 1, 2),
    ("Bloor-Yonge", "Kennedy", 24, 2), ("Kennedy", "Bloor-Yonge", 24, 2),
    ("Sheppard-Yonge", "Don Mills", 8, 4), ("Don Mills", "Sheppard-Yonge", 8, 4),
    ("Kennedy", "Don Mills", 50, 5), ("Don Mills", "Kennedy", 50, 5),   # 985 Sheppard East Express
    ("Kennedy", "Finch", 65, 5), ("Finch", "Kennedy", 65, 5),   # Bus 939(B) Finch Express
    ("Finch", "Finch-West", 20, 6), ("Finch-West", "Finch", 20, 6), # Street car 36 Finch West
    ("Finch", "Pioneer Village", 32, 5), ("Pioneer Village", "Finch", 32, 5),   # Bus 960 Steels West Express
    ("Sheppard-Yonge", "Sheppard-West", 15, 5), ("Sheppard-West", "Sheppard-Yonge", 15, 5)  # Bus 984(A) Sheppard West Express
]

# Add edges
for u, v, w, l in edges:
    TTC.add_edge(u, v, time=w, line=l)

# Number of RSZ between stations (There are currently 11 Reduced Speed Zones across Lines 1 and 2.)
reduced_speed_zones = {
    ("Kipling", "Spadina"): 1,
    ("Bloor-Yonge", "Kennedy"): 2,
    ("Bloor-Yonge", "Eglinton"): 2,
    ("Eglinton", "Bloor-Yonge"): 1,
    ("Eglinton-West", "Sheppard-West"): 2,
    ("Sheppard-West", "Eglinton-West"): 2
}

# Apply slow zones
for (u, v), rsz in reduced_speed_zones.items():
    print(f"Implementing {rsz} reduced speed zone{'s' * (rsz > 1)} from {u} to {v}")

    # One reduced speed zone can add approximately one to three minutes to a subway trip.
    time_loss = 0

    TTC[u][v]["time"] += rsz * time_loss

print(TTC.nodes())

fastest = 500
best_route = []
best_swaps = 15

for i in range(100_000):

    shortest_path = generate_valid_random_path(TTC)

    length = 0
    eols = 0
    direction_changes = 0
    line_changes = 0
    busses = 0
    street_cars = 0

    end_of_line_stations = {"VMC", "Finch", "Don Mills", "Kipling", "Kennedy"}
    eol_penalty = 0
    direction_swap_penalty = 0
    line_swap_penalty = 0

    for stop in range(len(shortest_path) - 1):
        current_station = shortest_path[stop]
        next_station = shortest_path[stop + 1]

        # Add base travel time
        length += TTC[current_station][next_station]["time"]

        if stop < len(shortest_path) - 2:
            next_next_station = shortest_path[stop + 2]

            current_line = TTC.get_edge_data(current_station, next_station).get("line")
            next_line = TTC.get_edge_data(next_station, next_next_station).get("line")

            if current_station == next_next_station:  # Check for turnaround
                if next_station in end_of_line_stations:  # Check if at EOL
                    length += eol_penalty
                    eols += 1
                else:
                    length += direction_swap_penalty
                    direction_changes += 1

            if current_line != next_line:  # Check if switching lines (including bus)
                length += line_swap_penalty

                if next_line == 5:  # Bus
                    busses += 1
                elif next_line == 6:  # Streetcar
                    street_cars += 1
                else:
                    line_changes += 1

    shortest_path.append([eols, direction_changes, line_changes, busses, street_cars])

    if length < fastest:
        best_route = shortest_path
        fastest = length
        print(f"New best route found with a time of {fastest} ({fastest // 60} hours and {fastest % 60} minutes)")
        print(best_route[:-1])
        print(
            f"End of lines: {best_route[-1][0]}, Direction changes: {best_route[-1][1]}, Line changes: {best_route[-1][2]}, Busses: {best_route[-1][3]}, Streetcars: {best_route[-1][4]}")
