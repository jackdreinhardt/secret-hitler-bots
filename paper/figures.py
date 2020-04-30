import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from itertools import cycle


def add_hatches(bars, categories=1, density=3, legend=True):
    hatches = []
    for hatch in ['x'*density, '\\'*density, '', '-'*density]:
        hatches.extend([hatch] * categories)

    for hatch, bar in zip(hatches, bars.patches):
        bar.set_hatch(hatch)
    if legend:
        bars.legend()


def overall_win_rates(save=False):
    df = pd.read_csv('data/latest_data_overall_win_rate.csv')
    agent_names = [a for a in df['agent']]
    win_rate = [[w for w in df['win_rate']]]
    df = pd.DataFrame(data=win_rate, columns=agent_names)

    bar = sns.barplot(data=df, color='black')
    bar.set(xlabel='Agent', ylabel='Win Rate')
    add_hatches(bar, legend=False)

    plt.show()
    if save:
        bar.get_figure().savefig('paper/img/overall_win_rate.png', dpi=300)


def win_rate_by_player_number(save=False):
    win_rates = np.array(
        [['Random', 5, 40],
         ['Random', 6, 35],
         ['Random', 7, 30],
         ['Random', 8, 25],
         ['Random', 9, 20],
         ['Random', 10, 15],
         ['Selfish', 5, 45],
         ['Selfish', 6, 40],
         ['Selfish', 7, 35],
         ['Selfish', 8, 30],
         ['Selfish', 9, 25],
         ['Selfish', 10, 20],
         ['SO-ISMCTS', 5, 45],
         ['SO-ISMCTS', 6, 40],
         ['SO-ISMCTS', 7, 35],
         ['SO-ISMCTS', 8, 30],
         ['SO-ISMCTS', 9, 25],
         ['SO-ISMCTS', 10, 20],
         ['SO-ISMCTS++', 5, 45],
         ['SO-ISMCTS++', 6, 40],
         ['SO-ISMCTS++', 7, 35],
         ['SO-ISMCTS++', 8, 30],
         ['SO-ISMCTS++', 9, 25],
         ['SO-ISMCTS++', 10, 20]])
    df = pd.DataFrame(data=win_rates, columns=['Agent', 'Number of Players', 'Win Rate'])
    bar = sns.barplot(x="Number of Players", y="Win Rate", hue="Agent", data=df, palette=['black'] * 4)
    add_hatches(bar, categories=6, density=4)

    plt.show()
    if save:
        bar.get_figure().savefig('paper/img/by_player_num_win_rate.png', dpi=300)


def win_rate_by_role(save=False):
    df = pd.read_csv('data/latest_data_secret_role_win_rate.csv')
    bar = sns.barplot(x="Secret Role", y="Win Rate", hue="Agent", data=df, palette=['black'] * 3)
    add_hatches(bar, categories=3, density=3)

    plt.show()
    if save:
        bar.get_figure().savefig('paper/img/by_secret_role_win_rate.png', dpi=300)


def win_rate_by_num_players(save=False):
    df = pd.read_csv('data/latest_data_num_players_win_rate.csv')
    new_df = [] # to get confidence intervals in figure
    for row in df.itertuples(index=False):
        for _ in range(0, row.wins):
            new_df.append({'Agent': row.Agent, 'Number of Players': row[1], 'Win Rate': 1})
        for _ in range(0, row.losses):
            new_df.append({'Agent': row.Agent, 'Number of Players': row[1], 'Win Rate': 0})
    new_df = pd.DataFrame(new_df)
    print(new_df)
    line = sns.lineplot(x="Number of Players", y="Win Rate", hue='Agent', data=new_df)
    line.legend(loc='lower right')

    plt.show()
    if save:
        line.get_figure().savefig('paper/img/by_number_players_win_rate.png', dpi=300)


if __name__ == "__main__":
    sns.set(context='paper', style='ticks', palette='colorblind')
    overall_win_rates(save=True)
    win_rate_by_role(save=True)
    win_rate_by_num_players(save=True)

