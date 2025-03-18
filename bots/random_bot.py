from .bot import Bot
import random
class RandomBot(Bot):
    def __init__(self, nom, symbole):
        super().__init__(nom, symbole)

    def trouver_coup(self, plateau, joueur2) -> int:
        return random.choice(list(plateau.colonnes_jouables))