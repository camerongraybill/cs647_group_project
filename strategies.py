from abc import ABC, abstractmethod
from collections import defaultdict
from itertools import chain
from typing import TYPE_CHECKING, Iterator, Mapping, Dict, Collection, List, Optional, Set, Tuple

import numpy as np

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
            new_peers = list(
                self._swarm.get_random_grouping(num_peers - len(current_peers), current_peers, self._client))
        for peer in new_peers:
            self._client.add_peer(peer)
            peer.add_peer(self._client)
            yield peer
        yield from current_peers

    def after_reset(self, current_iteration: int):
        pass

    def willing_to_give_to(self, client: 'Client') -> bool:
        return True

    def pre_generate(self, old_peers: Dict['Client', int], current_iteration: int) -> Tuple[
        Set['Client'], Set['Client']]:
        to_remove = []
        for peer in old_peers.keys():
            if self._client not in peer.peers:
                to_remove.append(peer)
        for peer in self._client.peers:
            if self._client not in peer.peers:
                self._client.remove_peer(peer)
        for removed in to_remove:
            del old_peers[removed]
        clients_connecting_to_us = {x for x in self._swarm.all_clients() if self._client in x.peers}
        # return the new clients
        return clients_connecting_to_us - set(old_peers.keys()), set(to_remove)

    @abstractmethod
    def generate_new_peers(self, old_peers: Mapping['Client', int], current_iteration, new_peers: Set['Client'],
                           removed_in_iteration: Set['Client']) -> Iterator['Client']:
        raise NotImplementedError


class NoStrategy(Strategy):
    def generate_new_peers(self, old_peers: Mapping['Client', int], current_iteration, new_peers: Set['Client'],
                           removed_in_iteration: Set['Client']) -> Iterator['Client']:
        def fun():
            yield from old_peers.keys()
            yield from new_peers
        yield from (a for a in fun() if a not in removed_in_iteration)


class RandomStrategy(Strategy):
    def generate_new_peers(self, old_peers: Mapping['Client', int], current_iteration, new_peers: Set['Client'],
                           removed_in_iteration: Set['Client']) -> Iterator['Client']:
        for peer in old_peers.keys():
            self._client.remove_peer(peer)
        for peer in self._swarm.swap_bad_clients(self._client, old_peers, ()):
            self._client.add_peer(peer)
            peer.add_peer(self._client)
            yield peer
        yield from new_peers


class DropZeros(Strategy):
    def generate_new_peers(self, old_peers: Mapping['Client', int], current_iteration, new_peers: Set['Client'],
                           removed_in_iteration: Set['Client']) -> Iterator['Client']:

        keep = [k for k, v in old_peers.items() if v != 0 and k not in removed_in_iteration] + list(new_peers)
        bad = [p for p, v in old_peers.items() if v == 0 and p not in removed_in_iteration]

        for peer in bad:
            self._client.remove_peer(peer)
            peer.remove_peer(self._client)

        new = list(self._swarm.swap_bad_clients(self._client, bad, keep + list(removed_in_iteration)))
        for peer in new:
            self._client.add_peer(peer)
            peer.add_peer(self._client)
        yield from keep
        yield from new


class HistEntry:
    def __init__(self, iterations, added):
        self.contributions: List[int] = [0] * iterations
        self.added: int = added

    def __repr__(self):
        return f'{self.contributions}, {self.added}'


class OptimisticUnchoking(Strategy):
    timeout = 3

    def __init__(self, swarm: 'Swarm', client: 'Client', iterations: int):
        super().__init__(swarm, client, iterations)
        self._times_unchoked: Dict[Client, int] = defaultdict(int)
        self._is_choked: Dict[Client, bool] = {}
        self._current_round = 0
        self._max_iterations = iterations
        self._historic_contributions: Dict[Client, HistEntry] = {}

    def willing_to_give_to(self, client: 'Client') -> bool:
        if client in self._is_choked:
            return not self._is_choked[client]
        return False

    def choose_next_person(self, current_peers: Collection['Client'], blacklist: Collection['Client'],
                           current_iteration) -> Optional['Client']:
        return self._swarm.get_one_random(set(chain(current_peers, blacklist)), self._client)

    def choke(self, peer: 'Client', remove=True):
        print(f"{self._client} choking {peer}")
        self._is_choked[peer] = True
        if remove:
            self._client.remove_peer(peer)
            peer.remove_peer(self._client)

    def unchoke(self, peer: 'Client', current_iteration: int, add: bool = True) -> None:
        print(f"{self._client} un_choking {peer}")
        self._is_choked[peer] = False
        self._times_unchoked[peer] += 1
        if peer not in self._historic_contributions:
            self._historic_contributions[peer] = HistEntry(self._max_iterations, current_iteration)
        self._historic_contributions[peer].added = current_iteration
        if add:
            self._client.add_peer(peer)
            peer.add_peer(self._client)

    def init_peers(self, num_peers: int) -> Iterator['Client']:
        new_peers = list(super().init_peers(num_peers))
        for peer in new_peers:
            self.unchoke(peer, 0, False)
            yield peer

    @property
    def neighbors(self):
        return set(self._swarm.all_clients()) - {self._client}

    def pre_generate(self, old_peers: Dict['Client', int], current_iteration: int) -> Tuple[
        Set['Client'], Set['Client']]:
        # Save contributions from this round
        for peer in list(old_peers.keys()):
            self._historic_contributions[peer].contributions[current_iteration] = old_peers[peer]
        return super().pre_generate(old_peers, current_iteration)

    @property
    def choked(self) -> Set['Client']:
        return {x for x, y in self._is_choked.items() if y is True}

    def generate_new_peers(self, old_peers: Mapping['Client', int], current_iteration, new_peers: Set['Client'],
                           removed_in_iteration: Set['Client']) -> Iterator['Client']:
        # choke the guys that suck, but only the first one
        newly_choked = set()
        for peer in old_peers.keys():
            hc = self._historic_contributions[peer]

            if hc.added <= (current_iteration - self.timeout):
                # If we did not get any contributions in the last {timeout} rounds
                recent_contributions = hc.contributions[current_iteration - self.timeout + 1:current_iteration + 1]
                if all(x == 0 for x in recent_contributions):
                    self.choke(peer)
                    newly_choked = {peer}
                    break


        # If we want more people, try to find more people
        current_peers = set((old_peers.keys() | new_peers) - removed_in_iteration) - self.choked
        if len(current_peers) < self._client.peer_size:
            new = self.choose_next_person(current_peers, removed_in_iteration | newly_choked, current_iteration)
            if new is not None:
                self.unchoke(new, current_iteration, add=new not in new_peers)
                current_peers.add(new)
        yield from current_peers

    def after_reset(self, current_iteration: int):
        for peer in self._client.peers:
            if peer not in self._historic_contributions:
                self._historic_contributions[peer] = HistEntry(self._max_iterations, current_iteration)


class GainValueUnchoking(OptimisticUnchoking):

    def _N(self, j: 'Client') -> int:
        return self._times_unchoked[j]

    def _n(self, j: 'Client') -> int:
        if j in self._historic_contributions:
            return sum(1 for x in self._historic_contributions[j].contributions if x != 0)
        return 0

    def _u(self, j: 'Client', current_iteration: int) -> float:
        if j not in self._historic_contributions:
            return 0
        if self._historic_contributions[j].added >= current_iteration:
            return 0
        return np.mean(
            self._historic_contributions[j].contributions[self._historic_contributions[j].added:current_iteration])

    def _Umax(self, current_iteration: int) -> float:
        return max(self._u(x, current_iteration) for x in self.neighbors)

    def _G(self, j: 'Client', current_iteration: int):
        if self._n(j) > 0:
            return self._u(j, current_iteration) * self._n(j) / self._N(j)
        else:
            return self._Umax(current_iteration) / (self._N(j) + 1)

    def choose_next_person(self, current_peers: Collection['Client'], blacklist: Collection['Client'],
                           current_iteration) -> 'Client':

        def gen():
            g_values = {x: self._G(x, current_iteration) for x in self.neighbors}
            sorted_g_values = sorted(g_values.items(), key=lambda kv: kv[1])
            for k, _ in sorted_g_values:
                if k.is_saturated:
                    continue
                if k in current_peers:
                    continue
                if k in blacklist:
                    continue
                yield k

        return next(gen(), None)


class DemeritChoking(OptimisticUnchoking):
    # timeout = 6 iterations
    def choose_next_person(self, current_peers: Collection['Client'], blacklist: Collection['Client'],
                           current_iteration) -> Optional['Client']:
        if current_iteration < 6:
            return None

        def gen():
            for peer, hc in self._historic_contributions.items():
                num_times_given = sum(1 for x in hc.contributions[current_iteration - 6: current_iteration] if x != 0)
                if num_times_given < 4:
                    continue
                if peer.is_saturated:
                    continue
                if peer in current_peers:
                    continue
                if peer in blacklist:
                    continue
                yield peer


        return next(gen(), None)

