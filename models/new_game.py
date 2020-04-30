class NewGame:
    """
    NewGame object passed to soket via 'addNewGame'
    """
    def __init__(self, gameName='Bot Game', flag=None, minPlayersCount=5, excludedPlayerCount=[6, 7, 8, 9, 10], maxPlayersCount=5, experiencedMode=True, disableChat=False, disableObserver=False, isTourny=False, isVerifiedOnly=False, disableGamechat=False, rainbowgame=False, blindMode=False, flappyMode=False, flappyOnlyMode=False, timedMode=False, casualGame=False, rebalance6p=True, rebalance7p=False, rebalance9p2f=True, eloSliderValue=None, unlistedGame=False, privatePassword=False):
        self.gameName = gameName
        self.flag = flag
        self.minPlayersCount = minPlayersCount
        self.excludedPlayerCount = excludedPlayerCount
        self.maxPlayersCount = maxPlayersCount
        self.experiencedMode = experiencedMode
        self.disableChat = disableChat
        self.disableObserver = disableObserver
        self.isTourny = isTourny
        self.isVerifiedOnly = isVerifiedOnly
        self.disableGamechat = disableGamechat
        self.rainbowgame = rainbowgame
        self.blindMode = blindMode
        self.flappyMode = flappyMode
        self.flappyOnlyMode = flappyOnlyMode
        self.timedMode = timedMode
        self.casualGame = casualGame
        self.rebalance6p = rebalance6p
        self.rebalance7p = rebalance7p
        self.rebalance9p2f = rebalance9p2f
        self.eloSliderValue = eloSliderValue
        self.unlistedGame = unlistedGame
        self.privatePassword = privatePassword