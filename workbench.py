from itertools import chain
from random import seed

from client import Client
from extra_types import Points, no_points
from model import Model
from strategies import DropZeros, NoStrategy, OptimisticUnchoking, GainValueUnchoking, DemeritChoking
from swarm import Swarm
from json import dumps, loads
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

OUTPUT_FILE = "output.json"

seed(0)

swarm = Swarm()

strategy = NoStrategy

iterations = 30
max_up = 100
max_down = 100

num_good_clients = 80
num_free_riders = 20
num_clients = num_good_clients + num_free_riders
peer_size = 4

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

data = Model.run(swarm, iterations)





# plt.scatter(y=list(chain.from_iterable(fixed_data)), x=[[x]*num_good_clients for x in range(iterations)], alpha=.1)



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
            'data': tuple(chain.from_iterable((x.to_json(iteration) for x in y) for iteration, y in enumerate(data)))
        }
    ))


