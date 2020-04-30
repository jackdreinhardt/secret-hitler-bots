import logging


class Actions:
    def __init__(self, gameUpdate, sio, strategy, username):
        self.gu = gameUpdate
        self.sio = sio
        self.strategy = strategy
        self.username = username
        self.logger = logging.getLogger(__name__)

    def getGovernmentStatus(self):
        for player in self.gu.publicPlayersState:
            if self.username == player.userName:
                return player.governmentStatus
        raise ValueError("username not present in publicPlayersState")

    async def governmentAction(self, role, func):
        self.logger.log(25, f'phase: {self.gu.gameState.phase}')
        try:
            power = self.gu.customGameSettings.powers[self.gu.trackState.fascistPolicyCount-1]
            self.logger.log(25, f'power: {power}')
        except:
            pass
        if self.getGovernmentStatus() == role:
            self.logger.log(25, f'{self.username} is {self.gu.gameState.phase}') 
            await func(self)

    async def votingPhase(self):
        self.logger.log(25, f'phase: {self.gu.gameState.phase}')
        await self.sio.emit('selectedVoting', { 'vote':self.strategy.vote(), 'uid':self.gu.general.uid })

    async def selectingChancellorPhase(self):
        async def presidentSelectedChancellor(self):
            await self.sio.emit('presidentSelectedChancellor', { 'chancellorIndex':self.strategy.selectChancellor(), 'uid':self.gu.general.uid }) 
        
        await self.governmentAction('isPendingPresident', presidentSelectedChancellor)

    async def presidentSelectingPolicyPhase(self):
        async def selectedPresidentPolicy(self):
            await self.sio.emit('selectedPresidentPolicy', {'selection':self.strategy.presidentSelectPolicy(), 'uid':self.gu.general.uid })
        
        await self.governmentAction('isPresident', selectedPresidentPolicy)

    async def chancellorSelectingPolicyPhase(self):
        async def selectedChancellorPolicy(self):
            await self.sio.emit('selectedChancellorPolicy', {'selection':self.strategy.chancellorSelectPolicy(), 'uid':self.gu.general.uid })
        
        await self.governmentAction('isChancellor', selectedChancellorPolicy)

    async def deckpeekPhase(self):
        async def selectedPolicies(self):
            await self.sio.emit('selectedPolicies', { 'uid':self.gu.general.uid })
        
        await self.governmentAction('isPresident', selectedPolicies)

    async def peekdropPhase(self):
        async def selectedPolicies(self):
            await self.sio.emit('selectedPolicies', { 'uid':self.gu.general.uid })

        await self.governmentAction('isPresident', selectedPolicies)

    async def executionPhase(self):
        async def selectedPlayerToExecute(self):
            await self.sio.emit('selectedPlayerToExecute', { 'playerIndex':self.strategy.selectPlayerToExecute(), 'uid':self.gu.general.uid })
        
        await self.governmentAction('isPresident', selectedPlayerToExecute)

    async def chancellorVoteOnVetoPhase(self):
        async def selectedChancellorVoteOnVeto(self):
            await self.sio.emit('selectedChancellorVoteOnVeto', { 'vote':self.strategy.chancellorVoteOnVeto(), 'uid':self.gu.general.uid })
        
        await self.governmentAction('isChancellor', selectedChancellorVoteOnVeto)

    async def presidentVoteOnVetoPhase(self):
        async def selectedPresidentVoteOnVeto(self):
            await self.sio.emit('selectedPresidentVoteOnVeto', { 'vote':self.strategy.presidentVoteOnVeto(), 'uid':self.gu.general.uid })

        await self.governmentAction('isPresident', selectedPresidentVoteOnVeto)

    async def selectPartyMembershipInvestigatePhase(self):
        async def selectPartyMembershipInvestigate(self):
            await self.sio.emit('selectPartyMembershipInvestigate', { 'playerIndex':self.strategy.selectPartyMembershipInvestigate(), 'uid':self.gu.general.uid })

        await self.governmentAction('isPresident', selectPartyMembershipInvestigate)

    async def selectPartyMembershipInvestigateReversePhase(self):
        async def selectPartyMembershipInvestigateReverse(self):
             await self.sio.emit('selectPartyMembershipInvestigateReverse', { 'playerIndex':self.strategy.selectPartyMembershipInvestigateReverse(), 'uid':self.gu.general.uid })

        await self.governmentAction('isPresident', selectPartyMembershipInvestigateReverse)

    async def specialElectionPhase(self):
        async def selectedSpecialElection(self):
            await self.sio.emit('selectedSpecialElection', { 'playerIndex':self.strategy.selectedSpecialElection(), 'uid':self.gu.general.uid })

        await self.governmentAction('isPresident', selectedSpecialElection)

    async def presidentVoteOnBurnPhase(self):
        async def selectedPresidentVoteOnBurn(self):
             await self.sio.emit('selectedPresidentVoteOnBurn', { 'vote':self.strategy.selectedPresidentVoteOnBurn(), 'uid':self.gu.general.uid })

        await self.governmentAction('isPresident', selectedPresidentVoteOnBurn)
