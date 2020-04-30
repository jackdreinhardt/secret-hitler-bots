import random
import logging
from agents.agent import Agent
from secrethitler import SecretHitlerState, Phase, PolicyChoiceAction, SecretRole

logger = logging.getLogger(__name__)


class SelfishAgent(Agent):
    """
    SelfishAgent Class.

    Plays randomly except in the following cases:
    1. always enacts their party's policies
    """
    def __init__(self, player_id: int, num_players: int, secret_role: SecretRole):
        super().__init__(player_id, 'Selfish Agent', secret_role, num_players)

    def get_action(self, state: SecretHitlerState, legal_actions):
        if state.phase == Phase.presidentSelectPolicy:
            assert state.president == self.player_id, 'asking president action from non president'
            discard = self.party.opposite() if PolicyChoiceAction(policy=self.party.opposite()) in legal_actions \
                else self.party
            move = PolicyChoiceAction(policy=discard)
        elif state.phase == Phase.chancellorSelectPolicy:
            assert state.chancellor == self.player_id, 'asking chancellor action from non chancellor'
            play = self.party if PolicyChoiceAction(policy=self.party) in legal_actions \
                else self.party.opposite()
            move = PolicyChoiceAction(policy=play)
        else:
            move = random.choice(legal_actions)

        logger.info(f'{self.name}:{self.player_id} has chosen {move}')
        return move
