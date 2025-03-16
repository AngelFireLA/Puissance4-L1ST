import random
import time

from bots.bot import Bot

def tri_coups(plateau):
    centre = plateau.colonnes // 2
    # Sort playable columns by how close they are to the center.
    return sorted(list(plateau.colonnes_jouables), key=lambda col: abs(col - centre))

class Negamax5B(Bot):
    def __init__(self, nom, symbole, profondeur=4, temps_max=0):
        """
        Initialize the Negamax bot.
        """
        super().__init__(nom, symbole)
        self.profondeur = profondeur
        self.coups = 0
        self.temps_de_pensée_max = temps_max
        self.table_de_transposition = None

    def trouver_coup(self, plateau, joueur2) -> int:
        self.coups = 0
        meilleur_score = -float('inf')
        start_time = time.time()
        self.table_de_transposition = {}
        i = -1
        coups_restants = 0
        for colonne in list(plateau.colonnes_jouables):
            coups_restants += plateau.lignes - plateau.hauteurs_colonnes[colonne]
        meilleur_coups = []

        if self.temps_de_pensée_max == 0:
            for col in tri_coups(plateau):
                colonne_est_enlevée = plateau.jouer_coup_reversible(col, self.symbole)
                if plateau.est_victoire(col):
                    plateau.annuler_coup(col, colonne_est_enlevée, self.symbole)
                    return col

                prochain_symbole = joueur2.symbole
                score = -self.negamax(plateau, profondeur=self.profondeur + i, symbole=prochain_symbole,
                                       alpha=-float('inf'), beta=float('inf'))
                plateau.annuler_coup(col, colonne_est_enlevée, self.symbole)
                if score > 0:
                    return col
                if score > meilleur_score:
                    meilleur_score = score
                    meilleur_coups = [col]
                elif score == meilleur_score:
                    meilleur_coups.append(col)
        else:
            while time.time() - start_time <= self.temps_de_pensée_max and meilleur_score <= 0 and i <= coups_restants:
                meilleur_score = -float('inf')
                meilleur_coups = []
                for col in tri_coups(plateau):
                    colonne_est_enlevée = plateau.jouer_coup_reversible(col, self.symbole)
                    if plateau.est_victoire(col):
                        plateau.annuler_coup(col, colonne_est_enlevée, self.symbole)
                        return col

                    prochain_symbole = joueur2.symbole
                    score = -self.negamax(plateau, profondeur=self.profondeur + i, symbole=prochain_symbole,
                                           alpha=-float('inf'), beta=float('inf'))
                    plateau.annuler_coup(col, colonne_est_enlevée, self.symbole)
                    if score > 0:
                        return col
                    if score > meilleur_score:
                        meilleur_score = score
                        meilleur_coups = [col]
                    elif score == meilleur_score:
                        meilleur_coups.append(col)
                i += 1

        if not meilleur_coups:
            print("not meilleur coups")
            return 0
        sorted_meilleur_coups = sorted(meilleur_coups, key=lambda col: abs(col - plateau.colonnes // 2))
        selected_move = sorted_meilleur_coups[0]
        return selected_move

    def grille_à_tuple(self, plateau):
        return tuple(tuple(col + ["."] * (plateau.lignes - len(col))) for col in plateau.grille)

    def negamax(self, plateau, profondeur, symbole, alpha, beta):
        self.coups += 1
        if profondeur == 0 or plateau.est_nul():
            return 0

        clé = (self.grille_à_tuple(plateau), profondeur, symbole)
        if clé in self.table_de_transposition:
            return self.table_de_transposition[clé]

        meilleur_score = -float('inf')
        for col in tri_coups(plateau):
            colonne_est_enlevée = plateau.jouer_coup_reversible(col, symbole)
            if plateau.est_victoire(col):
                plateau.annuler_coup(col, colonne_est_enlevée, symbole)
                self.table_de_transposition[clé] = 1000 + profondeur
                return 1000 + profondeur

            symbole_suivant = symbole_opposé(symbole)
            score = -self.negamax(plateau, profondeur - 1, symbole_suivant, -beta, -alpha)
            plateau.annuler_coup(col, colonne_est_enlevée, symbole)

            if score > meilleur_score:
                meilleur_score = score
            if meilleur_score > alpha:
                alpha = meilleur_score
            if alpha >= beta:
                break

        self.table_de_transposition[clé] = meilleur_score
        return meilleur_score

    def autre_symbole(self):
        return 'O' if self.symbole == 'X' else 'X'

def symbole_opposé(symbole):
    return 'O' if symbole == 'X' else 'X'
