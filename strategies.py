from abc import ABC, abstractmethod
from collections import defaultdict
from itertools import chain
from typing import TYPE_CHECKING, Iterator, Mapping, Dict

if TYPE_CHECKING:
    from client import Client
    from swarm import Swarm


class Strategy(ABC):
    def __init__(self, swarm: 'Swarm', client: 'Client'):
        self._swarm = swarm
        self._client = client

    def init_peers(self, num_peers: int) -> Iterator['Client']:
        yield from self._swarm.get_random_grouping(num_peers, (self._client,))

    def willing_to_give_to(self, client: 'Client') -> bool:
        return True

    @abstractmethod
    def generate_new_peers(self, old_peers: Mapping['Client', int], current_client: 'Client') -> Iterator['Client']:
        raise NotImplementedError


class NoStrategy(Strategy):
    def generate_new_peers(self, old_peers: Mapping['Client', int], current_client: 'Client') -> Iterator['Client']:
        yield from old_peers.keys()


class RandomStrategy(Strategy):
    def generate_new_peers(self, old_peers: Mapping['Client', int], current_client: 'Client') -> Iterator['Client']:
        return self._swarm.get_random_grouping(len(old_peers), {current_client})


class DropZeros(Strategy):
    def generate_new_peers(self, old_peers: Mapping['Client', int], current: 'Client') -> Iterator['Client']:
        keep = [k for k, v in old_peers.items() if v != 0]
        new = self._swarm.get_random_grouping(len(old_peers) - len(keep), set((old_peers.keys()) - set(keep)) | {current})
        return chain(keep, new)


class DropBottomHalf(Strategy):
    def generate_new_peers(self, old_peers: Mapping['Client', int], current_client: 'Client') -> Iterator['Client']:
        sorted_keys = [k for k, v in sorted(old_peers.items(), key= lambda kv: kv[1], reverse=True)]
        top_half = sorted_keys[:len(sorted_keys) // 2]
        bottom_half = self._swarm.get_random_grouping(len(sorted_keys) - (len(sorted_keys) // 2), set(old_peers.keys()) | {current_client})
        yield from chain(top_half, bottom_half)


class OptimisticUnchoking(Strategy):
    def __init__(self, swarm: 'Swarm', client: 'Client'):
        super().__init__(swarm, client)
        self._times_unchoked: Dict[Client, int] = {}
        self._is_choked: Dict[Client, bool] = defaultdict(lambda : True)

    def willing_to_give_to(self, client: 'Client') -> bool:
        return self._is_choked[client]


    def generate_new_peers(self, old_peers: Mapping['Client', int], current_client: 'Client') -> Iterator['Client']:
        pass


