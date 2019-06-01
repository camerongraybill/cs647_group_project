from random import sample
from typing import Set, Iterator, Collection

from client import Client


class Swarm:
    def __init__(self):
        self._clients: Set[Client] = set()

    def all_clients(self) -> Collection[Client]:
        return self._clients

    def join(self, client: Client) -> None:
        self._clients.add(client)

    def get_random_grouping(self, n: int, ignore: Collection[Client]) -> Iterator[Client]:
        possible_agents = self._clients - set(ignore)
        yield from sample(possible_agents, n)
