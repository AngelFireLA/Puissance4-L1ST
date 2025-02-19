import random
import time

from bots.bot import Bot

def tri_coups(plateau):
    centre = plateau.colonnes // 2
    # Sort playable columns by how close they are to the center.
    return sorted(list(plateau.colonnes_jouables), key=lambda col: abs(col - centre))

class Negamax5(Bot):
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
            # Fixed-depth search.
            for col in tri_coups(plateau):
                colonne_est_enlevée = plateau.jouer_coup_reversible(col, self.symbole)
                if plateau.est_victoire(col):
                    plateau.annuler_coup(col, colonne_est_enlevée, self.symbole)
                    return col

                prochain_symbole = joueur2.symbole
                score = -self.negamax(plateau, depth=self.profondeur + i, symbole=prochain_symbole,
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
                    score = -self.negamax(plateau, depth=self.profondeur + i, symbole=prochain_symbole,
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
            return 0

        center = plateau.colonnes // 2

        max_distance = max(abs(col - center) for col in plateau.colonnes_jouables) if plateau.colonnes_jouables else 1
        # For each candidate move, the weight is:
        #   weight = (max_distance - distance_to_center + 1)
        # Thus a move at the center (distance 0) gets weight = max_distance + 1.
        weights = [(max_distance - abs(col - center) + 1) for col in meilleur_coups]
        # Select one move from the best moves using the computed weights.
        selected_move = random.choices(meilleur_coups, weights=weights, k=1)[0]
        return selected_move

    def board_to_tuple(self, plateau):
        # Represent each column as a tuple with fixed length.
        # Fill missing slots with the empty marker (".")
        return tuple(tuple(col + ["."] * (plateau.lignes - len(col))) for col in plateau.grille)

    def negamax(self, plateau, depth, symbole, alpha, beta):
        self.coups += 1
        if depth == 0 or plateau.est_nul():
            return 0

        clé = (self.board_to_tuple(plateau), depth, symbole)
        if clé in self.table_de_transposition:
            return self.table_de_transposition[clé]

        meilleur_score = -float('inf')
        for col in tri_coups(plateau):
            colonne_est_enlevée = plateau.jouer_coup_reversible(col, symbole)
            if plateau.est_victoire(col):
                plateau.annuler_coup(col, colonne_est_enlevée, symbole)
                self.table_de_transposition[clé] = 1000 + depth
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

        self.table_de_transposition[clé] = meilleur_score
        return meilleur_score

    def autre_symbole(self):
        return 'O' if self.symbole == 'X' else 'X'
