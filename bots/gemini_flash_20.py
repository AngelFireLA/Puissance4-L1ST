import random
import time

from moteur.joueur import Joueur

class TranspositionTable:
    def __init__(self, capacity=1000000):
        self.capacity = capacity
        self.table = {}
        self.hits = 0
        self.misses = 0

    def __len__(self):
        return len(self.table)

    def put(self, key, value):
        if len(self.table) >= self.capacity:
            self.table.pop(next(iter(self.table)))  # Remove oldest entry (FIFO)
        self.table[key] = value

    def get(self, key):
        try:
            self.hits += 1
            return self.table[key]
        except KeyError:
            self.misses += 1
            return None

    def clear(self):
        self.table = {}
        self.hits = 0
        self.misses = 0

def sort_moves(board):
    center = board.colonnes // 2
    return sorted(list(board.colonnes_jouables), key=lambda col: abs(col - center))

class AlphaConnect(Joueur):
    def __init__(self, nom, symbole, profondeur=4, temp_max=1):
        super().__init__(nom, symbole)
        self.profondeur = profondeur
        self.temp_max = temp_max
        self.transposition_table = TranspositionTable()
        self.nodes_evaluated = 0
        self.start_time = 0

    def trouver_coup(self, board, opponent):
        self.transposition_table.clear()
        self.nodes_evaluated = 0
        self.start_time = time.time()
        best_move = None
        alpha = -float('inf')
        beta = float('inf')

        possible_moves = sort_moves(board)

        # Iterative deepening
        for depth in range(1, self.profondeur + 1):
            best_score = -float('inf')
            best_move_current_depth = None
            for move in possible_moves:
                if time.time() - self.start_time > self.temp_max:
                    break

                board_copy = board.copier_grille()
                board_copy.jouer_coup_reversible(move, self.symbole)
                score = -self.alphabeta(board_copy, depth - 1, -beta, -alpha, opponent.symbole)
                del board_copy

                if score > best_score:
                    best_score = score
                    best_move_current_depth = move

                alpha = max(alpha, best_score)
                if alpha >= beta:
                    break  # Beta cutoff

            if best_move_current_depth is not None and time.time() - self.start_time <= self.temp_max:
                best_move = best_move_current_depth
            else:
                break # Stop if we ran out of time

        if best_move is None:
            best_move = random.choice(list(board.colonnes_jouables))

        return best_move

    def alphabeta(self, board, depth, alpha, beta, player_symbol):
        self.nodes_evaluated += 1

        if depth == 0 or board.est_nul():
            return self.evaluate_board(board, self.symbole)

        # Check transposition table
        board_tuple = self.board_to_tuple(board)
        transposition_key = (board_tuple, depth, player_symbol)
        transposition_entry = self.transposition_table.get(transposition_key)
        if transposition_entry:
            return transposition_entry

        possible_moves = sort_moves(board)

        for move in possible_moves:
            # Check if the column is not empty before checking for a win
            if board.hauteurs_colonnes[move] > 0:
                board_copy = board.copier_grille()
                board_copy.jouer_coup_reversible(move, player_symbol)
                if board_copy.est_victoire(move):
                    del board_copy
                    return 1000
                del board_copy

            if time.time() - self.start_time > self.temp_max:
                break

            board_copy = board.copier_grille()
            board_copy.jouer_coup_reversible(move, player_symbol)
            score = -self.alphabeta(board_copy, depth - 1, -beta, -alpha, self.get_opponent_symbol(player_symbol))
            del board_copy

            alpha = max(alpha, score)
            if alpha >= beta:
                break  # Beta cutoff

        # Store in transposition table
        self.transposition_table.put(transposition_key, alpha)
        return alpha

    def evaluate_board(self, board, our_symbol):
        score = 0

        # Prioritize center column
        center_col = board.colonnes // 2
        center_count = board.grille[center_col].count(our_symbol)
        score += center_count * 2  # Slightly higher weight for center

        # Horizontal
        for r in range(board.lignes):
            row = [board.grille[c][r] if r < len(board.grille[c]) else "." for c in range(board.colonnes)]
            for c in range(board.colonnes - 3):
                window = row[c:c+4]
                score += self.evaluate_window(window, our_symbol)

        # Vertical
        for c in range(board.colonnes):
            col = board.grille[c]
            for r in range(board.lignes - 3):
                window = col[r:r+4]
                score += self.evaluate_window(window, our_symbol)

        # Positive sloped diagonal
        for r in range(board.lignes - 3):
            for c in range(board.colonnes - 3):
                window = [board.grille[c+i][r+i] if r+i < len(board.grille[c+i]) else "." for i in range(4)]
                score += self.evaluate_window(window, our_symbol)

        # Negative sloped diagonal
        for r in range(3, board.lignes):
            for c in range(board.colonnes - 3):
                window = [board.grille[c+i][r-i] if r-i < len(board.grille[c+i]) else "." for i in range(4)]
                score += self.evaluate_window(window, our_symbol)

        return score

    def evaluate_window(self, window, our_symbol):
        opponent_symbol = self.get_opponent_symbol(our_symbol)
        score = 0
        our_count = window.count(our_symbol)
        opponent_count = window.count(opponent_symbol)
        empty_count = window.count(".")

        if our_count == 4:
            score += 100
        elif our_count == 3 and empty_count == 1:
            score += 5
        elif our_count == 2 and empty_count == 2:
            score += 2

        if opponent_count == 3 and empty_count == 1:
            score -= 4  # Slightly less important to block than to create 3-in-a-row

        return score

    def get_opponent_symbol(self, symbol):
        return 'X' if symbol == 'O' else 'O'

    def board_to_tuple(self, board):
        return tuple(tuple(col) for col in board.grille)