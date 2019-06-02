from abc import ABC, abstractmethod
from collections import defaultdict
from itertools import chain
from statistics import mean
from typing import TYPE_CHECKING, Iterator, Mapping, Dict, Collection, List, Optional

from attr import dataclass

if TYPE_CHECKING:
    from client import Client
    from swarm import Swarm


class Strategy(ABC):
    def __init__(self, swarm: 'Swarm', client: 'Client', iterations: int):
        self._swarm = swarm
        self._client = client
        self._iterations = iterations

    def init_peers(self, num_peers: int) -> Iterator['Client']:
        current_peers = self._client.peers
        if num_peers <= len(current_peers):
            new_peers = ()
        else:
            new_peers = self._swarm.get_random_grouping(num_peers - len(current_peers), current_peers, self._client)
        yield from current_peers
        yield from new_peers

    def willing_to_give_to(self, client: 'Client') -> bool:
        return True

    @abstractmethod
    def generate_new_peers(self, old_peers: Mapping['Client', int], current_iteration) -> Iterator['Client']:
        raise NotImplementedError


class NoStrategy(Strategy):
    def generate_new_peers(self, old_peers: Mapping['Client', int], current_iteration) -> Iterator['Client']:
        yield from old_peers.keys()


class RandomStrategy(Strategy):
    def generate_new_peers(self, old_peers: Mapping['Client', int], current_iteration) -> Iterator['Client']:
        return self._swarm.swap_bad_clients(self._client, old_peers, ())


class DropZeros(Strategy):
    def generate_new_peers(self, old_peers: Mapping['Client', int], current_iteration) -> Iterator['Client']:
        keep = [k for k, v in old_peers.items() if v != 0]
        bad = [p for p in old_peers.keys() if p not in keep]

        new = self._swarm.swap_bad_clients(self._client, bad, keep)
        return chain(keep, new)


class DropBottomHalf(Strategy):
    def generate_new_peers(self, old_peers: Mapping['Client', int], current_iteration) -> Iterator['Client']:
        sorted_keys = [k for k, v in sorted(old_peers.items(), key=lambda kv: kv[1], reverse=True)]
        top_half = sorted_keys[:len(sorted_keys) // 2]

        bottom_half = self._swarm.swap_bad_clients(self._client, sorted_keys[len(sorted_keys) // 2:], top_half)
        yield from chain(top_half, bottom_half)


class HistEntry:
    def __init__(self, iterations):
        self.contributions: List[int] = [0] * iterations
        self.added: int = -1

    def __repr__(self):
        return f'{self.contributions}, {self.added}'

class OptimisticUnchoking(Strategy):
    def __init__(self, swarm: 'Swarm', client: 'Client', iterations: int):
        super().__init__(swarm, client, iterations)
        self._times_unchoked: Dict[Client, int] = defaultdict(int)
        self._is_choked: Dict[Client, bool] = defaultdict(lambda: True)
        self._current_round = 0
        self._historic_contributions: Mapping[Client, HistEntry] = defaultdict(lambda: HistEntry(iterations))

    def willing_to_give_to(self, client: 'Client') -> bool:
        return not self._is_choked[client]

    def choose_next_person(self, current_peers: Collection['Client'], current_iteration) -> Optional['Client']:
        return self._swarm.get_one_random(current_peers, self._client)

    def choke(self, peer: 'Client'):
        self._is_choked[peer] = True

    def unchoke(self, peer: 'Client', current_iteration: int) -> None:
        self._is_choked[peer] = False
        self._times_unchoked[peer] += 1
        self._historic_contributions[peer].added = current_iteration

    def init_peers(self, num_peers: int) -> Iterator['Client']:
        for peer in super().init_peers(num_peers):
            self.unchoke(peer, 0)
            yield peer

    @property
    def neighbors(self):
        return set(self._swarm.all_clients()) - {self._client}

    def generate_new_peers(self, old_peers: Mapping['Client', int], current_iteration) -> Iterator['Client']:
        for peer in list(old_peers.keys()):
            self._historic_contributions[peer].contributions[current_iteration] = old_peers[peer]
            hc = self._historic_contributions[peer]

            if current_iteration < 3:
                yield from old_peers.keys()
                break

            if hc.added <= current_iteration - 3:
                if all([x == 0 for x in hc.contributions[:-3]]):
                    peer.remove_peer(self._client)
                    self._client.remove_peer(peer)
                    self.choke(peer)
                    new = self.choose_next_person(old_peers.keys(), current_iteration)
                    if new is not None:
                        new.add_peer(self._client)
                        self._client.add_peer(new)
                        self.unchoke(new, current_iteration)
                        yield new

                    yield from (old_peers.keys() - {peer})
                    break
        else:
            yield from old_peers.keys()

class GainValueUnchoking(OptimisticUnchoking):

    def _N(self, j: 'Client') -> int:
        return self._times_unchoked[j]

    def _n(self, j: 'Client') -> int:
        return sum(1 for x in self._historic_contributions[j].contributions if x != 0)

    def _u(self, j: 'Client', current_iteration: int) -> float:
        return mean(self._historic_contributions[j].contributions[self._historic_contributions[j].added: current_iteration] or [0])

    def _Umax(self, current_iteration: int) -> float:
        return max(self._u(x, current_iteration) for x in self.neighbors)

    def _G(self, j: 'Client', current_iteration: int):
        if self._n(j) > 0:
            return self._u(j, current_iteration) * self._n(j) / self._N(j)
        else:
            return self._Umax(current_iteration) / (self._N(j) + 1)

    def choose_next_person(self, current_peers: Collection['Client'], current_iteration) -> 'Client':
        return next((a for a in (k for k, v in sorted({x: self._G(x, current_iteration) for x in self.neighbors}.items(), key=lambda kv: kv[1], reverse=True)) if not a.is_saturated), None)

class DemeritChoking(OptimisticUnchoking):
    # timeout = 6 iterations
    def choose_next_person(self, current_peers: Collection['Client'], current_iteration) -> Optional['Client']:
        return next((k for k, v in self._historic_contributions.items() if current_iteration >= 6 and sum(1 for x in v.contributions[current_iteration-6: current_iteration] if x != 0) < 4 and not k.is_saturated), None)

