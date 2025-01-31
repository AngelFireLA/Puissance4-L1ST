from moteur.joueur import Joueur
class Bot(Joueur):
    def __init__(self, nom, symbole):
        super().__init__(nom, symbole)


    def trouver_coup(self, plateau, joueur2) -> int:
        return list(plateau.colonnes_jouables)[0]