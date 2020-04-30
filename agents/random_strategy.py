import random
import time

def delay(func):
    def wrapper(*args, **kwargs):
        time.sleep(random.randint(1, 3))
        return func(*args, **kwargs)
    return wrapper

class RandomStrategy:
    def __init__(self):
        self.name = 'random'
        self.gameState = None

    @delay
    def vote(self):
        return random.randint(0, 1) == 1

    @delay
    def selectPlayer(self):
        return self.gameState.gameState.clickActionInfo[1][random.randint(0, len(self.gameState.gameState.clickActionInfo[1])-1)]

    @delay
    def selectChancellor(self):
        return self.selectPlayer()

    @delay
    def presidentSelectPolicy(self):
        return random.randint(0, 2)

    @delay
    def chancellorSelectPolicy(self):
        return random.randint(0, 1)

    @delay
    def selectPlayerToExecute(self):
        return self.selectPlayer()

    @delay
    def chancellorVoteOnVeto(self):
        return self.vote()

    @delay
    def presidentVoteOnVeto(self):
        return self.vote()

    @delay
    def selectPartyMembershipInvestigate(self):
        return self.selectPlayer()

    @delay
    def selectPartyMembershipInvestigateReverse(self):
        return self.selectPlayer()

    @delay
    def selectedSpecialElection(self):
        return self.selectPlayer()

    @delay
    def selectedPresidentVoteOnBurn(self):
        return self.vote()

