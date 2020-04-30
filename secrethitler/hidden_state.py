from __future__ import annotations
from typing import List, Tuple
from copy import deepcopy
from secrethitler.policy_deck import PolicyDeck
from secrethitler.types import SecretRole, Party
from secrethitler.constants import NUM_LIB_POLICY, NUM_FAS_POLICY, DECK_SIZE


class HiddenSecretHitlerState:
    def __init__(self, hidden_roles: Tuple[SecretRole, ...], policy_deck: PolicyDeck, discard_pile: List[Party],
                 proposed_policies: Tuple[Party] or None):
        self.hidden_roles = hidden_roles
        self.policy_deck = policy_deck
        self.discard_pile = discard_pile
        self.proposed_policies = proposed_policies

    # takes in kwargs for what attributes have changed
    def change(self, **kwargs):
        for k, v in self.__dict__.items():
            if k not in kwargs:
                kwargs[k] = v
        return self.__class__(**kwargs)

    def __str__(self):
        return '<HiddenSecretHitlerState ' + ' '.join(f'{k}={v}' for k, v in sorted(self.__dict__.items())) + '>'

    def __hash__(self):
        return hash((self.hidden_roles, tuple(self.proposed_policies),
                     tuple(self.discard_pile), tuple(self.policy_deck.deck)))

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    @classmethod
    def valid_policy_count(cls, draw_pile, discard_pile, proposal, fas_policy, lib_policy):
        assert len(draw_pile) + len(discard_pile) + len(proposal) + fas_policy + lib_policy == DECK_SIZE
        components = [draw_pile, discard_pile, proposal]
        return sum(map(lambda l: l.count(Party.fascist), components)) + fas_policy == NUM_FAS_POLICY \
            and sum(map(lambda l: l.count(Party.liberal), components)) + lib_policy == NUM_LIB_POLICY
