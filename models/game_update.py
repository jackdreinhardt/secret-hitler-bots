class Struct:
    """
    Struct object. Takes a dictionary and maps it to a class object.
    """
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @classmethod
    def from_json(cls, data):
        return cls(**data)

class Chats:
    """
    Chats object nested within GameUpdate object.
    """
    def __init__(self, chat, **kwargs):
        self.__dict__.update(kwargs)
        self.chat = chat

    @classmethod
    def from_json(cls, data):
        if type(data['chat']) == str:
            data['chat'] = [{'text': data['chat'], 'type': 'user'}]
        chat = list(map(Struct.from_json, data.pop('chat')))
        return cls(chat, **data)

class PublicPlayersState:
    """
    PublicPlayersState object nested within GameUpdate object.
    """
    def __init__(self, cardStatus, **kwargs):
        self.__dict__.update(kwargs)
        self.cardStatus = cardStatus

    @classmethod
    def from_json(cls, data):
        cardStatus = Struct.from_json(data.pop('cardStatus'))
        return cls(cardStatus, **data)

class CardFlingerState:
    """
    CardFlingerState object nested within GameUpdate object.
    """
    def __init__(self, cardStatus, **kwargs):
        self.__dict__.update(kwargs)
        self.cardStatus = cardStatus

    @classmethod
    def from_json(cls, data):
        cardStatus = Struct.from_json(data.pop('cardStatus'))
        return cls(cardStatus, **data)

class TrackState:
    """
    TrackState object nested within GameUpdate object.
    """
    def __init__(self, enactedPolicies, **kwargs):
        self.__dict__.update(kwargs)
        self.enactedPolicies = enactedPolicies

    @classmethod
    def from_json(cls, data):
        enactedPolicies = list(map(Struct.from_json, data.pop('enactedPolicies')))
        return cls(enactedPolicies, **data)


class GameUpdate:
    """
    GameUpdate object received from socket. Has game state information along with other information
    """
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @classmethod
    def from_json(cls, data):
        chats = []
        try:
            chats = list(map(Chats.from_json, data.pop('chats')))
        except:
            pass

        playersState = []
        try:
            playersState = list(map(Struct.from_json, data.pop('playersState')))
        except:
            pass

        cardFlingerState = []
        try: 
            cardFlingerState = list(map(CardFlingerState.from_json, data.pop('cardFlingerState')))
        except:
            pass

        args = {   
            'gameState':Struct.from_json(data.pop('gameState')),
            'chats':chats,
            'general':Struct.from_json(data.pop('general')),
            'customGameSettings':Struct.from_json(data.pop('customGameSettings')),
            'publicPlayersState':list(map(PublicPlayersState.from_json, data.pop('publicPlayersState'))),
            'playersState':playersState,
            'trackState':TrackState.from_json(data.pop('trackState')),
            'cardFlingerState':cardFlingerState,
            **data
        }
        return cls(**args)


"""
Full GameUpdate Model at https://github.com/cozuya/secret-hitler/blob/master/docs/model-info.txt

gameState
    isStarted bool
    isCompleted bool
    isVetoEnabled bool
    isTracksFlipped bool
    isGameFrozen bool
    pendingChancellorIndex number 
    timedModeEnabled bool
    phase string ?
    previousElectedGovernment array of numbers, 1st is pres 2nd is chanc,
    presidentIndex number
    undrawnPolicyCount number
    specialElectionFormerPresidentIndex number
    audioCue string no op - a hint for the front end to play a sound
flappyState
    liberalScore number
    fascistScore number
    pylonDensity number default 1
    flapDistance number default 1
chats array
    chat string
    type string
    gameChat bool
    isClaim bool
    isBroadcast bool
    timestamp time
general
    lastModPing date
    isVerifiedOnly bool
    blindMode bool
    name string
    isRemade bool, so that people can't click remake after its remade
    gameCreatorBlacklist array of strings of usernames
    replacementNames array of strings of animals to be used to replace player names in blind mode
    minPlayersCount number 5-10
    maxPlayersCount number 5-10
    excludedPlayerCount array of numbers
    status string
    whitelistedPlayers array of strings (userNames)
    uid string
    timedMode number
    rainbowgame bool
  private bool
    gameCreatorName string
    timeStarted date
    timeCreated date
    experiencedMode bool
    casualGame bool
    disableChat bool
    disableGamechat bool
    disableObserver bool
    playerCount number 5-10
    type number refers to fasctrack
    livingPlayerCount number
    electionCount number, starts at 0
    privateOnly bool only anons can play
    isTourny bool
    rebalance6p bool
    rebalance7p bool
    rebalance9p bool
    rerebalance9p bool
    tournyInfo
        round number
        showOtherTournyTable bool
        queuedPlayers array of objects
        isCancelled bool
        isRound1TableThatFinished2nd bool
seatedPlayers array 5-10
    obj
        connected bool
        userName string
    ...
trackState
    liberalPolicyCount number
    electionTrackerCount number
    fascistPolicyCount number
    enactedPolicies array
        location string offscreen center liberal0 ... fascist0 ...
remakeData array
    obj
        userName string
        isRemaking bool
        remakeTime int (Date)
publicPlayersState array
    obj
        pingTime number using getTime()
        governmentStatus string isPendingPresident isPendingChancellor
        isDead bool
        isConfetti bool
        connected bool
        isLoader bool
        leftGame bool
        userName string
        previousGovernmentStatus string wasPresident wasChancellor
        cardStatus
            cardDisplayed bool
            isFlipped bool
            cardFront string
            cardBack
                icon number
                roleName string
                team string
playersState (see private)
publicCardflingerState object
cardflingerState (see private)
private
    timerId number
    reports object
    _chancellorPlayerName string (bug resolution)
    timeout object
    policies array
    currentElectionPolicies array
  privatePassword string
    unSeatedGameChats array
        chat string
        timestamp time
    votesPeeked
    gameFrozen
    seatedPlayers array 5-10
        userName string
        connected bool
        policyNotification bool
        wonGame bool
        role obj
            icon number
            cardName string
            team string
        gameChats array of chat objects
        governmentStatus string isPresident isChancellor isSelectingChancellor isSelectingPresidentDiscard isSelectingChancellorDiscard
        voteStatus
            hasVoted bool
            didVoteYes bool
        reportedGame bool
        wasInvestigated bool
        playersState array 5-10
            obj
                cardBack object
                notificationStatus string outline around player
                nameStatus string fascist hitler disabled liberal
                hasVoted bool
                policyNotification bool
        cardFlingerState array
            obj
                position string middle-far-left middle-left middle-center middle-right middle-far-right
                notificationStatus
                cardStatus
                    isFlipped bool
                    cardFront string
                    cardBack string
"""
