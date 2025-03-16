import random
import time

from bots.bot import Bot


def tri_coups(plateau):
    centre = plateau.colonnes // 2
    return sorted(list(plateau.colonnes_jouables), key=lambda col: abs(col - centre))


class AlphaConnectX(Bot):
    def __init__(self, nom, symbole, profondeur=5, temps_max=0.02):
        super().__init__(nom, symbole)
        self.profondeur = profondeur
        self.temps_max = temps_max
        self.table_transposition = {}

    def trouver_coup(self, plateau, joueur2) -> int:
        debut = time.time()
        meilleur_score = -float('inf')
        meilleur_coup = random.choice(list(plateau.colonnes_jouables))
        self.table_transposition = {}
        profondeur = self.profondeur

        coups_restants = sum(plateau.lignes - plateau.hauteurs_colonnes[col] for col in plateau.colonnes_jouables)

        while time.time() - debut < self.temps_max and profondeur <= coups_restants:
            for col in tri_coups(plateau):
                colonne_enlevee = plateau.jouer_coup_reversible(col, self.symbole)
                if plateau.est_victoire(col):
                    plateau.annuler_coup(col, colonne_enlevee, self.symbole)
                    return col

                score = -self.negamax(plateau, profondeur - 1, joueur2.symbole, -float('inf'), float('inf'))
                plateau.annuler_coup(col, colonne_enlevee, self.symbole)

                if score > meilleur_score:
                    meilleur_score = score
                    meilleur_coup = col
            profondeur += 1

        return meilleur_coup

    def negamax(self, plateau, profondeur, symbole, alpha, beta):
        if profondeur == 0 or plateau.est_nul():
            return 0

        cle = (tuple(tuple(col) for col in plateau.grille), profondeur, symbole)
        if cle in self.table_transposition:
            return self.table_transposition[cle]

        meilleur_score = -float('inf')
        for col in tri_coups(plateau):
            colonne_enlevee = plateau.jouer_coup_reversible(col, symbole)
            if plateau.est_victoire(col):
                plateau.annuler_coup(col, colonne_enlevee, symbole)
                self.table_transposition[cle] = 1000 + profondeur
                return 1000 + profondeur

            score = -self.negamax(plateau, profondeur - 1, self.autre_symbole(symbole), -beta, -alpha)
            plateau.annuler_coup(col, colonne_enlevee, symbole)

            if score > meilleur_score:
                meilleur_score = score
            if meilleur_score > alpha:
                alpha = meilleur_score
            if alpha >= beta:
                break

        self.table_transposition[cle] = meilleur_score
        return meilleur_score

    def autre_symbole(self, symbole):
        return 'O' if symbole == 'X' else 'X'
