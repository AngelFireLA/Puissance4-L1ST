import random
import math
from bots.bot import Bot

class QuantumConnect4Bot(Bot):
    def __init__(self, nom, symbole, profondeur=6):
        """
        Initialize the bot.
        :param nom: Name of the bot.
        :param symbole: Bot's token, e.g., 'X' or 'O'.
        :param profondeur: Maximum search depth for negamax.
        """
        super().__init__(nom, symbole)
        self.profondeur = profondeur

    def trouver_coup(self, plateau, joueur2) -> int:
        """
        Determine the next move given the current board (plateau) and the opponent (joueur2).
        Returns a column number.
        """
        valid_moves = self.order_moves(plateau)

        # 1. Check for an immediate winning move.
        for move in valid_moves:
            col_removed = plateau.jouer_coup_reversible(move, self.symbole)
            if plateau.est_victoire(move):
                plateau.annuler_coup(move, col_removed, self.symbole)
                return move
            plateau.annuler_coup(move, col_removed, self.symbole)

        # 2. Check if the opponent can win on their next move; block it.
        opponent = joueur2.symbole
        for move in valid_moves:
            col_removed = plateau.jouer_coup_reversible(move, opponent)
            if plateau.est_victoire(move):
                plateau.annuler_coup(move, col_removed, opponent)
                return move
            plateau.annuler_coup(move, col_removed, opponent)

        # 3. Use negamax with alpha-beta pruning to choose the best move.
        best_move = valid_moves[0]
        best_score = -float("inf")
        alpha = -float("inf")
        beta = float("inf")

        for move in valid_moves:
            col_removed = plateau.jouer_coup_reversible(move, self.symbole)
            # If the move immediately wins, assign a high score.
            if plateau.est_victoire(move):
                score = 1000000
            else:
                score = -self.negamax(plateau, self.profondeur - 1, -beta, -alpha, opponent)
            plateau.annuler_coup(move, col_removed, self.symbole)

            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, score)
        return best_move

    def order_moves(self, plateau):
        """
        Return a list of playable columns ordered by proximity to the center.
        """
        center = plateau.colonnes // 2
        return sorted(list(plateau.colonnes_jouables), key=lambda c: abs(c - center))

    def negamax(self, plateau, depth, alpha, beta, player):
        """
        Negamax search with alpha-beta pruning.
        :param plateau: The current game state.
        :param depth: Depth remaining.
        :param alpha: Alpha bound.
        :param beta: Beta bound.
        :param player: The token for the player whose move it is.
        :return: Score of the board from the perspective of self.symbole.
        """
        # Terminal conditions: depth limit reached or board is full.
        if depth == 0 or plateau.est_nul():
            # Evaluate from self's perspective.
            return self.evaluate_board(plateau)

        max_score = -float("inf")
        opponent = self.get_opponent(player)
        valid_moves = self.order_moves(plateau)

        for move in valid_moves:
            col_removed = plateau.jouer_coup_reversible(move, player)
            if plateau.est_victoire(move):
                # Immediate win; add depth so that quicker wins are scored higher.
                score = 1000000 + depth
            else:
                score = -self.negamax(plateau, depth - 1, -beta, -alpha, opponent)
            plateau.annuler_coup(move, col_removed, player)

            max_score = max(max_score, score)
            alpha = max(alpha, score)
            if alpha >= beta:
                break  # Beta cutoff.
        return max_score

    def get_opponent(self, player):
        """
        Given a player's token, return the opponent's token.
        """
        return 'O' if player == 'X' else 'X'

    def get_board_matrix(self, plateau):
        """
        Convert the plateau's column-based grid into a 2D matrix (list of lists)
        with rows indexed from bottom (row 0) to top.
        """
        board = [['.' for _ in range(plateau.colonnes)] for _ in range(plateau.lignes)]
        for col in range(plateau.colonnes):
            for row in range(plateau.hauteurs_colonnes[col]):
                board[row][col] = plateau.grille[col][row]
        return board

    def evaluate_board(self, plateau):
        """
        Evaluate the board state from self's perspective.
        A higher score means a better position.
        """
        board = self.get_board_matrix(plateau)
        score = 0

        # Bonus for center column control.
        center = plateau.colonnes // 2
        center_count = sum(1 for row in range(plateau.lignes) if board[row][center] == self.symbole)
        score += center_count * 6

        # Evaluate all possible windows of 4 cells.
        # Horizontal windows.
        for row in range(plateau.lignes):
            for col in range(plateau.colonnes - 3):
                window = [board[row][col + i] for i in range(4)]
                score += self.evaluate_window(window)

        # Vertical windows.
        for col in range(plateau.colonnes):
            for row in range(plateau.lignes - 3):
                window = [board[row + i][col] for i in range(4)]
                score += self.evaluate_window(window)

        # Positive diagonal windows.
        for row in range(plateau.lignes - 3):
            for col in range(plateau.colonnes - 3):
                window = [board[row + i][col + i] for i in range(4)]
                score += self.evaluate_window(window)

        # Negative diagonal windows.
        for row in range(3, plateau.lignes):
            for col in range(plateau.colonnes - 3):
                window = [board[row - i][col + i] for i in range(4)]
                score += self.evaluate_window(window)

        return score

    def evaluate_window(self, window):
        """
        Evaluate a 4-cell window.
        Positive scores favor self.symbole and negative scores favor the opponent.
        """
        score = 0
        opponent = self.get_opponent(self.symbole)

        if window.count(self.symbole) == 4:
            score += 100000
        elif window.count(self.symbole) == 3 and window.count('.') == 1:
            score += 100
        elif window.count(self.symbole) == 2 and window.count('.') == 2:
            score += 10

        if window.count(opponent) == 4:
            score -= 100000
        elif window.count(opponent) == 3 and window.count('.') == 1:
            score -= 80

        return score
