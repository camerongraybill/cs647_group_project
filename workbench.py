from itertools import chain
from random import seed

from client import Client
from extra_types import Points, no_points
from model import Model
from strategies import DropZeros, NoStrategy, OptimisticUnchoking, GainValueUnchoking, DemeritChoking
from swarm import Swarm

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

seed(0)

swarm = Swarm()

strategy = DemeritChoking

iterations = 20
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

good_guys = [
    tuple(x.amount_acquired for x in y if not x.free_rider) if sum(int(not x.free_rider) for x in y) else (0,) for y in data
]

bad_guys = [
    tuple(x.amount_acquired for x in y if x.free_rider) if sum(int(x.free_rider) for x in y) else (0,) for y in data
]

all_guys = [
    tuple(x.amount_acquired for x in y) for y in data
]

import matplotlib.pyplot as plt
import numpy as np

# plt.scatter(y=list(chain.from_iterable(fixed_data)), x=[[x]*num_good_clients for x in range(iterations)], alpha=.1)
plt.plot([len(x) for x in good_guys], 'g')
plt.plot([len(x) for x in bad_guys], 'r')
#plt.plot([len(x) for x in all_guys], 'b')
plt.show()
