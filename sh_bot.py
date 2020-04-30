"""Secret Hitler Bot.

Usage:
  sh_bot new game <username> <password> [--scheme=<scheme>] [--host=<host>] [--strategy=<strategy>] [--log=<level>]
  sh_bot join game <gameuid> <username> <password> [--scheme=<scheme>] [--host=<host>] [--strategy=<strategy>] [--log=<level>]
  sh_bot -h | --help
  sh_bot -v | --version

Options:
  -h --help                       Show this screen
  -v --version                    Show version
  --scheme=<scheme>               Specify a network scheme [default: http]
  --host=<host>                   Specify a host [default: localhost:8080]
  --strategy=<strategy>           Specify an agent strategy to use [default: random]
  --log=<level>                   Specify logging level [default: INFO]
"""

from docopt import docopt
import socketio
import asyncio
import aiohttp
import logging
from util.json import JSON
from models.new_game import NewGame
from models.account import Account
from models.game_update import GameUpdate
from agents.random_strategy import RandomStrategy
from actions import Actions


class SecretHitlerBot:
    def __init__(self, username, password, scheme, host, new, gameuid, strategy='random', **kwargs):
        self.logger = logging.getLogger(__name__)
        if strategy == 'random':
            self.strategy = RandomStrategy()
        else:
            raise ValueError('invalid strategy')
        self.username = username
        self.password = password
        self.url = scheme + '://' + host
        self.createNewGame = new
        self.gameUID = gameuid
        self.logger.debug(f'url: {self.url}')
        self.lock = asyncio.Lock()
        self.sio = None
        self.inGame = False
        self.gameUpdate = None
        self.voted = False
        self.inUserList = False

    def register_socketio_events(self):
        @self.sio.event
        def connect():
            self.logger.log(25, 'connection established')

        @self.sio.event
        def disconnect():
            self.logger.log(25, 'disconnected from server')

        # if server requests user information, send user information
        @self.sio.event
        async def fetch_user():
            await self.sio.emit('getUserGameSettings') # to push user onto userList
            await self.sio.emit('confirmTOU')
            await self.sio.emit('hasSeenNewPlayerModal')
            await self.sio.emit('sendUser', Account(userName=self.username))

        # if server redirects to game, update user status
        @self.sio.event
        async def join_game_redirect(uid):
            self.logger.log(25, f'joining game {uid}')
            await self.sio.emit('updateSeatedUser', { "uid": uid })

        @self.sio.event
        def update_seat_for_user(success=True):
            if success:
                self.inGame = True

        @self.sio.event
        def user_list(data):
            self.logger.debug(data)
            for user in data['list']:
                if user['userName'] == self.username:
                    self.inUserList = True
                    return
            self.inUserList = False   

        @self.sio.event
        async def game_update(data, noChats=False):
            async with self.lock:
                self.gameUpdate = GameUpdate.from_json(data)
                self.strategy.gameState = self.gameUpdate
                try:
                    self.gameUpdate.gameState.isStarted
                    self.gameUpdate.gameState.phase
                except:
                    return
                
                gameState = self.gameUpdate.gameState
                general = self.gameUpdate.general
                trackState = self.gameUpdate.trackState
                try:
                    self.logger.log(25, f'{gameState.isCompleted} win!')
                    self.logger.log(25, f'voting to remake {general.uid}')
                    await self.sio.emit('updateRemake', { 'remakeStatus':True, 'uid': general.uid })
                    return
                except:
                    pass

                actions = Actions(gameUpdate=self.gameUpdate, sio=self.sio, strategy=self.strategy, username=self.username)

                # game is started and phase is active
                if gameState.phase =='voting':
                    if not self.voted:
                        await actions.votingPhase()
                        self.voted = True
                elif gameState.phase == 'selectingChancellor':
                    await actions.selectingChancellorPhase()
                    self.voted = False
                elif gameState.phase == 'presidentVoteOnVeto':
                    await actions.presidentVoteOnVetoPhase()
                elif gameState.phase == 'chancellorVoteOnVeto':
                    await actions.chancellorVoteOnVetoPhase()
                elif gameState.phase == 'chancellorSelectingPolicy':
                    await actions.chancellorSelectingPolicyPhase()
                elif gameState.phase == 'presidentSelectingPolicy':
                    await actions.presidentSelectingPolicyPhase()
                elif gameState.phase == 'enactPolicy':
                    power = self.gameUpdate.customGameSettings.powers[trackState.fascistPolicyCount-1]
                    if not trackState.enactedPolicies[len(trackState.enactedPolicies)-1].position == 'middle':
                        if power == 'deckpeek':
                            await actions.deckpeekPhase()
                        elif power == 'peekdrop':
                            await actions.peekdropPhase()
                        else:
                            raise ValueError('unsupported operation')
                elif gameState.phase == 'presidentVoteOnBurn':
                    await actions.presidentVoteOnBurnPhase()
                elif gameState.phase == 'selectPartyMembershipInvestigate':
                    await actions.selectPartyMembershipInvestigatePhase()
                elif gameState.phase == 'selectPartyMembershipInvestigateReverse':
                    await actions.selectPartyMembershipInvestigateReversePhase()
                elif gameState.phase == 'specialElection':
                    await actions.specialElectionPhase()
                elif gameState.phase == 'execution':
                    await actions.executionPhase()  
                elif gameState.phase == '':
                    self.logger.log(25, 'no game state')
                else:
                    raise ValueError(gameState.phase)

    async def run(self):
        login_data = {'username': self.username, 'password': self.password}
        self.logger.debug(f'login_data: {login_data}')
        async with aiohttp.ClientSession() as session:
            await session.post(self.url + '/account/signin', data=login_data)
            self.sio = socketio.AsyncClient(json=JSON)
            self.sio.eio.http = session # preserves cookie from login
            
            self.register_socketio_events()

            await self.sio.connect(self.url)

            while not self.inUserList:
                await self.sio.sleep(1)

            if self.createNewGame:
                await self.sio.emit('addNewGame', NewGame())
            else:
                while not self.inGame:
                    await self.sio.emit('getGameInfo', self.gameUID)
                    await self.sio.sleep(5)
         
            await self.sio.wait()


def clean_args(arguments):
    clean = {}
    for key in arguments:
        clean_key = key.replace('-', '').replace('<', '').replace('>', '')
        clean[clean_key] = arguments[key]
    return clean


# taken from https://stackoverflow.com/questions/6323860/sibling-package-imports
if __name__ == '__main__' and __package__ is None:
    from sys import path
    from os.path import dirname as dir
    
    path.append(dir(path[0]))
    __package__ = ''

    args = docopt(__doc__, version='Secret Hitler Bot 0.1')

    logger = logging.getLogger(__name__)

    logging.basicConfig(level=25) # getattr(logging, args['--log'].upper()))
    logger.debug(f'args:\n{args}')
    
    args = clean_args(args)

    bot = SecretHitlerBot(**args)
    asyncio.run(bot.run())
    




