import time
import random
from .bot import Bot


class Zenith(Bot):
    """
    Zenith: A high-performance Connect 4 AI utilizing Iterative Deepening,
    Alpha-Beta Pruning, Transposition Tables (Zobrist Hashing),
    and a lightweight Heuristic Evaluation.
    """

    def __init__(self, nom, symbole, profondeur=10, temps_max=0):
        super().__init__(nom, symbole)
        self.profondeur = profondeur
        self.temps_max = temps_max
        self.adversaire_symbole = "O" if symbole == "X" else "X"

        # Performance Tracking
        self.positions_explorees = 0

        # Move Ordering (Center columns are strategically better)
        self.ordre_colonnes = [3, 2, 4, 1, 5, 0, 6]

        # Transposition Table (TT) for Zobrist Hashing
        self.table_transposition = {}

        # Zobrist Hashing Setup
        # 7 columns, 6 rows, 2 possible symbols
        self.zobrist_table = [[[random.getrandbits(64) for _ in range(2)]
                               for _ in range(6)]
                              for _ in range(7)]
        self.current_hash = 0

        # Score Constants
        self.INF = 1000000
        self.WIN_SCORE = 100000

    def _get_symbole_index(self, symbole):
        return 0 if symbole == self.symbole else 1

    def _update_hash(self, col, row, symbole):
        sym_idx = self._get_symbole_index(symbole)
        self.current_hash ^= self.zobrist_table[col][row][sym_idx]

    def evaluer_position(self, plateau):
        """
        Lightweight heuristic to evaluate non-terminal nodes.
        Focuses on center control and potential 4-in-a-row paths.
        """
        score = 0
        # Positional weights (center-heavy)
        weights = [
            [1, 2, 3, 3, 2, 1],  # Col 0
            [2, 3, 4, 4, 3, 2],  # Col 1
            [3, 4, 5, 5, 4, 3],  # Col 2
            [4, 5, 6, 6, 5, 4],  # Col 3
            [3, 4, 5, 5, 4, 3],  # Col 4
            [2, 3, 4, 4, 3, 2],  # Col 5
            [1, 2, 3, 3, 2, 1],  # Col 6
        ]

        for c in range(plateau.colonnes):
            for r in range(plateau.hauteurs_colonnes[c]):
                sym = plateau.grille[c][r]
                val = weights[c][r]
                if sym == self.symbole:
                    score += val
                else:
                    score -= val
        return score

    def trouver_coup(self, plateau, joueur2) -> int:
        """
        Entry point for the AI. Uses Iterative Deepening to find the
        best move within the allocated time.
        """
        self.positions_explorees = 0
        start_time = time.perf_counter()
        best_move = random.choice(list(plateau.colonnes_jouables))

        # Re-sync hash with current board state if starting mid-game
        self.current_hash = 0
        for c in range(plateau.colonnes):
            for r in range(plateau.hauteurs_colonnes[c]):
                self._update_hash(c, r, plateau.grille[c][r])

        # Iterative Deepening
        for d in range(1, self.profondeur + 1):
            current_best_move, current_score = self._search(plateau, d, start_time)

            if current_best_move is not None:
                best_move = current_best_move

            # If we found a guaranteed win or time is almost up, stop
            if abs(current_score) >= self.WIN_SCORE - 100:
                break

            elapsed = time.perf_counter() - start_time
            if self.temps_max and elapsed > self.temps_max * 0.8:
                break

        # print(f"Zenith: Depth {d} reached | Positions: {self.positions_explorees} | Move: {best_move}")
        return best_move

    def _search(self, plateau, depth, start_time):
        """
        Alpha-Beta wrapper for a specific depth.
        """
        best_score = -self.INF
        best_col = None

        # Primary Move Ordering: prioritize center and available moves
        moves = [c for c in self.ordre_colonnes if c in plateau.colonnes_jouables]

        # Check for immediate win for self (Depth 1 logic)
        for col in moves:
            removed = plateau.jouer_coup_reversible(col, self.symbole)
            if plateau.est_victoire(col):
                plateau.annuler_coup(col, removed, self.symbole)
                return col, self.WIN_SCORE
            plateau.annuler_coup(col, removed, self.symbole)

        alpha = -self.INF
        beta = self.INF

        for col in moves:
            # Time check
            if self.temps_max and (self.positions_explorees % 512 == 0):
                if time.perf_counter() - start_time > self.temps_max:
                    return best_col, best_score

            row = plateau.hauteurs_colonnes[col]
            self._update_hash(col, row, self.symbole)
            removed = plateau.jouer_coup_reversible(col, self.symbole)

            score = -self._alpha_beta(plateau, depth - 1, -beta, -alpha, False, start_time)

            plateau.annuler_coup(col, removed, self.symbole)
            self._update_hash(col, row, self.symbole)

            if score > best_score:
                best_score = score
                best_col = col
            alpha = max(alpha, best_score)

        return best_col, best_score

    def _alpha_beta(self, plateau, depth, alpha, beta, maximizing_player, start_time):
        self.positions_explorees += 1

        # TT Lookup
        tt_entry = self.table_transposition.get(self.current_hash)
        if tt_entry and tt_entry['depth'] >= depth:
            if tt_entry['flag'] == 'EXACT':
                return tt_entry['score']
            elif tt_entry['flag'] == 'LOWERBOUND':
                alpha = max(alpha, tt_entry['score'])
            elif tt_entry['flag'] == 'UPPERBOUND':
                beta = min(beta, tt_entry['score'])
            if alpha >= beta:
                return tt_entry['score']

        # Terminal state check
        if depth == 0 or plateau.est_nul():
            return self.evaluer_position(plateau) if maximizing_player else -self.evaluer_position(plateau)

        current_sym = self.symbole if maximizing_player else self.adversaire_symbole
        moves = [c for c in self.ordre_colonnes if c in plateau.colonnes_jouables]

        # Quick win check (essential for speed)
        for col in moves:
            removed = plateau.jouer_coup_reversible(col, current_sym)
            if plateau.est_victoire(col):
                plateau.annuler_coup(col, removed, current_sym)
                return self.WIN_SCORE + depth  # Prioritize faster wins
            plateau.annuler_coup(col, removed, current_sym)

        best_val = -self.INF

        for col in moves:
            if self.temps_max and (self.positions_explorees % 1024 == 0):
                if time.perf_counter() - start_time > self.temps_max:
                    return alpha

            row = plateau.hauteurs_colonnes[col]
            self._update_hash(col, row, current_sym)
            removed = plateau.jouer_coup_reversible(col, current_sym)

            val = -self._alpha_beta(plateau, depth - 1, -beta, -alpha, not maximizing_player, start_time)

            plateau.annuler_coup(col, removed, current_sym)
            self._update_hash(col, row, current_sym)

            best_val = max(best_val, val)
            alpha = max(alpha, val)
            if alpha >= beta:
                break

        # TT Store
        flag = 'EXACT'
        if best_val <= alpha:
            flag = 'UPPERBOUND'
        elif best_val >= beta:
            flag = 'LOWERBOUND'

        # Limit TT size to prevent memory bloat
        if len(self.table_transposition) < 500000:
            self.table_transposition[self.current_hash] = {
                'score': best_val,
                'depth': depth,
                'flag': flag
            }

        return best_val