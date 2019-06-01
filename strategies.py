from abc import ABC, abstractmethod
from itertools import chain
from typing import TYPE_CHECKING, Iterator, Mapping


if TYPE_CHECKING:
    from client import Client
    from swarm import Swarm


class Strategy(ABC):
    def __init__(self, swarm: 'Swarm', client: 'Client'):
        self._swarm = swarm
        self._client = client

    def init_peers(self, num_peers: int) -> Iterator['Client']:
        yield from self._swarm.get_random_grouping(num_peers, (self._client,))

    @abstractmethod
    def generate_new_peers(self, old_peers: Mapping['Client', int], current_client: 'Client') -> Iterator['Client']:
        raise NotImplementedError


class NoStrategy(Strategy):
    def generate_new_peers(self, old_peers: Mapping['Client', int], current_client: 'Client') -> Iterator['Client']:
        yield from old_peers.keys()


class RandomStrategy(Strategy):
    def generate_new_peers(self, old_peers: Mapping['Client', int], current_client: 'Client') -> Iterator['Client']:
        return self._swarm.get_random_grouping(len(old_peers), {current_client})


class Testing(Strategy):
    def generate_new_peers(self, old_peers: Mapping['Client', int], current: 'Client') -> Iterator['Client']:
        keep = [k for k, v in old_peers.items() if v != 0]
        new = self._swarm.get_random_grouping(len(old_peers) - len(keep), set((old_peers.keys()) - set(keep)) | {current})
        return chain(keep, new)
