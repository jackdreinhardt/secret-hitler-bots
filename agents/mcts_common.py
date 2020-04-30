import logging
import numpy as np
import random
from typing import List, Tuple, Any
from collections import deque

from itertools import combinations_with_replacement

from secrethitler import SecretHitlerState, HiddenSecretHitlerState, PolicyDeck, POSSIBLE_DECKS, Party, \
    Phase, DECK_SIZE, PolicyChoiceAction

logger = logging.getLogger(__name__)


def _possible_draw_piles(deck_size: int, top_cards: List[Party]) -> List[PolicyDeck]:
    assert deck_size >= len(top_cards), 'deck size smaller than top card information'
    return list(map(lambda d: PolicyDeck(d),
                    filter(lambda deck: len(deck) == deck_size and deck[:len(top_cards)] == top_cards,
                           POSSIBLE_DECKS))
                )


def _possible_proposals(phase: Phase, legal_actions, president_pass) -> List[Tuple] or List[Tuple[Party]]:
    if phase in [Phase.presidentSelectPolicy, Phase.chancellorSelectPolicy]:
        return [tuple(action.policy for action in filter(lambda a: isinstance(a, PolicyChoiceAction), legal_actions))]
    elif phase == Phase.veto:
        return [tuple(president_pass)]
    else:
        return [()]


def _proposal_size(phase: Phase) -> int:
    return 3 if phase == Phase.presidentSelectPolicy else 2 if phase in [Phase.chancellorSelectPolicy, Phase.veto] else 0


def _possible_discard_piles(other_policies: int) -> List[List[Party]]:
    assert 0 <= other_policies <= DECK_SIZE, f'number of other policies is invalid: {other_policies}'
    discard_length = DECK_SIZE - other_policies
    return list(filter(lambda deck: len(deck) == discard_length, POSSIBLE_DECKS))


def determinization_iterator(possible_hidden_roles: List, num_iterations, state: SecretHitlerState, legal_actions, top_cards, president_pass):
    draw_piles = _possible_draw_piles(state.policy_deck_size, top_cards)
    discard_piles = _possible_discard_piles(other_policies=state.policy_deck_size + _proposal_size(state.phase) +
                                            state.fas_policy + state.lib_policy)

    possible_proposals = _possible_proposals(state.phase, legal_actions, president_pass)

    i = 0
    while i < num_iterations:
        random.shuffle(draw_piles)
        for draw_pile in draw_piles:
            random.shuffle(discard_piles)
            for discard_pile in discard_piles:
                random.shuffle(possible_proposals)
                for proposal in possible_proposals:
                    if HiddenSecretHitlerState.valid_policy_count(draw_pile=draw_pile, discard_pile=discard_pile,
                                                                  proposal=proposal, fas_policy=state.fas_policy,
                                                                  lib_policy=state.lib_policy):
                        random.shuffle(possible_hidden_roles)
                        for hidden_role in possible_hidden_roles:
                            if i >= num_iterations:
                                return
                            yield HiddenSecretHitlerState(hidden_roles=hidden_role, policy_deck=draw_pile,
                                                          discard_pile=discard_pile, proposed_policies=proposal)
                            i += 1


def random_choice(values, p=None):
    return values[np.random.choice(range(len(values)), p=p)]


def simulate(game_state, hidden_state):
    while not game_state.is_terminal():
        moves = tuple([
            random_choice(game_state.legal_actions(hidden_state, player))
            for player in game_state.moving_players()
        ])
        game_state, hidden_state, _ = game_state.transition(moves=moves, hidden_state=hidden_state)
    return game_state.terminal_value(hidden_state)


if __name__ == "__main__":
    sh = SecretHitlerState(starting_num_players=5, alive_players=[0,1,2,3,4], current_num_players=5, chancellor=4, chaos=0,
                           fas_policy=0, game_end=None, game_end_reason=None, lib_policy=0, phase=Phase.nomination,
                           policy_deck_size=17, president=1, president_veto=True, prev_gov=(None, 4), se_prev_pres=None)
    for s in determinization_iterator([()], 10, sh, top_cards=[Party.fascist, Party.fascist, Party.fascist]):
        print(s)
