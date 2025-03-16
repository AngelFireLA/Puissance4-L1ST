import random
import time
import math

from moteur.joueur import Joueur
from bots.bot import Bot

class AdvancedConnect4Bot(Bot):
    def __init__(self, nom, symbole, profondeur=4, temps_max=1):
        super().__init__(nom, symbole)
        self.profondeur = profondeur
        self.temps_max = temps_max
        self.table_de_transposition = {}

    def trouver_coup(self, plateau, joueur2) -> int:
        self.table_de_transposition.clear()
        meilleur_score = -float('inf')
        start_time = time.time()
        meilleur_coups = []

        # Sort playable columns by how close they are to the center.
        centre = plateau.colonnes // 2
        colonnes_triees = sorted(list(plateau.colonnes_jouables), key=lambda col: abs(col - centre))

        for col in colonnes_triees:
            colonne_est_enlevée = plateau.jouer_coup_reversible(col, self.symbole)
            if plateau.est_victoire(col):
                plateau.annuler_coup(col, colonne_est_enlevée, self.symbole)
                return col

            prochain_symbole = joueur2.symbole
            score = -self.negamax(plateau, profondeur=self.profondeur, symbole=prochain_symbole, alpha=-float('inf'), beta=float('inf'))
            plateau.annuler_coup(col, colonne_est_enlevée, self.symbole)

            if score > meilleur_score:
                meilleur_score = score
                meilleur_coups = [col]
            elif score == meilleur_score:
                meilleur_coups.append(col)

            if self.temps_max and (time.time() - start_time) > self.temps_max:
                break

        if not meilleur_coups:
            return random.choice(list(plateau.colonnes_jouables))

        # Choose the best move considering the center heuristic.
        centre = plateau.colonnes // 2
        max_distance = max(abs(col - centre) for col in plateau.colonnes_jouables) if plateau.colonnes_jouables else 1
        weights = [(max_distance - abs(col - centre) + 1) for col in meilleur_coups]
        selected_move = random.choices(meilleur_coups, weights=weights, k=1)[0]
        return selected_move

    def grille_à_tuple(self, plateau):
        return tuple(tuple(col + ["."] * (plateau.lignes - len(col))) for col in plateau.grille)

    def negamax(self, plateau, profondeur, symbole, alpha, beta):
        if profondeur == 0 or plateau.est_nul():
            return self.heuristique(plateau, symbole)

        clé = (self.grille_à_tuple(plateau), profondeur, symbole)
        if clé in self.table_de_transposition:
            return self.table_de_transposition[clé]

        meilleur_score = -float('inf')
        centre = plateau.colonnes // 2
        colonnes_triees = sorted(list(plateau.colonnes_jouables), key=lambda col: abs(col - centre))

        for col in colonnes_triees:
            colonne_est_enlevée = plateau.jouer_coup_reversible(col, symbole)
            if plateau.est_victoire(col):
                plateau.annuler_coup(col, colonne_est_enlevée, symbole)
                self.table_de_transposition[clé] = 1000 + profondeur
                return 1000 + profondeur

            symbole_suivant = self.symbole if symbole != self.symbole else self.autre_symbole()
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

    def heuristique(self, plateau, symbole):
        score = 0
        for col in range(plateau.colonnes):
            for ligne in range(plateau.hauteurs_colonnes[col]):
                jeton = plateau.grille[col][ligne]
                if jeton == symbole:
                    score += 1
                elif jeton != '.':
                    score -= 1
        return score

    def autre_symbole(self):
        return 'O' if self.symbole == 'X' else 'X'
