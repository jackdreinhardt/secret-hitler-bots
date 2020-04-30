from __future__ import annotations
import random
import logging
from typing import Tuple
from collections import deque
from copy import deepcopy

from secrethitler.types import Party
from secrethitler.constants import NUM_LIB_POLICY, NUM_FAS_POLICY

logger = logging.getLogger(__name__)


class PolicyDeck:
    """
    Policy deck implemented using a deque.

    pop cards from the right using 'pop'
    """
    def __init__(self, deck):
        self.deck = deque(deck)

    def reset(self, lib_enacted=0, fas_enacted=0):
        liberal_policies = NUM_LIB_POLICY - lib_enacted
        fascist_policies = NUM_FAS_POLICY - fas_enacted
        list_deck = [Party.liberal] * liberal_policies + [Party.fascist] * fascist_policies
        random.shuffle(list_deck)
        return self.__class__(deck=list_deck)

    def draw(self, lib_policy, fas_policy, n=3) -> (Tuple[Party], PolicyDeck):
        new_deck = deepcopy(self)
        if len(self) < n:
            new_deck = self.reset(lib_enacted=lib_policy, fas_enacted=fas_policy)
        return tuple([new_deck.deck.pop() for _ in range(n)]), new_deck

    def peek(self, lib_policy, fas_policy, n=3) -> (Tuple[Party], PolicyDeck):
        policies, new_deck = self.draw(lib_policy, fas_policy, n)
        for policy in reversed(list(policies)):
            new_deck.deck.append(policy)
        return policies, new_deck

    def count(self, x):
        return self.deck.count(x)

    def __eq__(self, other):
        return self.deck == other.deck

    def __len__(self):
        return len(self.deck)

    def __str__(self):
        return f'<PolicyDeck len={len(self)}>'


# if __name__ == "__main__":
#     p = PolicyDeck([Party.liberal, Party.fascist])
#     constant = deepcopy(p)
#     pol, dek = p.draw(0, 0)
#     print(pol, dek)
#     assert constant == p, f"constant={constant} != p={p}"
#
#     p = PolicyDeck([Party.liberal, Party.fascist, Party.liberal])
#     constant = deepcopy(p)
#     pol, dek = p.peek(0, 0)
#     print(pol, dek)
#     assert constant == p, f"constant={constant} != p={p}"
#     pol2, dek2 = p.draw(0, 0)
#     assert pol2 == pol
#
#     p = PolicyDeck([Party.liberal, Party.fascist])
#     constant = deepcopy(p)
#     pol, dek = p.peek(0, 0)
#     print("pol", pol, "dek", dek)
#     assert constant == p, f"constant={constant} != p={p}"
#     pol2, dek2 = dek.peek(0,0)
#     print("pol2", pol2, "dek2", dek2)
#     pol3, dek3 = dek.draw(0,0)
#     print("pol3", pol3, "dek3", dek3)

