import logging
from typing import List, Tuple

from secrethitler import SecretHitlerState, LIB_ROLES, Party, SecretRole, HiddenSecretHitlerState, \
    SECRET_HITLER_POSSIBLE_ROLES, DeckpeekPowerObservation, InvestigatePowerObservation, Phase, PresidentPassObservation

logger = logging.getLogger(__name__)


class Agent:
    """
    Base Agent class
    """
    def __init__(self, player_id: int, name: str, secret_role: SecretRole, num_players):
        if isinstance(self.__class__, Agent):
            raise NotImplementedError
        self.player_id = player_id
        self.name = name
        self.secret_role = secret_role
        self.party = Party.liberal if secret_role in LIB_ROLES else Party.fascist
        # TODO: refactor knowledge into subclass
        self.hidden_role_beliefs = SECRET_HITLER_POSSIBLE_ROLES[num_players]
        self.filter_hidden_roles_on_role(self.player_id, self.secret_role)
        self.deck_knowledge = []
        self.president_pass = []
        logger.debug(f'Initializing agent {self}')

    def get_action(self, state: SecretHitlerState, legal_actions: List):
        raise NotImplementedError

    def handle_transition(self, old_state: SecretHitlerState, new_state: SecretHitlerState, old_hidden_state: HiddenSecretHitlerState,
                          new_hidden_state: HiddenSecretHitlerState, moves, observation=None):
        self.filter_hidden_roles_on_terminal(old_state, new_state, old_hidden_state, moves)

        # remove deck beliefs from deckpeek power as cards are drawn
        old_deck_length, new_deck_length = len(old_hidden_state.policy_deck), len(new_hidden_state.policy_deck)
        if old_deck_length - new_deck_length > 0:
            self.deck_knowledge = self.deck_knowledge[old_deck_length - new_deck_length:]
        if new_state.phase not in [Phase.chancellorSelectPolicy, Phase.veto]:
            self.president_pass = []

    def handle_observation(self, observation):
        if isinstance(observation, DeckpeekPowerObservation):
            self.deck_knowledge = list(observation.policies)
        elif isinstance(observation, InvestigatePowerObservation):
            self.filter_hidden_roles_on_party(*observation.party)
        elif isinstance(observation, PresidentPassObservation):
            self.president_pass = list(observation.policies)
        else:
            logger.debug(f'Did not handle observation: {observation}')

    def __str__(self):
        return f'<{self.name} ' + ' '.join(f'num_{k}={len(v)}' if k == 'hidden_role_beliefs' or k == 'deck_beliefs'
                                           else f'{k}={v}'
                                           for k, v in sorted(self.__dict__.items())) + '>'

    def communicate_hidden_state(self, hidden_role):
        self.hidden_role_beliefs = [hidden_role]
        logger.debug(f'Updated hidden state belief for {self}')

    def filter_hidden_roles_on_role(self, player: int, role: SecretRole):
        self.hidden_role_beliefs = list(filter(lambda roles: roles[player] == role, self.hidden_role_beliefs))

    def filter_hidden_roles_on_party(self, player: int, party: Party):
        self.hidden_role_beliefs = list(filter(lambda roles: roles[player].party() == party, self.hidden_role_beliefs))

    def filter_hidden_roles_on_terminal(self, old_state: SecretHitlerState, new_state: SecretHitlerState,
                                        old_hidden_state: HiddenSecretHitlerState, moves):
        self.hidden_role_beliefs = self.hidden_role_beliefs if new_state.is_terminal() else \
            list(filter(
                lambda roles: not old_state.transition(moves, old_hidden_state.change(hidden_roles=roles))[0].is_terminal(),
                self.hidden_role_beliefs)
            )

