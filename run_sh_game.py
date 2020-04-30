"""Run Secret Hitler Game

Usage:
  run_sh_game <agent>... [options]
  run_sh_game --random [options]
  run_sh_game -h | --help
  run_sh_game -v | --versions

Options:
  -h --help                     Show this screen.
  -v --version                  Show version.
  -r --roles=<roles>            Set the role of each agent (e.g. l,l,l,f,h).
  -l --log=<level>              Set the log level [default: INFO].
  -n --games=<num_games>        Set the number of games to play. [default: 1]
  --random                      Randomize number and type of agents.
  --enable-mongo                Send game data to mongodb.
  --mongo-user=<user>           Set mongodb user.
  --mongo-password=<password>   Set mongodb password.
  --mongo-host=<host>           Set mongodb host [default: localhost].
  --mongo-port=<port>           Set mongodb port [default: 27017].
"""
import logging
import random
import time
from typing import List, Tuple
from pymongo import MongoClient, errors
from docopt import docopt

from battlefield import run_game
from agents import SelfishAgent, RandomAgent, SOISMCTSAgent100, SOISMCTSAgent10000, PIMCAgent10000, PIMCAgent100, Agent
from secrethitler import SecretRole, SecretHitlerState, SECRET_HITLER_POSSIBLE_ROLES, HiddenSecretHitlerState, \
    POSSIBLE_DECKS, PolicyDeck, DECK_SIZE, Party, Phase

HIDDEN_STATE_MAP = {
    'h': SecretRole.hitler,
    'f': SecretRole.fascist,
    'l': SecretRole.liberal,
    '': None
}

AGENT_MAP = {
    'random': RandomAgent,
    'selfish': SelfishAgent,
    # 'pimc': PIMCAgent10000,
    'soismcts': SOISMCTSAgent10000
}


def get_hidden_state(roles: List[str]) -> Tuple[SecretRole]:
    hidden_roles = [HIDDEN_STATE_MAP[r] for r in roles]

    possible_assignments = []
    for role_assignment in SECRET_HITLER_POSSIBLE_ROLES[len(roles)]:
        valid = True
        for proposed, given in zip(role_assignment, hidden_roles):
            if given is not None and proposed != given:
                valid = False
                break
        possible_assignments.append(role_assignment) if valid else None

    if len(possible_assignments) == 0:
        print(f'Role list is invalid. Incorrect number of roles. \n{__doc__}')
        exit(1)

    return tuple(random.choice(possible_assignments))


def push_game_summary_data(num_players: int, state: SecretHitlerState, agents: List[Agent], mongo_client: MongoClient, retries=0):
    if retries > 5:
        logging.error(f'Retry limit exceeded. Moving on.')
        return
    secrethitler = mongo_client.secrethitler2
    game_summaries = secrethitler.game_summaries
    game_summary = {
        'num_players': num_players,
        'winning_party': state.game_end.name,
        'win_reason': state.game_end_reason.name,
        'players': [{'name': agent.name, 'role': agent.secret_role.name} for agent in agents]
    }
    logging.debug(f'pushing game_summary={game_summary} to mongo')
    try:
        return game_summaries.insert_one(game_summary).inserted_id
    except errors.ServerSelectionTimeoutError or errors.AutoReconnect as e:
        logging.error(e)
        time.sleep(random.randint(10, 120))
        push_game_summary_data(num_players, state, agents, mongo_client, retries=retries + 1)


def push_agent_summary_data(state: SecretHitlerState, agents: List[Agent], mongo_client: MongoClient):
    secrethitler = mongo_client.secrethitler2
    agent_summaries = secrethitler.agent_summaries
    for agent in agents:
        win = agent.party == state.game_end
        reason = state.game_end_reason.name
        agent_data = {'agent': agent.name, 'secret_role': agent.secret_role.name}
        update = {
            '$setOnInsert': agent_data,
            '$inc':
                {
                    'total_wins' if win else 'total_losses': 1,
                    f'win_reasons.{reason}' if win else f'loss_reasons.{reason}': 1,
                    f'{state.starting_num_players}p.wins' if win else f'{state.starting_num_players}p.losses': 1,
                    f'{state.starting_num_players}p.win_reasons.{reason}' if win
                    else f'{state.starting_num_players}p.loss_reasons.{reason}': 1,
                }
        }
        logging.debug(f'pushed agent_summary={update} to mongo')

        def _push_agent(a, query, retries=0):
            if retries > 5:
                logging.error(f'Retry limit exceeded. Moving on.')
                return
            try:
                agent_summaries.update_one(a, query, upsert=True)
            except errors.ServerSelectionTimeoutError or errors.AutoReconnect as e:
                logging.error(e)
                time.sleep(random.randint(10, 120))
                _push_agent(a, query, retries=retries + 1)

        _push_agent(agent_data, update, retries=0)


def push_data_to_mongo(number_players: int, state: SecretHitlerState, agents: List[Agent], mongo_client: MongoClient):
    push_game_summary_data(num_players=number_players, state=state, agents=agents, mongo_client=mongo_client)
    push_agent_summary_data(state=state, agents=agents, mongo_client=mongo_client)


if __name__ == '__main__':
    # TODO: allow configuration for a subset of agents chosen at random
    args = docopt(__doc__, version='Run Secret Hitler Game 0.1')

    numeric_level = getattr(logging, args['--log'].upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {args["--log"]}')
    logging.basicConfig(level=numeric_level)
    logging.debug(f'args={args}')

    for i in range(int(args['--games'])):
        start_time = time.time()
        logging.info(f'========================= Game {i} Started =========================')
        agents = args['<agent>'] if not args['--random'] \
            else [random.choice([*AGENT_MAP]) for _ in range(random.randrange(5, 11))]
        logging.info(f'agents={agents}')
        role_list = args['--roles'].lower().split(',') if args['--roles'] is not None else ['' for _ in range(len(agents))]

        num_players = len(agents)
        if num_players != len(role_list):
            print(f'Agent list and Role list must be the same length.\n{__doc__}')
            exit(1)
        if num_players not in range(5, 11):
            print(f'Invalid number of players: {num_players}. Only 5 - 10 players allowed.\n{__doc__}')
            exit(1)

        for role in role_list:
            if role not in HIDDEN_STATE_MAP.keys():
                print(f'Role list may only contain {HIDDEN_STATE_MAP.keys()}\n{__doc__}')
                exit(1)
        for agent in agents:
            if agent not in AGENT_MAP.keys():
                print(f'Agent list may only contain {AGENT_MAP.keys()}\n{__doc__}')
                exit(1)

        hidden_roles = get_hidden_state(role_list)
        policy_deck = PolicyDeck(random.choice(list(filter(lambda d: len(d) == DECK_SIZE, POSSIBLE_DECKS))))
        agent_instances = [AGENT_MAP[agt](player_id=i, num_players=num_players, secret_role=hidden_roles[i])
                           for i, agt in enumerate(agents)]
        hidden_state = HiddenSecretHitlerState(hidden_roles=hidden_roles, policy_deck=policy_deck, discard_pile=[],
                                               proposed_policies=())
        state = SecretHitlerState.start_state(num_players=num_players)

        for agent in agent_instances:
            if (num_players < 7 and agent.secret_role == SecretRole.hitler) or agent.secret_role == SecretRole.fascist:
                agent.communicate_hidden_state(hidden_role=hidden_state.hidden_roles)

        terminal_value, state = \
            run_game(state=state, hidden_state=hidden_state, agents=agent_instances)
        logging.info(f'=============== Game {i} finished in {time.time() - start_time} seconds =====================\n')

        if args['--enable-mongo']:
            logging.info(f'====================== Started pushing results of game {i} to Mongo =======================')
            uri = f'mongodb://{args["--mongo-user"]}:{args["--mongo-password"]}@{args["--mongo-host"]}:{args["--mongo-port"]}'
            client = MongoClient(uri)
            push_data_to_mongo(number_players=num_players, state=state, agents=agent_instances, mongo_client=client)
            logging.info(f'================== Finished pushing results of game {i} to Mongo ======================\n\n')


