import os
from itertools import chain
from json import dumps
from random import seed
from typing import Tuple, Type, Iterable

from client import Client
from extra_types import Points, no_points
from model import Model
from strategies import DropZeros, NoStrategy, OptimisticUnchoking, GainValueUnchoking, DemeritChoking, Strategy
from swarm import Swarm
from multiprocessing import Pool

"""
For non-BitTorrent
    two lines
    x = iterations
    y1 = #free riders
    y2 = #non-freeriders
    at each iteration, update proportions based on happiness of populations


For BitTorrent strats
    same as above, uses choking stuff
"""

Task = Tuple[Type[Strategy], int, int, int, int, Points, Points]


def run_task(t: Task):
    strategy, iterations, num_good_clients, num_free_riders, peer_size, max_up, max_down = t
    swarm = Swarm()
    all_agents = chain(
        (Client(
            strat=strategy,
            up=Points(max_up),
            down=Points(max_down),
            peer_size=peer_size,
            swarm=swarm,
            iterations=iterations
        ) for _ in range(num_good_clients)),
        (Client(
            strat=strategy,
            up=no_points,
            down=Points(max_down),
            peer_size=peer_size,
            swarm=swarm,
            iterations=iterations
        ) for _ in range(num_free_riders))
    )

    [swarm.join(x) for x in all_agents]

    OUTPUT_FILE = f"./results/{strategy.__name__}/{iterations}_{num_good_clients}_{num_free_riders}_{peer_size}_{max_up}_{max_down}.json"
    if not os.path.isdir(os.path.dirname(OUTPUT_FILE)):
        os.makedirs(os.path.dirname(OUTPUT_FILE))
    with open(OUTPUT_FILE, 'w') as f:
        f.write(dumps(
            {
                'metadata': {
                    'strategy': strategy.__name__,
                    'iterations': iterations,
                    'max_up': max_up,
                    'max_down': max_down,
                    'starting_good_clients': num_good_clients,
                    'starting_bad_clients': num_free_riders,
                    'peer_size': peer_size
                },
                'data': tuple(
                    chain.from_iterable((x.to_json(iteration) for x in y) for iteration, y in enumerate(Model.run(swarm, iterations))))
            }
        ))


seed(0)

# Strategy, iterations, #good clients, #bad clients, peer_size, max_up, max_down
tasks: Iterable[Task] = [
    (DropZeros, 50, 80, 20, 4, Points(100), Points(100)),
    (NoStrategy, 50, 80, 20, 4, Points(100), Points(100)),
    (OptimisticUnchoking, 50, 80, 20, 4, Points(100), Points(100)),
    (GainValueUnchoking, 50, 80, 20, 4, Points(100), Points(100)),
    (DemeritChoking, 50, 80, 20, 4, Points(100), Points(100)),
    (Strategy, 50, 80, 20, 4, Points(100), Points(100)),
]
with Pool() as p:
    p.map(run_task, tasks)
