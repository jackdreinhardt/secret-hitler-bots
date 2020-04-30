from __future__ import annotations
import random
import logging
from typing import List, Tuple
from copy import deepcopy

from secrethitler.constants import *
from secrethitler.types import GameEndReason, Phase, Party, SecretRole, Power
from secrethitler.hidden_state import HiddenSecretHitlerState

logger = logging.getLogger(__name__)


class SecretHitlerState:
    """
    SecretHitlerState class. Inherits from GameState.

    Members variables of this class should remain static.
    """
    def __init__(self, starting_num_players, current_num_players, president, chancellor, phase, fas_policy,
                 lib_policy, chaos, game_end, prev_gov, alive_players, se_prev_pres, president_veto, game_end_reason,
                 policy_deck_size, **kwargs):
        assert 0 < starting_num_players <= 10
        assert 0 <= current_num_players <= starting_num_players
        assert president in alive_players
        assert chancellor in alive_players or chancellor is None
        assert len(alive_players) == current_num_players
        assert isinstance(phase, Phase)
        assert 0 <= fas_policy <= FAS_POLICY_WIN and 0 <= lib_policy <= LIB_POLICY_WIN
        assert 0 <= chaos < CHAOS
        assert 0 <= policy_deck_size <= DECK_SIZE
        assert isinstance(game_end, Party) if phase == Phase.end else True, f'{game_end}'
        assert 0 <= prev_gov[1] < starting_num_players if prev_gov is not None else True
        assert prev_gov[0] != prev_gov[1] if prev_gov is not None else True
        self.starting_num_players = starting_num_players
        self.current_num_players = current_num_players
        self.alive_players = alive_players
        self.president = president
        self.se_prev_pres = se_prev_pres
        self.chancellor = chancellor
        self.phase = phase
        self.fas_policy = fas_policy
        self.lib_policy = lib_policy
        self.policy_deck_size = policy_deck_size
        self.powers = SECRET_HITLER_POWERS[self.starting_num_players]
        self.chaos = chaos
        self.game_end = game_end
        self.game_end_reason = game_end_reason
        self.prev_gov = prev_gov
        self.veto = True if fas_policy == FAS_POLICY_WIN - 1 and president_veto else False
        self.president_veto = president_veto

    def __hash__(self):
        return hash((self.starting_num_players, self.president, self.chancellor, self.phase, self.game_end_reason,
                     self.fas_policy, self.lib_policy, self.chaos, self.game_end, self.prev_gov,
                     self.president_veto, self.se_prev_pres, tuple(self.alive_players), self.policy_deck_size))

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    @classmethod
    def start_state(cls, num_players):
        """
        Returns the starting state for a certain number of players
        """
        return cls(starting_num_players=num_players, president=random.randint(0, num_players - 1), prev_gov=None,
                   chancellor=None, phase=Phase.nomination, fas_policy=0, lib_policy=0, chaos=0, game_end=None,
                   current_num_players=num_players, game_end_reason=None, alive_players=[*range(num_players)],
                   president_veto=True, se_prev_pres=None, policy_deck_size=DECK_SIZE)

    # takes in kwargs for what attributes have changed
    def change(self, **kwargs):
        for k, v in self.__dict__.items():
            if k not in kwargs:
                kwargs[k] = v
        return self.__class__(**kwargs)

    def is_terminal(self):
        """
        Returns true if the game has ended
        """
        return self.phase == Phase.end

    def terminal_value(self, hidden_state: HiddenSecretHitlerState):
        """
        Returns the payoff for each player, this ensures zero-sum
        """
        num_lib, num_fas = SECRET_HITLER_PLAYER_COUNT[self.starting_num_players]

        lib_amount = 1.0 if self.game_end == Party.liberal else -1.0
        fas_amount = -float(num_lib) / num_fas if self.game_end == Party.liberal else float(num_lib) / num_fas

        return [
            lib_amount if player_role in LIB_ROLES else fas_amount
            for player_role in hidden_state.hidden_roles
        ]

    def moving_players(self) -> List[int]:
        """
        Returns an array of players whose turn it is.
        """
        assert not self.is_terminal(), "The game has ended"
        if self.phase in [Phase.presidentSelectPolicy, Phase.nomination, Phase.presidentPower]:
            return [] if self.phase == Phase.presidentPower and self.powers[self.fas_policy] == Power.none \
                else [self.president]

        if self.phase == Phase.vote:
            return self.alive_players

        if self.phase == Phase.chancellorSelectPolicy:
            return [self.chancellor]

        if self.phase == Phase.veto:
            return [self.president]

        raise ValueError(f'{self.phase} is not valid')

    def legal_actions(self, hidden_state: HiddenSecretHitlerState, player: int) -> List:
        """
        Returns the legal actions of the player from this state
        """
        assert player in self.moving_players(), "Asked a non-moving player legal actions"
        if self.phase == Phase.nomination:
            return [NominateChancellorAction(chancellor=p)
                    for p in self.alive_players if p != player
                    and p not in (self.prev_gov if self.prev_gov is not None else tuple([]))]

        if self.phase == Phase.vote:
            return [VoteAction(ja=True), VoteAction(ja=False)]

        if self.phase == Phase.presidentSelectPolicy:
            assert len(hidden_state.proposed_policies) == 3
            return [PolicyChoiceAction(policy=p) for p in hidden_state.proposed_policies]

        if self.phase == Phase.chancellorSelectPolicy:
            assert len(hidden_state.proposed_policies) == 2
            return [PolicyChoiceAction(policy=p) for p in hidden_state.proposed_policies] + \
                ([VetoAction(veto=True)] if self.veto and self.president_veto else [])

        if self.phase == Phase.veto:
            return [VetoAction(veto=True), VetoAction(veto=False)]

        if self.phase == Phase.presidentPower:
            if self.powers[self.fas_policy] not in [Power.deckpeek, Power.none]:
                return [SECRET_HITLER_POWERS_ACTIONS[self.powers[self.fas_policy]](player=p)
                        for p in self.alive_players if p != player]

            if self.powers[self.fas_policy] == Power.deckpeek:
                return [SECRET_HITLER_POWERS_ACTIONS[self.powers[self.fas_policy]](nonsense=None)]

        assert False, "Invalid Phase"

    @staticmethod
    def _next_president(current_president: int, num_players: int, alive_players: List[int], se_prev_pres=None) -> (int, int):
        new_pres = ((current_president if se_prev_pres is None else se_prev_pres) + 1) % num_players
        while new_pres not in alive_players:
            new_pres = (new_pres + 1) % num_players
        return new_pres, None

    @staticmethod
    def _game_ending_policy(fas_policy, lib_policy) -> (Party, GameEndReason):
        if fas_policy == FAS_POLICY_WIN:
            return Party.fascist, GameEndReason.six_fascist_policies
        elif lib_policy == LIB_POLICY_WIN:
            return Party.liberal, GameEndReason.five_liberal_policies
        else:
            return None, None

    def _chaos_helper(self, hidden_state: HiddenSecretHitlerState, **kwargs) \
            -> (SecretHitlerState, HiddenSecretHitlerState):
        policy, new_deck = hidden_state.policy_deck.draw(lib_policy=self.lib_policy, fas_policy=self.fas_policy, n=1)
        discard_pile = [] if len(new_deck) > len(hidden_state.policy_deck) else hidden_state.discard_pile
        assert len(policy) == 1
        fas_policy = self.fas_policy + 1 if policy[0] == Party.fascist else self.fas_policy
        lib_policy = self.lib_policy + 1 if policy[0] == Party.liberal else self.lib_policy
        phase = Phase.end if fas_policy == FAS_POLICY_WIN or lib_policy == LIB_POLICY_WIN else Phase.nomination
        game_end, game_end_reason = self._game_ending_policy(fas_policy=fas_policy, lib_policy=lib_policy)
        if game_end is not None and phase not in [Phase.end]:
            print('what')

        return self.change(chaos=0, prev_gov=None, game_end=game_end, fas_policy=fas_policy, lib_policy=lib_policy,
                           phase=phase, game_end_reason=game_end_reason, policy_deck_size=len(new_deck),
                           **kwargs), hidden_state.change(policy_deck=new_deck,
                                                       discard_pile=discard_pile), None

    def vote_fail_transition(self, hidden_state: HiddenSecretHitlerState) \
            -> (SecretHitlerState, HiddenSecretHitlerState):
        president, se_prev_pres \
            = self._next_president(current_president=self.president, num_players=self.starting_num_players,
                                   alive_players=self.alive_players, se_prev_pres=self.se_prev_pres)

        if self.chaos + 1 >= CHAOS:
            return self._chaos_helper(hidden_state=hidden_state, president=president, se_prev_pres=se_prev_pres)

        return self.change(chancellor=None, phase=Phase.nomination, chaos=self.chaos + 1, president=president,
                           se_prev_pres=se_prev_pres), hidden_state, None

    def vote_pass_transition(self, hidden_state: HiddenSecretHitlerState) \
            -> (SecretHitlerState, HiddenSecretHitlerState):
        if self.fas_policy >= HITLER_ZONE:
            if hidden_state.hidden_roles[self.chancellor] == SecretRole.hitler:
                phase = Phase.end
                game_end = Party.fascist
                game_end_reason = GameEndReason.hitler_elected
                return self.change(phase=phase, game_end=game_end, game_end_reason=game_end_reason), hidden_state, None
        prev_gov = (self.president if self.current_num_players > 5 else None, self.chancellor)
        proposed_policies, new_deck = hidden_state.policy_deck.draw(lib_policy=self.lib_policy, fas_policy=self.fas_policy, n=3)
        discard_pile = [] if len(new_deck) > len(hidden_state.policy_deck) else hidden_state.discard_pile

        return self.change(phase=Phase.presidentSelectPolicy, prev_gov=prev_gov, policy_deck_size=len(new_deck)), \
               hidden_state.change(proposed_policies=proposed_policies, policy_deck=new_deck, discard_pile=discard_pile), None

    def vote_transition(self, hidden_state: HiddenSecretHitlerState, votes: List[VoteAction]) \
            -> (SecretHitlerState, HiddenSecretHitlerState):
        assert len(votes) == len(self.alive_players)
        ja_votes = sum([1 for vote in votes if vote.ja])
        if ja_votes > self.current_num_players / 2:
            return self.vote_pass_transition(hidden_state)
        else:
            return self.vote_fail_transition(hidden_state)

    def nominate_chancellor_transition(self, chancellor: int) -> SecretHitlerState:
        return self.change(chancellor=chancellor, phase=Phase.vote)

    def president_select_transition(self, hidden_state: HiddenSecretHitlerState, discard_policy: Party) \
            -> (SecretHitlerState, HiddenSecretHitlerState):
        assert discard_policy in hidden_state.proposed_policies
        passed_policies = list(hidden_state.proposed_policies)
        passed_policies.remove(discard_policy)
        discard_pile = hidden_state.discard_pile + [discard_policy]
        return self.change(phase=Phase.chancellorSelectPolicy), \
            hidden_state.change(proposed_policies=passed_policies, discard_pile=discard_pile), \
            PresidentPassObservation(policies=passed_policies)

    def chancellor_select_transition(self, hidden_state: HiddenSecretHitlerState, move) \
            -> (SecretHitlerState, HiddenSecretHitlerState):
        if isinstance(move, VetoAction):
            return self.change(phase=Phase.veto), hidden_state, None
        elif isinstance(move, PolicyChoiceAction):
            policy = move.policy
            assert policy in hidden_state.proposed_policies
            fas_policy = self.fas_policy + 1 if policy == Party.fascist else self.fas_policy
            lib_policy = self.lib_policy + 1 if policy == Party.liberal else self.lib_policy
            discarded_policy = list(hidden_state.proposed_policies)
            discarded_policy.remove(policy)
            assert len(discarded_policy) == 1
            discard_pile = hidden_state.discard_pile + discarded_policy

            phase = Phase.end \
                if fas_policy == FAS_POLICY_WIN or lib_policy == LIB_POLICY_WIN \
                else (Phase.presidentPower
                      if policy == Party.fascist
                      and SECRET_HITLER_POWERS[self.starting_num_players][fas_policy] != Power.none
                      else Phase.nomination)

            game_end, game_end_reason = self._game_ending_policy(fas_policy=fas_policy, lib_policy=lib_policy)

            president = self.president
            se_prev_pres = self.se_prev_pres

            if phase == Phase.nomination:
                president, se_prev_pres \
                    = self._next_president(current_president=self.president, num_players=self.starting_num_players,
                                           alive_players=self.alive_players, se_prev_pres=self.se_prev_pres)

            return self.change(fas_policy=fas_policy, lib_policy=lib_policy, chaos=0, phase=phase, game_end=game_end,
                               president=president, se_prev_pres=se_prev_pres, chancellor=None,
                               president_veto=True, game_end_reason=game_end_reason), \
                hidden_state.change(proposed_policies=(), discard_pile=discard_pile), None
        else:
            assert False, f'Invalid Action={move}'

    def deckpeek_transition(self, hidden_state: HiddenSecretHitlerState) \
            -> (SecretHitlerState, HiddenSecretHitlerState, Tuple):
        president, se_prev_pres \
            = self._next_president(current_president=self.president, num_players=self.starting_num_players,
                                   alive_players=self.alive_players, se_prev_pres=self.se_prev_pres)
        policies, new_deck = hidden_state.policy_deck.peek(lib_policy=self.lib_policy, fas_policy=self.fas_policy, n=3)
        discard_pile = [] if len(new_deck) > len(hidden_state.policy_deck) else hidden_state.discard_pile

        return self.change(president=president, se_prev_pres=se_prev_pres,
                           phase=Phase.nomination, policy_deck_size=len(new_deck)), \
            hidden_state.change(policy_deck=new_deck, discard_pile=discard_pile), DeckpeekPowerObservation(policies)

    def bullet_transition(self, hidden_state: HiddenSecretHitlerState, target: int) \
            -> (SecretHitlerState, HiddenSecretHitlerState, Tuple):
        if hidden_state.hidden_roles[target] == SecretRole.hitler:
            return self.change(phase=Phase.end, game_end=Party.liberal, game_end_reason=GameEndReason.hitler_killed), \
                hidden_state, None

        alive_players = [player for player in self.alive_players if player != target]
        assert len(alive_players) < self.starting_num_players
        president, se_prev_pres \
            = self._next_president(current_president=self.president, num_players=self.starting_num_players,
                                   alive_players=alive_players, se_prev_pres=self.se_prev_pres)
        prev_gov = self.prev_gov if self.current_num_players > 5 else (None, self.prev_gov[1])

        return self.change(phase=Phase.nomination, current_num_players=self.current_num_players - 1,
                           alive_players=alive_players, president=president, se_prev_pres=se_prev_pres,
                           prev_gov=prev_gov), hidden_state, None

    # TODO: prevent player from being investigated twice
    def investigate_transition(self, hidden_state: HiddenSecretHitlerState, target: int) \
            -> (SecretHitlerState, HiddenSecretHitlerState, Tuple):
        assert target in self.alive_players
        president, se_prev_pres \
            = self._next_president(current_president=self.president, num_players=self.starting_num_players,
                                   alive_players=self.alive_players, se_prev_pres=self.se_prev_pres)
        party = Party.liberal if hidden_state.hidden_roles[target] in LIB_ROLES else Party.fascist

        return self.change(president=president, se_prev_pres=se_prev_pres, phase=Phase.nomination), hidden_state, \
            InvestigatePowerObservation((target, party))

    def special_election_transition(self, hidden_state: HiddenSecretHitlerState, target: int) \
            -> (SecretHitlerState, HiddenSecretHitlerState, Tuple):
        assert target in self.alive_players
        return self.change(president=target, se_prev_pres=self.president, phase=Phase.nomination), hidden_state, None

    def president_power_transition(self, hidden_state: HiddenSecretHitlerState, power) \
            -> (SecretHitlerState, HiddenSecretHitlerState, Tuple):
        if isinstance(power, DeckpeekPowerAction):
            return self.deckpeek_transition(hidden_state)
        if isinstance(power, BulletPowerAction):
            return self.bullet_transition(hidden_state, power.player)
        if isinstance(power, InvestigateAction):
            return self.investigate_transition(hidden_state, power.player)
        if isinstance(power, SpecialElectionAction):
            return self.special_election_transition(hidden_state, power.player)

        assert False, f'Invalid Presidential Power={power}'

    def veto_transition(self, hidden_state: HiddenSecretHitlerState, veto: bool) \
            -> (SecretHitlerState, HiddenSecretHitlerState):
        if veto:
            discard_pile = hidden_state.discard_pile + list(hidden_state.proposed_policies)
            hs = hidden_state.change(discard_pile=discard_pile, proposed_policies=())
            president, se_prev_pres \
                = self._next_president(current_president=self.president, num_players=self.starting_num_players,
                                       alive_players=self.alive_players, se_prev_pres=self.se_prev_pres)

            if self.chaos + 1 >= CHAOS:
                return self._chaos_helper(hidden_state=hs, chancellor=None, president=president,
                                          se_prev_pres=se_prev_pres)

            return self.change(phase=Phase.nomination, chancellor=None, president=president,
                               se_prev_pres=se_prev_pres), hs, None

        return self.change(phase=Phase.chancellorSelectPolicy, president_veto=False), hidden_state, None

    def transition(self, moves: List, hidden_state: HiddenSecretHitlerState) \
            -> (SecretHitlerState, HiddenSecretHitlerState, Tuple or None):
        """
        Returns a tuple:
        state': the new state
        new hidden state
        observation
        """
        assert len(moves) == len(self.moving_players()), f'More players moved than allowed, moves={moves}'
        assert self.policy_deck_size == len(hidden_state.policy_deck), f'deck sizes not equal'
        assert self.policy_deck_size + len(hidden_state.discard_pile) + len(hidden_state.proposed_policies) \
            + self.fas_policy + self.lib_policy == DECK_SIZE
        components = [hidden_state.policy_deck, hidden_state.discard_pile, hidden_state.proposed_policies]
        assert sum(map(lambda l: l.count(Party.fascist), components)) + self.fas_policy == NUM_FAS_POLICY
        assert sum(map(lambda l: l.count(Party.liberal), components)) + self.lib_policy == NUM_LIB_POLICY
        if self.phase == Phase.nomination:
            return self.nominate_chancellor_transition(chancellor=moves[0].chancellor), hidden_state, None

        if self.phase == Phase.vote:
            return self.vote_transition(hidden_state=hidden_state, votes=moves)

        if self.phase == Phase.presidentSelectPolicy:
            return self.president_select_transition(hidden_state=hidden_state, discard_policy=moves[0].policy)

        if self.phase == Phase.chancellorSelectPolicy:
            return self.chancellor_select_transition(hidden_state=hidden_state, move=moves[0])

        if self.phase == Phase.veto:
            return self.veto_transition(hidden_state=hidden_state, veto=moves[0].veto)

        if self.phase == Phase.presidentPower:
            return self.president_power_transition(hidden_state=hidden_state, power=moves[0])

        assert False, f'Invalid phase={self.phase}'

    def __str__(self):
        return '<SecretHitlerState ' + ' '.join(f'{k}={v}' for k, v in sorted(self.__dict__.items())) + '>'
