import numpy as np

from fastapi import FastAPI
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from utils import (
    dist,
    create_data_model,
    extract_solution
)
from scipy.spatial.distance import pdist, squareform

class Locations(BaseModel):
    coordinates: list[dict[str, float]]
    n_vehicles: int

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Hello World"}


@app.post("/")
def calculate_route(locations: Locations):

    lat_long = [list(loc.values()) for loc in locations.coordinates]

    distances = pdist(lat_long, metric=dist)
    distance_matrix = squareform(distances)

    data = create_data_model(
        np.array(distance_matrix).astype(int),
        num_vehicles=locations.n_vehicles
    )

    manager = pywrapcp.RoutingIndexManager(
        len(data["distance_matrix"]),
        data["num_vehicles"],
        data["depot"]
    )

    def distance_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data["distance_matrix"][from_node][to_node]

    routing = pywrapcp.RoutingModel(manager)

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add Distance constraint.
    dimension_name = "Distance"
    routing.AddDimension(
        transit_callback_index,
        0, # no slack
        200_000, # vehicle maximum travel distance
        True, # start cumul to zero
        dimension_name,
    )
    distance_dimension = routing.GetDimensionOrDie(dimension_name)
    distance_dimension.SetGlobalSpanCostCoefficient(100)

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    solution = routing.SolveWithParameters(search_parameters)

    if solution:
        indexes = extract_solution(data, manager, routing, solution)
    
    route_coordinates = {vehicle_id: [] for vehicle_id in range(data["num_vehicles"])}
    
    for vehicle_id, nodes in indexes.items():
        for node in nodes:
            route_coordinates[vehicle_id].append(lat_long[node])

    return route_coordinates