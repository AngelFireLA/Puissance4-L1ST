import random
from moteur.joueur import Joueur

class AdvancedNegamaxBot(Joueur):
    def __init__(self, nom, symbole, profondeur):
        super().__init__(nom, symbole)
        self.profondeur = profondeur  # Increased search depth
        self.transposition_table = {}
        self.directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

    def trouver_coup(self, plateau, joueur2):
        self.transposition_table = {}
        best_score = -float('inf')
        best_move = None
        # Prefer center column first
        sorted_cols = sorted(plateau.colonnes_jouables, key=lambda c: abs(c - plateau.colonnes // 2))

        for col in sorted_cols:
            if not plateau.colonne_valide(col):
                continue

            # Check immediate win
            if self.is_win_move(plateau, col):
                return col

            colonne_est_enlevée = plateau.jouer_coup_reversible(col, self.symbole)
            next_symbole = self.autre_symbole(self.symbole)
            score = -self.negamax(plateau, self.profondeur - 1, next_symbole, -float('inf'), float('inf'))
            plateau.annuler_coup(col, colonne_est_enlevée, self.symbole)

            if score > best_score:
                best_score = score
                best_move = col
        return best_move if best_move is not None else random.choice(list(plateau.colonnes_jouables))

    def negamax(self, plateau, profondeur, symbole, alpha, beta):
        key = self._state_key(plateau, profondeur, symbole)
        if key in self.transposition_table:
            return self.transposition_table[key]

        if profondeur == 0 or plateau.est_nul():
            return self.evaluate_board(plateau, symbole)

        best_score = -float('inf')
        # Use the current player's symbol for move ordering.
        for col in self._sorted_moves(plateau, symbole):
            if col not in plateau.colonnes_jouables:
                continue

            colonne_est_enlevée = plateau.jouer_coup_reversible(col, symbole)
            if plateau.est_victoire(col):
                score = 1000 + profondeur  # Prioritize immediate wins
            else:
                next_symbole = self.autre_symbole(symbole)
                score = -self.negamax(plateau, profondeur - 1, next_symbole, -beta, -alpha)
            plateau.annuler_coup(col, colonne_est_enlevée, symbole)

            if score > best_score:
                best_score = score
                alpha = max(alpha, score)
            if alpha >= beta:
                break  # Beta cutoff

        self.transposition_table[key] = best_score
        return best_score

    def _sorted_moves(self, plateau, symbole):
        """Sort moves by heuristic priority using the given player's symbol"""
        center = plateau.colonnes // 2
        return sorted(plateau.colonnes_jouables, key=lambda c: (
            -self.heuristic_score(plateau, c, symbole),
            abs(c - center)
        ))

    def _state_key(self, plateau, profondeur, symbole):
        return (
            self._grille_tuple(plateau),
            profondeur,
            symbole
        )

    def _grille_tuple(self, plateau):
        return tuple(
            tuple(col + ['.'] * (plateau.lignes - len(col)))
            for col in plateau.grille
        )

    def evaluate_board(self, plateau, current_player):
        opponent = self.autre_symbole(current_player)
        score = 0

        # Center column preference
        center_col = plateau.colonnes // 2
        center_count = sum(1 for row in range(plateau.lignes)
                           if len(plateau.grille[center_col]) > row
                           and plateau.grille[center_col][row] == current_player)
        score += center_count * 3

        # Check all possible windows
        for row in range(plateau.lignes):
            for col in range(plateau.colonnes - 3):
                # Horizontal
                window = self._get_window(plateau, row, col, 0, 1)
                score += self._window_score(window, current_player, opponent)

            for col in range(plateau.colonnes):
                # Vertical
                if len(plateau.grille[col]) >= row + 4:
                    window = self._get_window(plateau, row, col, 1, 0)
                    score += self._window_score(window, current_player, opponent)

        for row in range(plateau.lignes - 3):
            for col in range(plateau.colonnes - 3):
                # Diagonal /
                window = self._get_window(plateau, row, col, 1, 1)
                score += self._window_score(window, current_player, opponent)

                # Diagonal \
                window = self._get_window(plateau, row, col + 3, 1, -1)
                score += self._window_score(window, current_player, opponent)

        return score

    def _get_window(self, plateau, start_row, start_col, dr, dc):
        window = []
        for i in range(4):
            r = start_row + dr * i
            c = start_col + dc * i
            if 0 <= c < plateau.colonnes and r < len(plateau.grille[c]):
                window.append(plateau.grille[c][r])
            else:
                window.append('.')
        return window

    def _window_score(self, window, player, opponent):
        score = 0
        count_player = window.count(player)
        count_opponent = window.count(opponent)
        empty = window.count('.')

        if count_player == 4:
            return 100
        if count_player == 3 and empty == 1:
            score += 5
        if count_player == 2 and empty == 2:
            score += 2
        if count_opponent == 3 and empty == 1:
            score -= 4
        return score

    def autre_symbole(self, symbole):
        return 'O' if symbole == 'X' else 'X'

    def is_win_move(self, plateau, col):
        symbole = self.symbole
        colonne_est_enlevée = plateau.jouer_coup_reversible(col, symbole)
        result = plateau.est_victoire(col)
        plateau.annuler_coup(col, colonne_est_enlevée, symbole)
        return result

    def heuristic_score(self, plateau, col, player):
        colonne_est_enlevée = plateau.jouer_coup_reversible(col, player)
        score = self.evaluate_board(plateau, player)
        plateau.annuler_coup(col, colonne_est_enlevée, player)
        return score

