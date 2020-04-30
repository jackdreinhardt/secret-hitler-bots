"""Data Collection

Usage:
  data_collection <user> <password> [options]
  data_collection -h | --help
  data_collection -v | --versions

Options:
  -h --help                     Show this screen.
  -v --version                  Show version.
  -l --log=<level>              Set the log level [default: INFO].
  --mongo-host=<host>           Set mongodb host [default: localhost].
  --mongo-port=<port>           Set mongodb port [default: 27017].
"""
import logging
import time
from datetime import datetime
import pandas as pd
import statsmodels.stats.proportion as sm
from pymongo import MongoClient
from docopt import docopt
from pprint import pprint


logger = logging.getLogger(__name__)


def get_total_games(mongo_database):
    games = 0
    for doc in mongo_database.game_summaries.aggregate([{'$count': 'total_num_games'}]):
        games = doc["total_num_games"]
    print(f'Total Number of Games Played: {games}\n')

    with open("data/total_games.txt", "a") as outfile:
        outfile.write(f'{time.ctime(datetime.now().timestamp())}: {games}\n')

    return games


def get_win_reason_percentages(mongo_database, total_games):
    query = [{'$group':
             {
                '_id': {'win_reason': '$win_reason'},
                'number_wins': {'$sum': 1},
             }}]

    win_reasons = []
    for doc in mongo_database.game_summaries.aggregate(query):
        win_reasons.append([doc["_id"]["win_reason"], doc["number_wins"], doc["number_wins"]/float(total_games)])

    df = pd.DataFrame(data=win_reasons, columns=['win_reason', 'number_wins', 'percentage_of_total'])
    df.to_csv('data/latest_data_win_reason_percentages.csv', index=False)
    print(df, '\n')


def get_overall_win_rates(mongo_database):
    query = [{'$group':
             {
                '_id': {'agent': '$agent'},
                'wins': {'$sum': '$total_wins'},
                'losses': {'$sum': '$total_losses'}
             }}]

    data = [
        {
            'agent': doc['_id']['agent'], 'wins': doc['wins'], 'losses': doc['losses'],
            'win_rate': round(float(doc['wins']) / (doc['wins'] + doc['losses']), 3),
            'error': round(sm.proportion_confint(count=doc['wins'], nobs=doc['wins']+doc['losses'], alpha=0.05)[1]
                           - float(doc['wins']) / (doc['wins'] + doc['losses']), 3),
            'conf_int': sm.proportion_confint(count=doc['wins'], nobs=doc['wins']+doc['losses'], alpha=0.05)
        }
        for doc in mongo_database.agent_summaries.aggregate(query)
    ]
    df = pd.DataFrame(columns=['agent', 'wins', 'losses', 'win_rate', 'error', 'conf_int'], data=data)
    df = df.replace(to_replace=r'SO-ISMCTS-10000 Agent', value='SO-ISMCTS Agent')
    df.to_csv('data/latest_data_overall_win_rate.csv', index=False)
    print(df, '\n')


def get_secret_role_win_rate(mongo_database):
    query = [
        {
            '$group':
                {
                    '_id': {'agent': '$agent', 'secret_role': '$secret_role'},
                    'wins': {'$sum': '$total_wins'},
                    'losses': {'$sum': '$total_losses'}
                }
        }
    ]
    data = [
        {
            'Agent': doc['_id']['agent'], 'Secret Role': doc['_id']['secret_role'],
            'wins': doc['wins'], 'losses': doc['losses'],
            'Win Rate': round(float(doc['wins']) / (doc['wins'] + doc['losses']), 3),
            'error': round(sm.proportion_confint(count=doc['wins'], nobs=doc['wins']+doc['losses'], alpha=0.05)[1]
                           - float(doc['wins']) / (doc['wins'] + doc['losses']), 3),
            'conf_int': sm.proportion_confint(count=doc['wins'], nobs=doc['wins']+doc['losses'], alpha=0.05)
        }
        for doc in mongo_database.agent_summaries.aggregate(query)
    ]
    df = pd.DataFrame(columns=['Agent', 'Secret Role', 'wins', 'losses', 'Win Rate', 'error', 'conf_int'], data=data)
    df = df.replace(to_replace=r'SO-ISMCTS-10000 Agent', value='SO-ISMCTS Agent')
    df.to_csv('data/latest_data_secret_role_win_rate.csv', index=False)
    print(df, '\n')


def get_num_player_win_rate(mongo_database, n):
    query = [
        {
            '$group':
                {
                    '_id': {'agent': '$agent'},
                    'wins': {'$sum': f'${n}p.wins'},
                    'losses': {'$sum': f'${n}p.losses'}
                }
        }
    ]
    data = [
        {
            'Agent': doc['_id']['agent'], 'Number of Players': n, 'wins': doc['wins'], 'losses': doc['losses'],
            'Win Rate': round(float(doc['wins']) / (doc['wins'] + doc['losses']), 3),
            'error': round(sm.proportion_confint(count=doc['wins'], nobs=doc['wins'] + doc['losses'], alpha=0.05)[1]
                           - float(doc['wins']) / (doc['wins'] + doc['losses']), 3),
            'conf_int': sm.proportion_confint(count=doc['wins'], nobs=doc['wins'] + doc['losses'], alpha=0.05)
        }
        for doc in mongo_database.agent_summaries.aggregate(query)
    ]
    return pd.DataFrame(columns=['Agent', 'Number of Players', 'wins', 'losses', 'Win Rate', 'error', 'conf_int'], data=data)


def get_all_num_player_win_rate(mongo_database):
    df = pd.DataFrame()
    for p in range(5, 11):
        df = df.append(get_num_player_win_rate(mongo_database, p))
    df = df.replace(to_replace=r'SO-ISMCTS-10000 Agent', value='SO-ISMCTS Agent')
    df.to_csv('data/latest_data_num_players_win_rate.csv', index=False)
    print(df, '\n')


if __name__ == '__main__':
    args = docopt(__doc__, version='Data Collection 0.1')

    numeric_level = getattr(logging, args['--log'].upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {args["--log"]}')
    logging.basicConfig(level=numeric_level)
    logging.debug(f'args={args}')

    uri = f'mongodb://{args["<user>"]}:{args["<password>"]}@{args["--mongo-host"]}:{args["--mongo-port"]}'
    client = MongoClient(uri)

    secrethitler = client.secrethitler2

    total_games_played = get_total_games(secrethitler)
    get_win_reason_percentages(secrethitler, total_games_played)
    get_overall_win_rates(secrethitler)
    get_secret_role_win_rate(secrethitler)
    get_all_num_player_win_rate(secrethitler)

    total_win_and_loss_reasons_by_agent = [
        {
            '$group':
                {
                    '_id': {'agent': '$agent'},
                    'hitler_killed_wins': {'$sum': '$win_reasons.hitler_killed'},
                    'hitler_elected_wins': {'$sum': '$win_reasons.hitler_elected'},
                    'five_liberal_policies_wins': {'$sum': '$win_reasons.five_liberal_policies'},
                    'six_fascist_policies_wins': {'$sum': '$win_reasons.six_fascist_policies'},
                    'hitler_killed_losses': {'$sum': '$loss_reasons.hitler_killed'},
                    'hitler_elected_losses': {'$sum': '$loss_reasons.hitler_elected'},
                    'five_liberal_policies_losses': {'$sum': '$loss_reasons.five_liberal_policies'},
                    'six_fascist_policies_losses': {'$sum': '$loss_reasons.six_fascist_policies'}
                }
        }
    ]
    print(f'\nWin and Loss Reasons by Agent:')
    [pprint(doc) for doc in secrethitler.agent_summaries.aggregate(total_win_and_loss_reasons_by_agent)]


