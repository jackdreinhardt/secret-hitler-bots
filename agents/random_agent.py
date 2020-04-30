import random
import logging
from typing import List
from agents.agent import Agent
from secrethitler import SecretHitlerState, SecretRole, Party, HiddenSecretHitlerState, PolicyDeck, Phase

logger = logging.getLogger(__name__)


class RandomAgent(Agent):
    """
    RandomAgent Class.

    Plays randomly.
    """

    def __init__(self, player_id: int, num_players: int, secret_role: SecretRole):
        super().__init__(player_id, 'Random Agent', secret_role, num_players)

    def get_action(self, state: SecretHitlerState, legal_actions: List):
        move = random.choice(legal_actions)
        logger.info(f'{self.name}:{self.player_id} has chosen {move}')
        return move


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    hidden = HiddenSecretHitlerState(hidden_roles=(SecretRole.fascist, SecretRole.liberal, SecretRole.liberal,
                                                   SecretRole.liberal, SecretRole.hitler, SecretRole.fascist,
                                                   SecretRole.liberal, SecretRole.fascist, SecretRole.liberal, SecretRole.liberal),
                                     policy_deck=PolicyDeck([Party.fascist, Party.liberal, Party.liberal]),
                                     proposed_policies=(), discard_pile=[Party.fascist, Party.liberal, Party.fascist,
                                                                         Party.fascist, Party.liberal, Party.liberal,
                                                                         Party.fascist, Party.fascist])
    s = SecretHitlerState(starting_num_players=10, current_num_players=8, president=9, chancellor=2, phase=Phase.presidentSelectPolicy,
                          fas_policy=5, lib_policy=1, chaos=2, game_end=None, prev_gov=(5, 6), alive_players=[1, 2, 4, 5, 6, 8, 9],
                          se_prev_pres=None, president_veto=True, game_end_reason=None, policy_deck_size=3)
    agent = RandomAgent(player_id=1, num_players=10, secret_role=SecretRole.liberal)

    while True:
        agent.get_action(s, s.legal_actions(hidden_state=hidden, player=agent.player_id))
