import random
import time

from moteur.joueur import Joueur

class OptimizedNegamaxBot(Joueur):
    def __init__(self, nom, symbole, profondeur=6):
        """
        Initialize the Optimized Negamax bot.
        """
        super().__init__(nom, symbole)
        self.profondeur = profondeur
        self.transposition_table = {} # Initialize transposition table

    def trouver_coup(self, plateau, joueur2) -> int:
        """
        Find the best move using Negamax algorithm with alpha-beta pruning,
        iterative deepening, move ordering, and transposition table.
        """
        self.transposition_table = {} # Reset transposition table at each turn for independence
        best_move = -1
        best_score = -float('inf')

        # Iterative deepening loop (optional for this example, but good practice)
        # for depth in range(1, self.profondeur + 1):
        #     best_move, best_score = self.negamax_alpha_beta(plateau, depth, -float('inf'), float('inf'), True)
        #     if best_score == 10000: # Found winning move, no need to search deeper
        #         break

        # For simplicity in this example, we will use a fixed depth
        best_move, best_score = self.negamax_alpha_beta(plateau, self.profondeur, -float('inf'), float('inf'), True)

        return best_move

    def negamax_alpha_beta(self, plateau, profondeur, alpha, beta, maximizing_player):
        """
        Negamax algorithm with alpha-beta pruning and transposition table.
        """
        # Check transposition table first
        board_tuple = self._get_board_tuple(plateau)
        if (board_tuple, profondeur, maximizing_player) in self.transposition_table:
            return self.transposition_table[(board_tuple, profondeur, maximizing_player)]

        playable_columns = list(plateau.colonnes_jouables)

        # Check for terminal states
        if plateau.est_nul():
            return -1, 0  # Draw is neutral
        if profondeur == 0:
            return -1, self.evaluate_board(plateau, self.symbole if maximizing_player else self.get_opponent_symbol(self.symbole))


        if maximizing_player:
            best_score = -float('inf')
            best_move = -1
            # Move ordering: try center columns first
            ordered_columns = sorted(playable_columns, key=lambda col: abs(col - plateau.colonnes // 2))

            for colonne in ordered_columns:
                plateau_copy = plateau.copier_grille()
                colonne_est_enlevee = plateau_copy.jouer_coup_reversible(colonne, self.symbole)
                if plateau_copy.est_victoire(colonne):
                    score = 10000 # Winning move
                else:
                    _, score = self.negamax_alpha_beta(plateau_copy, profondeur - 1, alpha, beta, False)

                plateau_copy.annuler_coup(colonne, colonne_est_enlevee, self.symbole)

                if score > best_score:
                    best_score = score
                    best_move = colonne
                alpha = max(alpha, best_score)
                if alpha >= beta:
                    break # Beta cutoff

        else: # Minimizing player
            best_score = float('inf')
            best_move = -1
            # Move ordering: try center columns first
            ordered_columns = sorted(playable_columns, key=lambda col: abs(col - plateau.colonnes // 2))

            for colonne in ordered_columns:
                plateau_copy = plateau.copier_grille()
                opponent_symbol = self.get_opponent_symbol(self.symbole)
                colonne_est_enlevee = plateau_copy.jouer_coup_reversible(colonne, opponent_symbol)

                if plateau_copy.est_victoire(colonne):
                    score = -10000 # Opponent wins, bad for maximizing player
                else:
                    _, score = self.negamax_alpha_beta(plateau_copy, profondeur - 1, alpha, beta, True)

                plateau_copy.annuler_coup(colonne, colonne_est_enlevee, opponent_symbol)

                if score < best_score:
                    best_score = score
                    best_move = colonne
                beta = min(beta, best_score)
                if beta <= alpha:
                    break # Alpha cutoff

        # Store result in transposition table
        self.transposition_table[(board_tuple, profondeur, maximizing_player)] = (best_move, best_score)
        return best_move, best_score


    def evaluate_board(self, plateau, bot_symbol):
        """
        Heuristic evaluation function for non-terminal board states.
        """
        score = 0

        # Define winning lines (horizontal, vertical, diagonals)
        def count_lines(lines, symbole):
            count = 0
            for line in lines:
                line_str = "".join(line)
                if symbole * 4 in line_str:
                    return 10000 # Immediate win is very high
                elif symbole * 3 in line_str:
                    count += 50 # Potential for win
                elif symbole * 2 in line_str:
                    count += 10 # Still relevant
            return count

        opponent_symbol = self.get_opponent_symbol(bot_symbol)

        # Check horizontal, vertical, and diagonal lines
        lines_bot = self.get_all_lines(plateau, bot_symbol)
        lines_opponent = self.get_all_lines(plateau, opponent_symbol)

        score += count_lines(lines_bot, bot_symbol)
        score -= count_lines(lines_opponent, opponent_symbol) # Penalize opponent's potential lines

        # Center column preference
        center_col = plateau.colonnes // 2
        for r in range(plateau.hauteurs_colonnes[center_col]):
             if plateau.grille[center_col][r] == bot_symbol:
                score += 2 # Slightly prefer center column

        return score


    def get_all_lines(self, plateau, symbole):
        lines = []
        # Horizontal lines
        for r in range(plateau.lignes):
            row = [plateau.grille[c][r] if r < plateau.hauteurs_colonnes[c] else '.' for c in range(plateau.colonnes)]
            lines.append(row)
        # Vertical lines (already in plateau.grille)
        for c in range(plateau.colonnes):
            lines.append(plateau.grille[c])
        # Diagonal lines (top-left to bottom-right)
        for c in range(plateau.colonnes - 3):
            for r in range(plateau.lignes - 3):
                diag = [plateau.grille[c+i][r+i] if r+i < plateau.hauteurs_colonnes[c+i] else '.' for i in range(4)]
                lines.append(diag)
        # Diagonal lines (bottom-left to top-right)
        for c in range(plateau.colonnes - 3):
            for r in range(3, plateau.lignes):
                diag = [plateau.grille[c+i][r-i]if r-i < plateau.hauteurs_colonnes[c+i] else '.' for i in range(4)]
                lines.append(diag)
        return lines


    def get_opponent_symbol(self, symbole):
        return 'O' if symbole == 'X' else 'X'

    def _get_board_tuple(self, plateau):
        """
        Convert the board state to a hashable tuple for transposition table.
        """
        return tuple(tuple(col) for col in plateau.grille)
