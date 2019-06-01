from __future__ import annotations

from dataclasses import dataclass
from itertools import count
from typing import Dict, Sequence, TYPE_CHECKING, Type

from extra_types import Points, no_points
from strategies import Strategy

if TYPE_CHECKING:
    from swarm import Swarm

_counter = count(0)


@dataclass(frozen=True)
class Result:
    max_amount: int
    amount_acquired: int
    amount_remaining: int
    willing_to_give: int
    free_rider: bool


class Client:
    def __init__(self,
                 strat: Type[Strategy],
                 up: Points,
                 down: Points,
                 peer_size: int,
                 swarm: 'Swarm',
                 is_free_rider: bool = False):
        self._strategy = strat(swarm, self)
        self._id = _counter.__next__()
        self._max_up = up
        self._max_down = down
        self._current_up = up
        self._is_free_rider = is_free_rider
        self._peers: Dict[Client, Points] = {}
        self._peer_size = peer_size

    @property
    def peers(self) -> Sequence[Client]:
        return list(self._peers.keys())

    def init_peers(self) -> None:
        self._peers = {
            x: no_points for x in self._strategy.init_peers(self._peer_size)
        }

    @property
    def is_free_rider(self) -> bool:
        return self._is_free_rider

    @property
    def _current_down(self) -> Points:
        return sum(self._peers.values())

    def reset(self) -> None:
        self._current_up = self._max_up

        self._peers = {
            x: no_points for x in self._strategy.generate_new_peers(self._peers, self)
        }

    def ask_for_content(self) -> bool:
        """ Returns whether or not content was granted """
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
            max_amount=self._max_down,
            amount_acquired=self._current_down,
            amount_remaining=self._current_up,
            willing_to_give=self._max_up,
            free_rider=self._is_free_rider
        )

    def __hash__(self) -> int:
        return self._id.__hash__()

    def __repr__(self):
        return str(self.__hash__())