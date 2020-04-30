from math import comb, floor


def configurations(agents):
    c = 0
    for players in range(5, 11):
        c += comb(agents + players - 1, players) * players * comb(players-1, floor(float(players-1)/2) - 1)
    return c


if __name__ == '__main__':
    num_agents = 3
    print(configurations(num_agents))
