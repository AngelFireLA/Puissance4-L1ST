from math import inf
import random

from bots.bot import Bot


class SigmaBot(Bot):
    def __init__(self, nom, symbole, profondeur=5):
        super().__init__(nom, symbole)
        self.profondeur = profondeur
        self.adversaire_symbole = None
        self.transposition_table = {}

    def trouver_coup(self, plateau, joueur2) -> int:
        # Reset any state from previous calls
        self.transposition_table = {}
        self.adversaire_symbole = joueur2.symbole

        meilleur_score = -inf
        meilleur_coup = random.choice(list(plateau.colonnes_jouables))

        # Check for immediate winning moves
        for colonne in plateau.colonnes_jouables:
            nouveau_plateau = plateau.copier_grille()
            colonne_est_enlevee = nouveau_plateau.jouer_coup_reversible(colonne, self.symbole)
            if nouveau_plateau.est_victoire(colonne):
                nouveau_plateau.annuler_coup(colonne, colonne_est_enlevee, self.symbole)
                return colonne
            nouveau_plateau.annuler_coup(colonne, colonne_est_enlevee, self.symbole)

        # Check if opponent has winning moves and block them
        for colonne in plateau.colonnes_jouables:
            nouveau_plateau = plateau.copier_grille()
            colonne_est_enlevee = nouveau_plateau.jouer_coup_reversible(colonne, self.adversaire_symbole)
            if nouveau_plateau.est_victoire(colonne):
                nouveau_plateau.annuler_coup(colonne, colonne_est_enlevee, self.adversaire_symbole)
                return colonne
            nouveau_plateau.annuler_coup(colonne, colonne_est_enlevee, self.adversaire_symbole)

        # Order columns to prioritize center columns
        centre = plateau.colonnes // 2
        colonnes_ordonnees = sorted(plateau.colonnes_jouables, key=lambda x: abs(x - centre))

        # Perform alpha-beta search on each possible move
        for colonne in colonnes_ordonnees:
            colonne_est_enlevee = plateau.jouer_coup_reversible(colonne, self.symbole)

            if plateau.est_victoire(colonne):
                score = 1000000  # Immediate win
            else:
                # Use negative of score from opponent's perspective
                score = -self.alphabeta(plateau, self.profondeur - 1, -inf, -meilleur_score, False, colonne)

            plateau.annuler_coup(colonne, colonne_est_enlevee, self.symbole)

            if score > meilleur_score:
                meilleur_score = score
                meilleur_coup = colonne
            elif score == meilleur_score and random.random() < 0.5:
                # Add some randomness among equal scores
                meilleur_coup = colonne

        return meilleur_coup

    def alphabeta(self, plateau, profondeur, alpha, beta, maximisant, dernier_coup):
        # Base case: terminal node or max depth reached
        if profondeur == 0 or plateau.est_nul():
            return self.evaluer_plateau(plateau, dernier_coup)

        if plateau.est_victoire(dernier_coup):
            return 1000000 if not maximisant else -1000000

        # Generate board hash for transposition table
        board_hash = self.generer_hash_tableau(plateau)
        key = (board_hash, profondeur, maximisant)

        if key in self.transposition_table:
            return self.transposition_table[key]

        # Order moves - center columns first
        centre = plateau.colonnes // 2
        colonnes_ordonnees = sorted(plateau.colonnes_jouables, key=lambda x: abs(x - centre))

        if maximisant:
            meilleur_score = -inf
            for colonne in colonnes_ordonnees:
                colonne_est_enlevee = plateau.jouer_coup_reversible(colonne, self.symbole)
                score = self.alphabeta(plateau, profondeur - 1, alpha, beta, False, colonne)
                plateau.annuler_coup(colonne, colonne_est_enlevee, self.symbole)

                meilleur_score = max(meilleur_score, score)
                alpha = max(alpha, meilleur_score)
                if beta <= alpha:
                    break  # Beta cutoff

            self.transposition_table[key] = meilleur_score
            return meilleur_score
        else:
            meilleur_score = inf
            for colonne in colonnes_ordonnees:
                colonne_est_enlevee = plateau.jouer_coup_reversible(colonne, self.adversaire_symbole)
                score = self.alphabeta(plateau, profondeur - 1, alpha, beta, True, colonne)
                plateau.annuler_coup(colonne, colonne_est_enlevee, self.adversaire_symbole)

                meilleur_score = min(meilleur_score, score)
                beta = min(beta, meilleur_score)
                if beta <= alpha:
                    break  # Alpha cutoff

            self.transposition_table[key] = meilleur_score
            return meilleur_score

    def evaluer_plateau(self, plateau, dernier_coup):
        """Evaluate the board position from the perspective of the current player"""
        if plateau.est_victoire(dernier_coup):
            # Determine which player made the winning move
            joueur_dernier_coup = plateau.grille[dernier_coup][-1]
            return 1000000 if joueur_dernier_coup == self.symbole else -1000000

        if plateau.est_nul():
            return 0

        # Score based on potential threats and center control
        score = 0

        # Prefer central columns
        centre = plateau.colonnes // 2
        for colonne in range(plateau.colonnes):
            if colonne not in plateau.colonnes_jouables:
                continue

            # Center control is valuable
            score += (plateau.colonnes - abs(colonne - centre)) // 2

            # Check potential winning setups
            colonne_est_enlevee = plateau.jouer_coup_reversible(colonne, self.symbole)
            if plateau.est_victoire(colonne):
                score += 50  # Potential win next move
            plateau.annuler_coup(colonne, colonne_est_enlevee, self.symbole)

            # Check opponent's potential winning setups
            colonne_est_enlevee = plateau.jouer_coup_reversible(colonne, self.adversaire_symbole)
            if plateau.est_victoire(colonne):
                score -= 50  # Potential loss next move
            plateau.annuler_coup(colonne, colonne_est_enlevee, self.adversaire_symbole)

        # Count pieces and their positions
        for c in range(plateau.colonnes):
            for r in range(len(plateau.grille[c])):
                piece = plateau.grille[c][r]
                # Add value for piece positions
                if piece == self.symbole:
                    # Prefer pieces in the center columns
                    score += (plateau.colonnes - abs(c - centre)) // 2
                    # Prefer pieces higher up in the columns
                    score += r
                elif piece == self.adversaire_symbole:
                    # Penalize opponent pieces in center columns
                    score -= (plateau.colonnes - abs(c - centre)) // 2
                    # Penalize opponent pieces higher up in columns
                    score -= r

        return score

    def generer_hash_tableau(self, plateau):
        """Generate a hashable representation of the board state"""
        return tuple(tuple(col) for col in plateau.grille)