from typing import List
import logging
from secrethitler import SecretHitlerState, HiddenSecretHitlerState

logger = logging.getLogger(__name__)


def run_game(state: SecretHitlerState, hidden_state: HiddenSecretHitlerState, agents: List):
    logger.info(f'game started with: state={state}')
    logger.info(f'game started with: hidden_state={hidden_state}')
    logger.info(f'game started with: agents={[agent.__str__() for agent in agents]}')

    while not state.is_terminal():
        logger.info(f'current state={state}')
        logger.info(f'hidden_state={hidden_state}')

        # moving agents choose their actions
        moving_players = state.moving_players()
        moves = [
            agents[player].get_action(state, state.legal_actions(hidden_state=hidden_state, player=player))
            for player in moving_players
        ]

        # state is transitioned
        new_state, new_hidden_state, observation = state.transition(moves=moves, hidden_state=hidden_state)

        # private observations are communicated to moving players
        for player in moving_players:
            agents[player].handle_observation(observation)

        # public observations are communicated to all players
        for agent in agents:
            agent.handle_transition(old_state=state, new_state=new_state, old_hidden_state=hidden_state,
                                    new_hidden_state=new_hidden_state, moves=moves)
        state = new_state
        hidden_state = new_hidden_state

    logger.info(f'ending game state={state}')
    logger.info(f'game ended in a {state.game_end.name} victory. {state.game_end_reason}')
    return state.terminal_value(hidden_state), state
