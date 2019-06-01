from itertools import chain
from random import shuffle
from typing import Callable, Tuple, List, Type

from extra_types import Points
from swarm import Swarm
from client import Client, Result
from strategies import Strategy
from utils import repeat_forever


def main(num_free_riders: int, num_good_clients: int, strategy: Type[Strategy], max_up: Points, max_down: Points, iterations: int, peer_size: int):
    output: List[Tuple[Result, ...]] = []

    swarm = Swarm()

    all_agents = list(chain(
        (Client(
            strat=strategy,
            up=max_up,
            down=max_down,
            peer_size=peer_size,
            swarm=swarm,
            is_free_rider=False
        ) for _ in range(num_good_clients)),
        (Client(
            strat=strategy,
            up=Points(max_up // 4),
            down=max_down,
            peer_size=peer_size,
            swarm=swarm,
            is_free_rider=True
        ) for _ in range(num_free_riders))
    ))

    [swarm.join(x) for x in all_agents]

    [x.init_peers() for x in all_agents]

    for _ in range(iterations):
        # TODO: Shuffle ordering of agents?
        remaining_agents = set(all_agents)
        idx_counter = repeat_forever(range(peer_size))
        while remaining_agents:
            idx = idx_counter.__next__()
            rem_agents_copy = list(remaining_agents)
            shuffle(rem_agents_copy)
            for agent in rem_agents_copy:
                if agent.wants_content():
                    peers = list(agent.peers)
                    for peer in chain(peers[idx:], peers[:idx]):
                        if peer.ask_for_content():  # If they gave us content
                            agent.give_content(peer)
                            break
                    else:
                        remaining_agents.remove(agent)
                else:
                    remaining_agents.remove(agent)
        output.append(
            tuple(x.get_state() for x in all_agents)
        )

        [x.reset() for x in all_agents]

    return output
