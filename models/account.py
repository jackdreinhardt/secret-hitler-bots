class GameSettings:
    """
    GameSettings object within the Account object
    """
    def __init__(self, gameFilters={}, gameNotes={}, blacklist=[], tourneyWins=[], playerNotes=[], soundStatus='pack2', isPrivate=False):
        self.gameFilters = gameFilters
        self.gameNotes = gameNotes
        self.blacklist = blacklist
        self.tourneyWins = tourneyWins
        self.playerNotes = playerNotes
        self.soundStatus = soundStatus
        self.isPrivate = isPrivate

class Account:
    """
    Account object passed to socket via 'sendUser'
    """
    def __init__(self, userName='Bot', verified=False, staffRole='', hasNotDismissedSignupModal=False, gameFilters={}, gameNotes={}, blacklist=[], tourneyWins=[], playerNotes=[], soundStatus='pack2', isPrivate=False):
        self.userName = userName
        self.verified = verified
        self.staffRole = staffRole
        self.hasNotDismissedSignupModal = hasNotDismissedSignupModal
        self.gameSettings = \
            GameSettings(gameFilters=gameFilters, \
                         gameNotes=gameNotes, \
                         blacklist=blacklist,
                         tourneyWins=tourneyWins, \
                         playerNotes=playerNotes, \
                         soundStatus=soundStatus, \
                         isPrivate=False)


"""
Full Account Model at https://github.com/cozuya/secret-hitler/blob/master/models/account.js

const Account = new Schema({
    username: {
        type: String,
        required: true,
        unique: true
    },
    password: String,
    isLocal: Boolean,
    staffRole: String,
    isContributor: Boolean,
    hasNotDismissedSignupModal: Boolean,
    gameSettings: {
        staffDisableVisibleElo: Boolean,
        staffDisableStaffColor: Boolean,
        staffIncognito: Boolean,
        isRainbow: Boolean,
        newReport: Boolean,
        customCardback: String,
        customCardbackSaveTime: String,
        customCardbackUid: String,
        enableTimestamps: Boolean,
        enableRightSidebarInGame: Boolean,
        disablePlayerColorsInChat: Boolean,
        disablePlayerCardbacks: Boolean,
        disableHelpMessages: Boolean,
        disableHelpIcons: Boolean,
        disableConfetti: Boolean,
        disableCrowns: Boolean,
        disableSeasonal: Boolean,
        disableAggregations: Boolean,
        soundStatus: String,
        unbanTime: Date,
        unTimeoutTime: Date,
        fontSize: Number,
        fontFamily: String,
        isPrivate: Boolean,
        privateToggleTime: Number,
        blacklist: Array,
        tournyWins: Array,
        hasChangedName: Boolean,
        previousSeasonAward: String,
        specialTournamentStatus: String,
        disableElo: Boolean,
        fullheight: Boolean,
        safeForWork: Boolean,
        gameFilters: {
            pub: Boolean,
            priv: Boolean,
            unstarted: Boolean,
            inprogress: Boolean,
            completed: Boolean,
            customgame: Boolean,
            casualgame: Boolean,
            timedMode: Boolean,
            standard: Boolean,
            rainbow: Boolean
        },
        gameNotes: {
            top: Number,
            left: Number,
            width: Number,
            height: Number
        },
        playerNotes: Array,
        ignoreIPBans: Boolean,
        truncatedSize: Number
    },
    verification: {
        email: String
    },
    signupIP: String,
    lastConnectedIP: String,
    ipHistory: Array,
    verified: Boolean,
    isBanned: Boolean,
    isTimeout: Date,
    touLastAgreed: String,
    bio: String,
    games: Array,
    wins: Number,
    losses: Number,
    rainbowWins: Number,
    rainbowLosses: Number,
    winsSeason1: Number,
    lossesSeason1: Number,
    rainbowWinsSeason1: Number,
    rainbowLossesSeason1: Number,
    winsSeason2: Number,
    lossesSeason2: Number,
    rainbowWinsSeason2: Number,
    rainbowLossesSeason2: Number,
    winsSeason3: Number,
    lossesSeason3: Number,
    rainbowWinsSeason3: Number,
    rainbowLossesSeason3: Number,
    winsSeason4: Number,
    lossesSeason4: Number,
    rainbowWinsSeason4: Number,
    rainbowLossesSeason4: Number,
    winsSeason5: Number,
    lossesSeason5: Number,
    rainbowWinsSeason5: Number,
    rainbowLossesSeason5: Number,
    winsSeason6: Number,
    lossesSeason6: Number,
    rainbowWinsSeason6: Number,
    rainbowLossesSeason6: Number,
    winsSeason7: Number,
    lossesSeason7: Number,
    rainbowWinsSeason7: Number,
    rainbowLossesSeason7: Number,
    winsSeason8: Number,
    lossesSeason8: Number,
    rainbowWinsSeason8: Number,
    rainbowLossesSeason8: Number,
    winsSeason9: Number,
    lossesSeason9: Number,
    rainbowWinsSeason9: Number,
    rainbowLossesSeason9: Number,
    previousDayElo: Number,
    created: Date,
    isOnFire: Boolean,
    lastCompletedGame: Date,
    lastVersionSeen: String,
    isFixed: Boolean,
    eloSeason: Number,
    eloOverall: Number,
    hashUid: String,
    discordUsername: String,
    discordDiscriminator: String,
    discordMfa_enabled: Boolean,
    discordUID: String,
    githubUsername: String,
    github2FA: Boolean,
    warnings: Array, // {text: String, moderator: String, time: Date, acknowledged: Boolean},
    primaryColor: String,
    secondaryColor: String,
    tertiaryColor: String,
    backgroundColor: String,
    textColor: String
});
"""