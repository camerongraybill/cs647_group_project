from random import shuffle
from time import time
from typing import Tuple, List, Sequence, TypeVar, Iterable, Iterator

from client import Result
from swarm import Swarm

T = TypeVar('T')


def random_iteration(iterable: Iterable[T]) -> Iterator[T]:
    l = list(iterable)
    shuffle(l)
    yield from l


def do_assertions(all_agents):
    for client in all_agents:
        for p in client.peers:
            assert (client in p.peers)
        assert (sum(1 for x in all_agents if client in x.peers) <= client.peer_size)


class Model:

    @staticmethod
    def run(swarm: Swarm, iterations: int) -> Iterator[Iterator[Result]]:
        all_agents = list(swarm.all_clients())
        [x.init_peers() for x in all_agents]

        for c in range(iterations):
            print("Iteration", c)

            do_assertions(all_agents)

            remaining_agents = set(all_agents)
            while remaining_agents:
                # filter out the ones that don't want content
                remaining_agents -= {x for x in all_agents if not x.wants_content()}
                # Iterate in random order
                for agent in random_iteration(remaining_agents):
                    # Iterate all peers of that agent in random order
                    for peer in random_iteration(agent.peers):
                        if peer.ask_for_content(agent):  # If they gave us content
                            agent.give_content(peer)
                            break
                    else:
                        # None of the peers gave them something
                        remaining_agents.remove(agent)
            yield (x.get_state() for x in all_agents)

            [x.reset_values() for x in all_agents]

            do_assertions(all_agents)
            # Find new peers
            print("--before--")
            [x.before_reset() for x in random_iteration(all_agents)]
            print("--reset--")
            [x.reset(c) for x in random_iteration(all_agents)]
            print("--after--")
            [x.after_reset(c) for x in random_iteration(all_agents)]
            do_assertions(all_agents)
