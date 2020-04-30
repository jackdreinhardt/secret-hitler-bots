from enum import Enum, unique


@unique
class GameEndReason(Enum):
    hitler_killed = 0
    hitler_elected = 1
    five_liberal_policies = 2
    six_fascist_policies = 3


@unique
class Phase(Enum):
    nomination = 0
    vote = 1
    presidentSelectPolicy = 2
    chancellorSelectPolicy = 3
    presidentPower = 4
    end = 5
    veto = 6


@unique
class SecretRole(Enum):
    fascist = 0
    liberal = 1
    hitler = 2

    def party(self):
        return Party.liberal if self.value == Party.liberal.value else Party.fascist


@unique
class Power(Enum):
    deckpeek = 0
    bullet = 1
    investigate = 2
    specialelection = 3
    none = 4


@unique
class Party(Enum):
    fascist = 0
    liberal = 1

    def opposite(self):
        return Party.liberal if self.value == Party.fascist.value else Party.fascist

    @staticmethod
    def list_possible():
        return [Party.liberal, Party.fascist]


if __name__ == "__main__":
    print(Party.liberal.opposite())
