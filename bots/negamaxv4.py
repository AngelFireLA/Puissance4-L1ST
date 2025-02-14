import random
import time

from bots.bot import Bot

def center_ordered_moves(plateau):
    center = plateau.colonnes // 2
    # Sort available columns by how close they are to the center.
    return sorted(list(plateau.colonnes_jouables), key=lambda col: abs(col - center))

class Negamax4(Bot):
    def __init__(self, nom, symbole, profondeur=4, temps_max=0):
        """
        """
        super().__init__(nom, symbole)
        self.profondeur = profondeur
        self.coups = 0
        self.temps_de_pensée_max = temps_max

    def trouver_coup(self, plateau, joueur2) -> int:
        self.coups = 0
        meilleur_score = -float('inf')
        start_time = time.time()
        i = -1
        coups_restants = 0
        for colonne in list(plateau.colonnes_jouables):
            coups_restants += plateau.lignes - plateau.hauteurs_colonnes[colonne]
        if self.temps_de_pensée_max == 0:
            # print("went to depth", self.profondeur + i)
            meilleur_score = -float('inf')
            meilleur_coups = []

            for col in center_ordered_moves(plateau):

                colonne_est_enlevée = plateau.jouer_coup_reversible(col, self.symbole)

                if plateau.est_victoire(col):
                    plateau.annuler_coup(col, colonne_est_enlevée, self.symbole)
                    return col

                prochain_symbole = joueur2.symbole
                score = - self.negamax(plateau, depth=self.profondeur + i, symbole=prochain_symbole, alpha=-float('inf'), beta=float('inf'))
                plateau.annuler_coup(col, colonne_est_enlevée, self.symbole)
                if score > 0:
                    return col

                # print("score", score, "coup", col, "meilleur_score", meilleur_score, "meilleur_coup", meilleur_coup)
                if score > meilleur_score:
                    meilleur_score = score
                    meilleur_coups = [col]
                elif score == meilleur_score:
                    meilleur_coups.append(col)
                    random.shuffle(meilleur_coups)
        else:
            while time.time()-start_time <= self.temps_de_pensée_max and meilleur_score <= 0 and i <= coups_restants:

                #print("went to depth", self.profondeur + i +1)
                meilleur_score = -float('inf')
                meilleur_coups = []

                for col in center_ordered_moves(plateau):
                    colonne_est_enlevée = plateau.jouer_coup_reversible(col, self.symbole)

                    if plateau.est_victoire(col):
                        plateau.annuler_coup(col, colonne_est_enlevée, self.symbole)
                        return col

                    prochain_symbole = joueur2.symbole
                    score = - self.negamax(plateau, depth=self.profondeur + i, symbole=prochain_symbole, alpha=-float('inf'), beta=float('inf'))
                    plateau.annuler_coup(col, colonne_est_enlevée, self.symbole)

                    # print("score", score, "coup", col, "meilleur_score", meilleur_score, "meilleur_coup", meilleur_coup)
                    if score > 0:
                        return col
                    if score > meilleur_score:
                        meilleur_score = score
                        meilleur_coups = [col]
                    elif score == meilleur_score:
                        meilleur_coups.append(col)
                        random.shuffle(meilleur_coups)
                i += 1

        # print()
        return meilleur_coups[0] if meilleur_coups is not None else 0



    def negamax(self, plateau, depth, symbole, alpha, beta):
        self.coups += 1
        if depth == 0 or plateau.est_nul():
            return 0

        meilleur_score = -float('inf')
        for col in center_ordered_moves(plateau):
            colonne_est_enlevée = plateau.jouer_coup_reversible(col, symbole)

            if plateau.est_victoire(col):
                plateau.annuler_coup(col, colonne_est_enlevée, symbole)
                return 1000 + depth
            symbole_suivant = self.symbole if symbole != self.symbole else self.autre_symbole()
            score = -self.negamax(plateau, depth - 1, symbole_suivant, -beta, -alpha)

            plateau.annuler_coup(col, colonne_est_enlevée, symbole)

            if score > meilleur_score:
                meilleur_score = score
            if meilleur_score > alpha:
                alpha = meilleur_score
            if alpha >= beta:
                break
        return meilleur_score

    def autre_symbole(self):
        return 'O' if self.symbole == 'X' else 'X'
