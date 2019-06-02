from __future__ import annotations

from dataclasses import dataclass
from itertools import count
from typing import Dict, Sequence, TYPE_CHECKING, Type, Any

from extra_types import Points, no_points
from strategies import Strategy

if TYPE_CHECKING:
    from swarm import Swarm

_counter = count(0)


@dataclass(frozen=True)
class Result:
    amount_acquired: int
    amount_remaining: int
    willing_to_give: int
    free_rider: bool
    id: int

    def to_json(self, iteration: int) -> Any:
        return {
            'amount_acquired': self.amount_acquired,
            'amount_remaining': self.amount_remaining,
            'willing_to_give': self.willing_to_give,
            'free_rider': self.free_rider,
            'id': self.id,
            'iteration': iteration
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
        self._peer_size = peer_size

    @property
    def is_saturated(self):
        return len(self._peers) >= self._peer_size

    @property
    def peers(self) -> Sequence[Client]:
        return list(self._peers.keys())

    def add_peer(self, peer: Client) -> None:
        self._peers[peer] = no_points

    def remove_peer(self, peer: Client) -> None:
        del self._peers[peer]

    @property
    def _is_free_rider(self) -> bool:
        return self._willing_to_give < (self._max_down // 2)

    def init_peers(self) -> None:
        self._peers = {
            x: no_points for x in self._strategy.init_peers(self._peer_size)
        }

    @property
    def _current_down(self) -> Points:
        return sum(self._peers.values())

    def reset(self, current_iteration: int) -> None:
        # if happy for this round reset to max
        if self._current_down > int(.65 * float(self._max_down)):
            self._willing_to_give = self._max_up
        else:
            # otherwise scale to give less
            self._willing_to_give = int((self._current_down / self._max_down) * self._willing_to_give)

        self._current_up = self._willing_to_give

        self._peers = {
            x: no_points for x in self._strategy.generate_new_peers(self._peers, current_iteration)
        }

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
            willing_to_give=self._max_up,
            free_rider=self._is_free_rider,
            id=self._id
        )

    def __hash__(self) -> int:
        return self._id.__hash__()

    def __repr__(self):
        return str(self.__hash__())