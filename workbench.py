from itertools import chain

from client import Client
from extra_types import Points
from model import Model
from strategies import RandomStrategy, DropZeros, NoStrategy, DropBottomHalf
from swarm import Swarm
from random import seed

seed(0)

swarm = Swarm()

strategy = NoStrategy

iterations = 100
max_up = 100
max_down = 100
peer_size = 10

num_good_clients = 50
num_free_riders = 50
num_clients = num_good_clients + num_free_riders

all_agents = chain(
    (Client(
        strat=strategy,
        up=Points(max_up),
        down=Points(max_down),
        peer_size=peer_size,
        swarm=swarm,
        is_free_rider=False
    ) for _ in range(num_good_clients)),
    (Client(
        strat=strategy,
        up=Points(max_up // 4),
        down=Points(max_down),
        peer_size=peer_size,
        swarm=swarm,
        is_free_rider=True
    ) for _ in range(num_free_riders))
)

[swarm.join(x) for x in all_agents]

data = Model.run(swarm, iterations)

good_guys = [
    tuple(x.amount_acquired for x in y if not x.free_rider) for y in data
]

bad_guys = [
    tuple(x.amount_acquired for x in y if x.free_rider) for y in data
]

all_guys = [
    tuple(x.amount_acquired for x in y) for y in data
]

import matplotlib.pyplot as plt
import numpy as np

#plt.scatter(y=list(chain.from_iterable(fixed_data)), x=[[x]*num_good_clients for x in range(iterations)], alpha=.1)
plt.plot(np.mean(good_guys, axis=1), 'r')
plt.plot(np.mean(bad_guys, axis=1), 'b')
plt.plot(np.mean(all_guys, axis=1), 'g')
plt.show()