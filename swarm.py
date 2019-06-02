from random import sample
from typing import Set, Iterator, Collection, Optional

from client import Client


class Swarm:
    def __init__(self):
        self._clients: Set[Client] = set()

    def all_clients(self) -> Collection[Client]:
        return self._clients

    def join(self, client: Client) -> None:
        self._clients.add(client)

    @property
    def saturated_clients(self) -> Collection[Client]:
        return [x for x in self._clients if x.is_saturated]

    def swap_bad_clients(self, me: Client, clients: Collection[Client], ignore: Collection[Client]):
        for c in clients:
            c.remove_peer(me)
        yield from self.get_random_grouping(len(clients), ignore, me)

    def get_random_grouping(self, n: int, ignore: Collection[Client], requestor: Client) -> Iterator[Client]:
        possible_agents = self._clients - (set(ignore) | {requestor}) - set(self.saturated_clients)
        if len(possible_agents) <= n:
            grouping = possible_agents
        else:
            grouping = sample(possible_agents, n)
        for peer in grouping:
            peer.add_peer(requestor)
            yield peer

    def get_one_random(self, ignore: Collection[Client], requestor: Client) -> Optional[Client]:
        return next(self.get_random_grouping(1, ignore, requestor), None)
