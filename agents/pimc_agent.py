import logging
import numpy as np
from typing import Tuple
from tqdm import tqdm
from . import Agent
from .mcts_common import determinization_iterator
from secrethitler import SecretHitlerState, SecretRole, HiddenSecretHitlerState
OPPONENT_TREMBLE = 0.1


logger = logging.getLogger(__name__)


def get_opponent_moves_probs(state: SecretHitlerState, player: int, hidden_state: HiddenSecretHitlerState, no_tremble=False):
    legal_actions = state.legal_actions(player=player, hidden_state=hidden_state)
    if len(legal_actions) == 1:
        return legal_actions, np.ones(1)

    move_probs = np.ones(len(legal_actions))
    move_probs /= np.sum(move_probs)
    if no_tremble:
        return legal_actions, move_probs

    tremble = np.ones(len(legal_actions)) / len(legal_actions)
    return legal_actions, (1 - OPPONENT_TREMBLE) * move_probs + OPPONENT_TREMBLE * tremble


def select_opponent_move(state, hidden_state: HiddenSecretHitlerState, player, no_tremble=False):
    moves, probs = get_opponent_moves_probs(state, player, no_tremble=no_tremble, hidden_state=hidden_state)
    return moves[np.random.choice(len(moves), p=probs)]


class Node:
    def __init__(self, legal_actions, incoming_edge, parent, is_terminal, terminal_value=None):
        self.parent = parent
        self.incoming_edge = incoming_edge
        self.is_terminal = is_terminal
        if self.is_terminal:
            self.terminal_value = terminal_value
        else:
            self.choose_counts = {action: 0 for action in legal_actions}
            self.total_payoffs = {action: 0.0 for action in legal_actions}
            self.legal_actions = legal_actions
            self.children = {}
            self.total_choices = 0

    def select_move(self):
        ucb_cur_max = -float('inf')
        best_move = None
        unseen_moves = []
        for move in self.legal_actions:
            choose_count = self.choose_counts[move]
            if choose_count == 0:
                unseen_moves.append(move)
                continue
            ucb_val = self.total_payoffs[move] / self.choose_counts[move] + \
                (2*np.log(self.total_choices)/self.choose_counts[move])**0.5
            if ucb_val > ucb_cur_max:
                ucb_cur_max = ucb_val
                best_move = move
        if len(unseen_moves) != 0:
            return unseen_moves[np.random.choice(len(unseen_moves))]
        return best_move

    def __str__(self):
        return '<Node ' + ' '.join(f'{k}={v}' for k, v in sorted(self.__dict__.items())) + '>'


def next_node(node: Node, state: SecretHitlerState, hidden_state: HiddenSecretHitlerState, player: int, move)\
        -> Tuple[Node, SecretHitlerState, HiddenSecretHitlerState, bool]:
    moves = [move if p == player else select_opponent_move(state=state, player=p, hidden_state=hidden_state)
             for p in state.moving_players()]
    state, hidden_state, _ = state.transition(moves=moves, hidden_state=hidden_state)
    while not state.is_terminal() and player not in state.moving_players():
        moves = [select_opponent_move(state=state, player=p, hidden_state=hidden_state) for p in state.moving_players()]
        state, hidden_state, _ = state.transition(moves=moves, hidden_state=hidden_state)

    key = (move, hash(state), hash(hidden_state))
    if key in node.children:
        return node.children[key], state, hidden_state, False

    is_terminal = state.is_terminal()
    legal_actions = None if is_terminal else state.legal_actions(player=player, hidden_state=hidden_state)
    terminal_value = state.terminal_value(hidden_state)[player] if is_terminal else None
    new_node = Node(legal_actions, key, node, is_terminal, terminal_value)
    node.children[key] = new_node
    return new_node, state, hidden_state, True


def find_leaf_and_payoff(node, state, hidden_state: HiddenSecretHitlerState, player, node_value_func):
    if node.is_terminal:
        assert state.is_terminal(), "Terminal node not terminal"
        return node, node.terminal_value

    move = node.select_move()
    new_node, next_state, next_hidden_state, is_new = next_node(node, state, hidden_state, player, move)
    if is_new:
        payoff = node_value_func(state, hidden_state, player)
        return new_node, payoff

    return find_leaf_and_payoff(new_node, next_state, next_hidden_state, player, node_value_func)


def search_and_backprop(node, state, hidden_state: HiddenSecretHitlerState, player, node_value_func):
    node, payoff = find_leaf_and_payoff(node, state, hidden_state, player, node_value_func)
    while node.parent is not None:
        parent_action, _, _ = node.incoming_edge
        node.parent.total_choices += 1
        node.parent.choose_counts[parent_action] += 1
        node.parent.total_payoffs[parent_action] += payoff
        node = node.parent


NUM_PLAYOUTS = 1


def playout_value_func(root_state, root_hidden_state: HiddenSecretHitlerState, player):
    total_payoff = 0
    for _ in range(NUM_PLAYOUTS):
        state = root_state
        hidden_state = root_hidden_state
        while not state.is_terminal():
            moves = [select_opponent_move(state=state, player=p, hidden_state=hidden_state) for p in state.moving_players()]
            state, hidden_state, _ = state.transition(moves=moves, hidden_state=hidden_state)
        total_payoff += state.terminal_value(hidden_state)[player]
    return total_payoff


def search_mcts(state, player, hidden_roles, node_value_func, legal_actions, num_searches, deck_belief, president_pass):
    root = Node(legal_actions, None, None, is_terminal=False)
    for hidden_state in tqdm(determinization_iterator(hidden_roles, num_searches, state, legal_actions, deck_belief, president_pass),
                             desc='Searching', total=num_searches, disable=None, leave=False):
        if state.legal_actions(player=player, hidden_state=hidden_state) == legal_actions:
            search_and_backprop(root, state, hidden_state, player, node_value_func)
    return root.select_move()


class PIMCAgentBase(Agent):
    def __init__(self, player_id: int, num_players: int, secret_role: SecretRole, iterations=1000, name='PIMC Agent'):
        super().__init__(player_id, name, secret_role, num_players)
        self.iterations = iterations

    def get_action(self, state, legal_actions):
        if len(legal_actions) == 1:
            return legal_actions[0]
        move = search_mcts(state, self.player_id, self.hidden_role_beliefs, playout_value_func, legal_actions,
                           self.iterations, self.deck_knowledge, self.president_pass)
        logger.info(f'{self.name}:{self.player_id} has chosen {move}')
        return move


class PIMCAgent100(PIMCAgentBase):
    def __init__(self, player_id: int, num_players: int, secret_role: SecretRole):
        super().__init__(player_id, num_players, secret_role, 100, 'PIMC-100 Agent')


class PIMCAgent10000(PIMCAgentBase):
    def __init__(self, player_id: int, num_players: int, secret_role: SecretRole):
        super().__init__(player_id, num_players, secret_role, 10000, 'PIMC-10000 Agent')
