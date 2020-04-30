import logging
import math
import itertools
from collections import defaultdict, deque
from tqdm import tqdm

from agents.mcts_common import random_choice, determinization_iterator, simulate
from agents.pimc_agent import PIMCAgent100
from agents.agent import Agent
from secrethitler import SecretRole, SecretHitlerState, HiddenSecretHitlerState, Phase, PolicyDeck, Party, PolicyChoiceAction

logger = logging.getLogger(__name__)


# TODO: find a better solution to this from within PolicyDeck
SIMULATED_HIDDEN_STATES = deque()  # needed for deterministic shuffles of policy deck
SIMULATED_GAME_STATES = deque()


class Node:
    def __init__(self, parent, incoming_edge):
        self.parent = parent
        self.incoming_edge = incoming_edge
        self.children = {}  # map from joint actions to child nodes
        self.total_reward = 0.0  # the total reward for the parent for selecting this action
        self.availability_count = 0
        self.visit_count = 0
        self.exp3_sum = defaultdict(lambda: defaultdict(lambda: 0.0))  # map from player to action to reward

    def compatible_children(self, game_state, hidden_state):
        moving_players = game_state.moving_players()
        return [
            moves
            for moves in itertools.product(*[
                game_state.legal_actions(hidden_state, player)
                for player in moving_players
            ])
        ]

    def unexplored_children(self, game_state, hidden_state):
        return [moves for moves in self.compatible_children(game_state, hidden_state) if moves not in self.children]

    def calculate_exp3_probs(self, game_state, hidden_state, player):
        available_actions = game_state.legal_actions(hidden_state, player)
        K = len(available_actions)
        n = self.visit_count
        if n == 0:
            gamma = 1.0
        else:
            gamma = min(1.0, math.sqrt(K * math.log(K) / (n * (math.e - 1))))

        eta = gamma / K
        probs = [
            (
                    gamma / K +
                    (1.0 - gamma) / sum([
                math.exp(min(eta * (self.exp3_sum[player][a] - self.exp3_sum[player][action]), 700))
                for a in available_actions
            ])
            )
            for action in available_actions
        ]
        return available_actions, probs

    def select_child(self, game_state, hidden_state):
        moving_players = game_state.moving_players()
        if len(moving_players) == 1:
            available_actions = self.compatible_children(game_state, hidden_state)
            if len(available_actions) == 1:
                return available_actions[0]

            return max(
                available_actions,
                # UCB1
                key=lambda action: (
                        (self.children[action].total_reward / self.children[action].visit_count) +
                        2000 * math.sqrt(
                    math.log(self.children[action].availability_count) / self.children[action].visit_count)
                )
            )
        else:
            move = ()
            for player in moving_players:
                actions, probs = self.calculate_exp3_probs(game_state, hidden_state, player)
                if len(actions) == 1:
                    chosen_move = actions[0]
                else:
                    chosen_move = random_choice(actions, p=probs)
                move += (chosen_move,)
            return move


def select_leaf(node, game_state, hidden_state):
    if game_state.is_terminal():
        return node, game_state, hidden_state
    if len(node.unexplored_children(game_state, hidden_state)) != 0:
        return node, game_state, hidden_state

    action = node.select_child(game_state, hidden_state)
    new_node = node.children[action]
    new_game_state, new_hidden_state, _ = game_state.transition(action, hidden_state)
    SIMULATED_GAME_STATES.appendleft(new_game_state)
    SIMULATED_HIDDEN_STATES.appendleft(new_hidden_state)
    return select_leaf(new_node, new_game_state, new_hidden_state)


def expand_if_needed(node, game_state, hidden_state):
    if game_state.is_terminal():
        return node, game_state, hidden_state
    unexplored_children = node.unexplored_children(game_state, hidden_state)

    action = random_choice(unexplored_children)

    new_node = Node(parent=node, incoming_edge=action)
    node.children[action] = new_node
    new_game_state, new_hidden_state, _ = game_state.transition(action, hidden_state)
    SIMULATED_GAME_STATES.appendleft(new_game_state)
    SIMULATED_HIDDEN_STATES.appendleft(new_hidden_state)
    return new_node, new_game_state, new_hidden_state


def backpropagate(initial_game_state, initial_hidden_state: HiddenSecretHitlerState, node, rewards):
    action_history = []
    while node.parent is not None:
        action_history.append(node.incoming_edge)
        node = node.parent
    action_history = action_history[::-1]

    game_state, hidden_state = initial_game_state, initial_hidden_state
    for action in action_history:
        moving_players = game_state.moving_players()
        for neighbor in node.compatible_children(game_state, hidden_state):
            if neighbor in node.children:
                node.children[neighbor].availability_count += 1

        node.children[action].visit_count += 1

        if len(moving_players) == 1:
            node.children[action].total_reward += rewards[moving_players[0]]
        else:
            for player, move in zip(moving_players, action):
                if move not in node.exp3_sum[player]:
                    node.exp3_sum[player][move] += rewards[player]
                else:
                    actions, probs = node.calculate_exp3_probs(game_state, hidden_state, player)
                    prob = probs[actions.index(move)]
                    node.exp3_sum[player][move] += rewards[player] / prob

        node = node.children[action]
        # this does not work due to randomization of deck shuffle
        # game_state, hidden_state, _ = game_state.transition(action, hidden_state)
        game_state = SIMULATED_GAME_STATES.pop()
        hidden_state = SIMULATED_HIDDEN_STATES.pop()


def search_ismcts(searcher, initial_game_state, possible_hidden_states, num_iterations, legal_actions, deck_beliefs, president_pass):
    root = Node(parent=None, incoming_edge=None)

    for initial_hidden_state in tqdm(determinization_iterator(possible_hidden_states, num_iterations, initial_game_state,
                                                              legal_actions, deck_beliefs, president_pass),
                                     desc='Searching', total=num_iterations, disable=None, leave=False):
        if initial_game_state.legal_actions(player=searcher, hidden_state=initial_hidden_state) == legal_actions:
            SIMULATED_HIDDEN_STATES.clear()
            node, game_state, hidden_state = select_leaf(root, initial_game_state, initial_hidden_state)
            node, game_state, hidden_state = expand_if_needed(node, game_state, hidden_state)
            rewards = simulate(game_state, hidden_state)
            backpropagate(initial_game_state, initial_hidden_state, node, rewards)

    moves = max(root.children, key=lambda action: root.children[action].visit_count)
    move = moves[initial_game_state.moving_players().index(searcher)]
    return move, root


class SOISMCTSAgentBase(Agent):
    def __init__(self, player_id: int, num_players: int, secret_role: SecretRole, iterations=1000, name='SO-ISMCTS Agent'):
        super().__init__(player_id, name, secret_role, num_players)
        self.iterations = iterations

    def get_action(self, state, legal_actions):
        if len(legal_actions) == 1:
            return legal_actions[0]
        action, _ = search_ismcts(self.player_id, state, self.hidden_role_beliefs, self.iterations,
                                  legal_actions, self.deck_knowledge, self.president_pass)
        logger.info(f'{self} has chosen {action}')
        return action


class SOISMCTSAgent100(SOISMCTSAgentBase):
    def __init__(self, player_id: int, num_players: int, secret_role: SecretRole):
        super().__init__(player_id, num_players, secret_role, 100, 'SO-ISMCTS-100 Agent')


class SOISMCTSAgent10000(SOISMCTSAgentBase):
    def __init__(self, player_id: int, num_players: int, secret_role: SecretRole):
        super().__init__(player_id, num_players, secret_role, 10000, 'SO-ISMCTS-10000 Agent')


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    # testing for SIMULATED_HIDDEN_STATES
    # hidden = HiddenSecretHitlerState(hidden_roles=(SecretRole.liberal, SecretRole.liberal, SecretRole.liberal,
    #                                                SecretRole.hitler, SecretRole.fascist),
    #                                  policy_deck=PolicyDeck([]), proposed_policies=(),
    #                                  discard_pile=[Party.liberal, Party.liberal, Party.fascist, Party.fascist,
    #                                                Party.fascist, Party.fascist, Party.fascist, Party.fascist])
    # s = SecretHitlerState(starting_num_players=5, current_num_players=3, president=1, chancellor=2, phase=Phase.vote,
    #                       fas_policy=5, lib_policy=4, chaos=0, game_end=None, prev_gov=(None, 4), alive_players=[1, 2, 3],
    #                       se_prev_pres=None, president_veto=True, game_end_reason=None, policy_deck_size=0)
    # agent = SOISMCTSAgentBase(player_id=1, num_players=5, secret_role=SecretRole.hitler)
    # while True:
    #     agent.get_action(s, s.legal_actions(hidden_state=hidden, player=agent.player_id))

    # "INFO:battlefield.tournament:current state=<SecretHitlerState alive_players=[0, 1, 2, 4, 5, 6, 8, 9] chancellor=2 chaos=2 current_num_players=8 fas_policy=5 game_end=None game_end_reason=None lib_policy=1 " \
    # "phase=Phase.vote policy_deck_size=3 powers=[<Power.none: 4>, <Power.investigate: 2>, <Power.investigate: 2>, <Power.specialelection: 3>, <Power.bullet: 1>, <Power.bullet: 1>] " \
    # "president=9 president_veto=True prev_gov=(5, 6) se_prev_pres=None starting_num_players=10 veto=True>\n",

    # ERROR CASE 1:
    # "INFO:battlefield.tournament:current state=<SecretHitlerState alive_players= chancellor=       se_prev_pres=None starting_num_players=8 veto=True>
    # "INFO:battlefield.tournament:hidden_state=<HiddenSecretHitlerState discard_pile=[] hidden_roles=() policy_deck=<PolicyDeck len=3> proposed_policies=[]>
    hidden = HiddenSecretHitlerState(hidden_roles=(SecretRole.fascist, SecretRole.liberal, SecretRole.liberal,
                                                   SecretRole.hitler, SecretRole.fascist, SecretRole.liberal,
                                                   SecretRole.liberal, SecretRole.liberal),
                                     policy_deck=PolicyDeck([Party.fascist, Party.fascist, Party.liberal]),
                                     proposed_policies=(Party.liberal, Party.fascist, Party.liberal),
                                     discard_pile=[Party.fascist, Party.fascist, Party.liberal,
                                                   Party.liberal, Party.liberal, Party.fascist])
    s = SecretHitlerState(starting_num_players=8, current_num_players=8, president=6, chancellor=7, phase=Phase.presidentSelectPolicy,
                          fas_policy=5, lib_policy=0, chaos=1, game_end=None, prev_gov=(6, 7), alive_players=[0, 1, 2, 3, 4, 5, 6, 7],
                          se_prev_pres=None, president_veto=True, game_end_reason=None, policy_deck_size=3)
    agent = PIMCAgent100(player_id=6, num_players=8, secret_role=SecretRole.liberal)

    while True:
        agent.get_action(s, s.legal_actions(hidden_state=hidden, player=agent.player_id))



