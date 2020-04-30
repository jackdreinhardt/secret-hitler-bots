import itertools as it
from collections import namedtuple

from sympy.utilities.iterables import multiset_permutations

from secrethitler.types import SecretRole, Power, Party


FAS_ROLES = {SecretRole.fascist, SecretRole.hitler}
LIB_ROLES = {SecretRole.liberal}

# (num_lib, num_fas)
SECRET_HITLER_PLAYER_COUNT = {
    5:  (3, 2),
    6:  (4, 2),
    7:  (4, 3),
    8:  (5, 3),
    9:  (5, 4),
    10: (6, 4)
}

SECRET_HITLER_SECRET_ROLES = {
    5:  tuple([SecretRole.fascist] * 1 + [SecretRole.hitler] + [SecretRole.liberal] * 3),
    6:  tuple([SecretRole.fascist] * 1 + [SecretRole.hitler] + [SecretRole.liberal] * 4),
    7:  tuple([SecretRole.fascist] * 2 + [SecretRole.hitler] + [SecretRole.liberal] * 4),
    8:  tuple([SecretRole.fascist] * 2 + [SecretRole.hitler] + [SecretRole.liberal] * 5),
    9:  tuple([SecretRole.fascist] * 3 + [SecretRole.hitler] + [SecretRole.liberal] * 5),
    10: tuple([SecretRole.fascist] * 3 + [SecretRole.hitler] + [SecretRole.liberal] * 6)
}

SECRET_HITLER_POWERS = {
    5:  [Power.none, Power.none, Power.none, Power.deckpeek, Power.bullet, Power.bullet],
    6:  [Power.none, Power.none, Power.none, Power.deckpeek, Power.bullet, Power.bullet],
    7:  [Power.none, Power.none, Power.investigate, Power.specialelection, Power.bullet, Power.bullet],
    8:  [Power.none, Power.none, Power.investigate, Power.specialelection, Power.bullet, Power.bullet],
    9:  [Power.none, Power.investigate, Power.investigate, Power.specialelection, Power.bullet, Power.bullet],
    10: [Power.none, Power.investigate, Power.investigate, Power.specialelection, Power.bullet, Power.bullet]
}

VoteAction = namedtuple('VoteAction', ['ja'])
NominateChancellorAction = namedtuple('NominateChancellorAction', ['chancellor'])
PolicyChoiceAction = namedtuple('PolicyChoiceAction', ['policy'])
VetoAction = namedtuple('VetoAction', ['veto'])

# nonsense field necessary for isinstance call to identify type
DeckpeekPowerAction = namedtuple('DeckpeekPowerAction', ['nonsense'])
BulletPowerAction = namedtuple('BulletPowerAction', ['player'])
InvestigateAction = namedtuple('InvestigateAction', ['player'])
SpecialElectionAction = namedtuple('SpecialElectionAction', ['player'])

DeckpeekPowerObservation = namedtuple('DeckpeekPowerObservation', ['policies'])
InvestigatePowerObservation = namedtuple('InvestigatePowerObservation', ['party'])
PresidentPassObservation = namedtuple('PresidentPassObservation', ['policies'])

SECRET_HITLER_POWERS_ACTIONS = {
    Power.deckpeek: DeckpeekPowerAction,
    Power.bullet: BulletPowerAction,
    Power.investigate: InvestigateAction,
    Power.specialelection: SpecialElectionAction
}

SECRET_HITLER_POSSIBLE_ROLES = {
    5: list(set(it.permutations(SECRET_HITLER_SECRET_ROLES[5]))),
    6: list(set(it.permutations(SECRET_HITLER_SECRET_ROLES[6]))),
    7: list(set(it.permutations(SECRET_HITLER_SECRET_ROLES[7]))),
    8: list(set(it.permutations(SECRET_HITLER_SECRET_ROLES[8]))),
    9: list(set(it.permutations(SECRET_HITLER_SECRET_ROLES[9]))),
    10: list(set(it.permutations(SECRET_HITLER_SECRET_ROLES[10])))
}

NUM_LIB_POLICY = 6
NUM_FAS_POLICY = 11
DECK_SIZE = NUM_FAS_POLICY + NUM_LIB_POLICY
LIB_POLICY_WIN = 5
FAS_POLICY_WIN = 6
CHAOS = 3
HITLER_ZONE = 3

POSSIBLE_DECKS = []
for lib in range(0, NUM_LIB_POLICY + 1):
    for fas in range(0, NUM_FAS_POLICY + 1):
        if fas == 0 and lib == 0:
            POSSIBLE_DECKS.append([])
        else:
            for deck in multiset_permutations([Party.liberal.value] * lib + [Party.fascist.value] * fas):
                deck = list(map(lambda p: Party.liberal if p == Party.liberal.value else Party.fascist, deck))
                POSSIBLE_DECKS.append(deck)
