import random

from ..moteur.joueur import Joueur
class Bot(Joueur):
    def __init__(self, nom, symbole):
        super().__init__(nom, symbole)
        self.target = random.randint(0, 6)


    def trouver_coup(self, plateau, joueur2) -> int:
        if self.target in plateau.colonnes_jouables:
            return self.target
        else:
            while self.target not in plateau.colonnes_jouables:
                self.target = random.randint(0, 6)
            return self.target