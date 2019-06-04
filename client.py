from __future__ import annotations

from dataclasses import dataclass
from itertools import count
from typing import Dict, Sequence, TYPE_CHECKING, Type, Any, List

from extra_types import Points, no_points
from strategies import Strategy

if TYPE_CHECKING:
    from swarm import Swarm

_counter = count(0)

def empty_peers_dict(peers):
    return {
        x: no_points for x in peers
    }

@dataclass(frozen=True)
class Result:
    amount_acquired: int
    amount_remaining: int
    willing_to_give: int
    free_rider: bool
    id: int
    peers: List[int]

    def to_json(self, iteration: int) -> Any:
        return {
            'amount_acquired': self.amount_acquired,
            'amount_remaining': self.amount_remaining,
            'willing_to_give': self.willing_to_give,
            'free_rider': self.free_rider,
            'id': self.id,
            'iteration': iteration,
            'peers': self.peers
        }


class Client:
    def __init__(self,
                 strat: Type[Strategy],
                 up: Points,
                 down: Points,
                 peer_size: int,
                 swarm: 'Swarm',
                 iterations: int
                 ):
        self._strategy = strat(swarm, self, iterations)
        self._id = _counter.__next__()
        self._max_up = up
        self._willing_to_give = up
        self._max_down = down
        self._current_up = up
        self._peers: Dict[Client, Points] = {}
        self.peer_size = peer_size
        self._persisted = None

    @property
    def id(self) -> int:
        return self._id

    @property
    def is_saturated(self):
        return len(self.peers) >= self.peer_size

    @property
    def peers(self) -> Sequence[Client]:
        return list(self._peers.keys())

    def add_peer(self, peer: Client) -> None:
        print(f"connecting {self} --> {peer}")
        assert peer not in self.peers
        self._peers[peer] = no_points

    def remove_peer(self, peer: Client) -> None:
        print(f"removing {self} --> {peer}")
        del self._peers[peer]

    @property
    def _is_free_rider(self) -> bool:
        return self._willing_to_give < (self._max_down // 2)

    def init_peers(self) -> None:
        self._peers = empty_peers_dict(self._strategy.init_peers(self.peer_size))

    @property
    def _current_down(self) -> Points:
        return sum(self._peers.values())

    def before_reset(self):
        self._persisted = dict(self._peers.items())

    def reset_values(self):
        # if happy for this round reset to max
        if self._current_down > int(.65 * float(self._max_down)):
            self._willing_to_give = self._max_up
        else:
            # otherwise scale to give less
            self._willing_to_give = int((self._current_down / self._max_down) * self._willing_to_give)

        self._current_up = self._willing_to_give

    def reset(self, current_iteration: int) -> None:
        new_neighbors, removed_people = self._strategy.pre_generate(self._persisted, current_iteration)
        new_peers = list(self._strategy.generate_new_peers(self._persisted, current_iteration, new_neighbors, removed_people))
        print(f"Got new peers for {self}: ", new_peers)
        self._peers = empty_peers_dict(new_peers)

    def after_reset(self, current_iteration: int):
        # clean up dangling connections
        for peer in self.peers:
            if self not in peer.peers:
                self.remove_peer(peer)
        self._strategy.after_reset(current_iteration)


    def ask_for_content(self, give_to: Client) -> bool:
        """ Returns whether or not content was granted """
        if self._strategy.willing_to_give_to(give_to):
            if self._current_up > 0:
                self._current_up -= 1
                return True
        return False

    def wants_content(self) -> bool:
        """ Returns whether or not client wants content"""
        return self._current_down < self._max_down

    def give_content(self, from_: Client) -> None:
        self._peers[from_] += 1

    def get_state(self) -> Result:
        return Result(
            amount_acquired=self._current_down,
            amount_remaining=self._current_up,
            willing_to_give=self._willing_to_give,
            free_rider=self._is_free_rider,
            id=self._id,
            peers=[x.id for x in self.peers]
        )

    def __hash__(self) -> int:
        return self._id.__hash__()

    def __repr__(self):
        return str(self.__hash__())