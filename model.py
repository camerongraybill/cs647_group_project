from random import shuffle
from typing import Tuple, List, Sequence

from client import Result
from swarm import Swarm


class Model:
    @staticmethod
    def run(swarm: Swarm, iterations: int) -> Sequence[Tuple[Result, ...]]:
        all_agents = list(swarm.all_clients())
        [x.init_peers() for x in all_agents]
        output: List[Tuple[Result, ...]] = []
        for _ in range(iterations):
            remaining_agents = set(all_agents)
            while remaining_agents:
                rem_agents_copy = list(remaining_agents)
                shuffle(rem_agents_copy)
                for agent in rem_agents_copy:
                    if agent.wants_content():
                        peers = list(agent.peers)
                        shuffle(peers)
                        for peer in peers:
                            if peer.ask_for_content(agent):  # If they gave us content
                                agent.give_content(peer)
                                break
                        else:
                            remaining_agents.remove(agent)
                    else:
                        remaining_agents.remove(agent)
            output.append(
                tuple(x.get_state() for x in all_agents)
            )

            [x.reset() for x in all_agents]
        return output