import random

from .bot import Bot

class Negamax(Bot):
    def __init__(self, nom, symbole, profondeur=4):
        """
        """
        super().__init__(nom, symbole)
        self.profondeur = profondeur
        self.coups = 0

    def trouver_coup(self, plateau, joueur2) -> int:
        self.coups = 0
        meilleur_score = -float('inf')
        meilleur_coups = []

        for col in plateau.colonnes_jouables:
            plateau_simule = plateau.copier_grille()
            plateau_simule.ajouter_jeton(col, self.symbole)

            if plateau_simule.est_victoire(col):
                return col

            prochain_symbole = joueur2.symbole
            score = - self.negamax(plateau_simule, depth=self.profondeur-1, symbole=prochain_symbole)
            # print("score", score, "coup", col, "meilleur_score", meilleur_score, "meilleur_coup", meilleur_coup)
            if score > meilleur_score:
                meilleur_score = score
                meilleur_coups = [col]
            elif score == meilleur_score:
                meilleur_coups.append(col)
                random.shuffle(meilleur_coups)

        # print()
        return meilleur_coups[0] if meilleur_coups is not None else 0


    def negamax(self, plateau, depth, symbole):
        self.coups += 1
        if depth == 0:
            return self.evaluation(plateau)

        if plateau.est_nul():
            return 0

        meilleur_score = -float('inf')
        for col in plateau.colonnes_jouables:
            plateau_simule = plateau.copier_grille()
            plateau_simule.ajouter_jeton(col, symbole)
            # if depth == self.profondeur-1:
            #     print(col, depth, symbole, 1000 + depth)
            #     plateau_simule.afficher()
            #     print()

            if plateau_simule.est_victoire(col):

                return 1000 + depth

            symbole_suivant = self.symbole if symbole != self.symbole else self.autre_symbole()

            score = - self.negamax(plateau_simule, depth - 1, symbole_suivant)

            if score > meilleur_score:
                meilleur_score = score
        return meilleur_score

    def evaluation(self, plateau):
        return 0

    def autre_symbole(self):
        return 'O' if self.symbole == 'X' else 'X'
