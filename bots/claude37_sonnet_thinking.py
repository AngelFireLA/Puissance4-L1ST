import random
import time
from bots.bot import Bot


class QuantumConnect4(Bot):
    """
    Advanced Connect4 bot using iterative deepening Negamax with alpha-beta pruning,
    sophisticated evaluation function, and multiple optimization techniques.
    """

    def __init__(self, nom, symbole, profondeur, temps_max):
        super().__init__(nom, symbole)
        # Configuration
        self.profondeur = profondeur  # Maximum search depth
        self.temps_max = temps_max  # Time limit for move selection in seconds

        # State variables (reset before each move)
        self.transposition_table = {}  # Cache for positions
        self.opponent_symbol = None
        self.start_time = 0

        # Pre-calculate pattern scores (initialized only once)
        self.pattern_weights = {
            4: 100000,  # Four in a row (win)
            3: 100,  # Three in a row
            2: 10,  # Two in a row
        }

        # Killer move heuristic
        self.killer_moves = {}

        # ZOBRIST HASHING
        self.zobrist_table = self._initialize_zobrist()

    def _initialize_zobrist(self):
        """Initialize Zobrist hashing tables for fast position hashing"""
        import random
        random.seed(42)  # Fixed seed for reproducibility
        table = {}
        # For each cell and each possible piece
        for col in range(7):
            for row in range(6):
                for piece in ['X', 'O']:
                    table[(col, row, piece)] = random.randint(0, 2 ** 64)
        return table

    def trouver_coup(self, plateau, joueur2) -> int:
        """Find the best move in the current position"""
        # Reset state for this move
        self.transposition_table = {}
        self.killer_moves = {}
        self.opponent_symbol = joueur2.symbole
        self.start_time = time.time()

        # Check for immediate win
        for col in plateau.colonnes_jouables:
            if self._is_winning_move(plateau, col, self.symbole):
                return col

        # Check if opponent has a winning move and block it
        for col in plateau.colonnes_jouables:
            if self._is_winning_move(plateau, col, self.opponent_symbol):
                return col

        # Iterative deepening
        best_move = random.choice(list(plateau.colonnes_jouables))  # Fallback
        best_score = float('-inf')

        # Start with lower depth and increase as time allows
        for depth in range(1, self.profondeur + 1):
            current_best_move = None
            current_best_score = float('-inf')
            alpha = float('-inf')
            beta = float('inf')

            # Order moves (center columns first)
            center = plateau.colonnes // 2
            ordered_moves = sorted(plateau.colonnes_jouables, key=lambda col: abs(col - center))

            # Search each move at current depth
            for col in ordered_moves:
                removed = plateau.jouer_coup_reversible(col, self.symbole)

                if plateau.est_victoire(col):
                    score = 10000  # Win
                else:
                    score = -self._negamax(plateau, depth - 1, -beta, -alpha, self.opponent_symbol, 1)

                plateau.annuler_coup(col, removed, self.symbole)

                if score > current_best_score:
                    current_best_score = score
                    current_best_move = col

                alpha = max(alpha, score)

            # Update best move if we completed the iteration
            if current_best_move is not None and time.time() - self.start_time < self.temps_max:
                best_move = current_best_move
                best_score = current_best_score

            # If we found a winning move or running out of time, stop
            if best_score > 9000 or time.time() - self.start_time > self.temps_max:
                break

        return best_move

    def _negamax(self, plateau, depth, alpha, beta, symbole, ply):
        """Negamax algorithm with alpha-beta pruning"""
        # Time management
        if time.time() - self.start_time > self.temps_max:
            return 0

        # Check for draws
        if plateau.est_nul():
            return 0

        # Transposition table lookup
        alpha_orig = alpha
        hash_key = self._hash_position(plateau, symbole)
        if hash_key in self.transposition_table:
            tt_entry = self.transposition_table[hash_key]
            if tt_entry[0] >= depth:  # If stored with sufficient depth
                if tt_entry[2] == 0:  # Exact value
                    return tt_entry[1]
                elif tt_entry[2] == 1:  # Lower bound
                    alpha = max(alpha, tt_entry[1])
                elif tt_entry[2] == 2:  # Upper bound
                    beta = min(beta, tt_entry[1])

                if alpha >= beta:
                    return tt_entry[1]

        # Leaf node evaluation
        if depth == 0:
            return self._evaluate(plateau, symbole)

        # Move ordering - prioritize center columns and killer moves
        ordered_moves = self._order_moves(plateau, ply)

        max_value = float('-inf')
        best_move = None

        for col in ordered_moves:
            if col not in plateau.colonnes_jouables:
                continue

            removed = plateau.jouer_coup_reversible(col, symbole)

            # Check for immediate win
            if plateau.est_victoire(col):
                value = 10000 + depth  # Prefer quicker wins
                plateau.annuler_coup(col, removed, symbole)

                # Store killer move
                self.killer_moves[ply] = col

                # Store in transposition table
                self.transposition_table[hash_key] = (depth, value, 0)  # Exact value
                return value

            next_symbol = self.symbole if symbole == self.opponent_symbol else self.opponent_symbol
            value = -self._negamax(plateau, depth - 1, -beta, -alpha, next_symbol, ply + 1)

            plateau.annuler_coup(col, removed, symbole)

            if value > max_value:
                max_value = value
                best_move = col

            alpha = max(alpha, value)
            if alpha >= beta:
                # Store killer move
                self.killer_moves[ply] = col
                break

        # Store in transposition table
        flag = 0  # Exact value
        if max_value <= alpha_orig:
            flag = 2  # Upper bound
        elif max_value >= beta:
            flag = 1  # Lower bound

        self.transposition_table[hash_key] = (depth, max_value, flag)
        return max_value

    def _evaluate(self, plateau, symbole):
        """
        Evaluate the current position from the perspective of the given symbol.
        Uses pattern recognition and strategic positioning.
        """
        # If evaluation is taking too long, return a simple heuristic
        if time.time() - self.start_time > self.temps_max:
            return 0

        score = 0
        opponent = self.opponent_symbol if symbole == self.symbole else self.symbole

        # Evaluate horizontal, vertical, and diagonal patterns
        score += self._evaluate_lines(plateau, symbole, opponent)

        # Evaluate control of center columns (positional advantage)
        center_cols = [plateau.colonnes // 2, plateau.colonnes // 2 - 1, plateau.colonnes // 2 + 1]
        for col in center_cols:
            if 0 <= col < plateau.colonnes:
                # Count pieces in center columns
                score += sum(1 for piece in plateau.grille[col] if piece == symbole) * 3
                score -= sum(1 for piece in plateau.grille[col] if piece == opponent) * 2

        # Evaluate threats (potential winning moves)
        score += self._evaluate_threats(plateau, symbole) * 5
        score -= self._evaluate_threats(plateau, opponent) * 8

        return score

    def _evaluate_lines(self, plateau, symbole, opponent):
        """Evaluate patterns of pieces in all directions"""
        score = 0

        # Check horizontal patterns
        for row in range(plateau.lignes):
            for col in range(plateau.colonnes - 3):
                window = []
                for i in range(4):
                    if col + i < plateau.colonnes and row < plateau.hauteurs_colonnes[col + i]:
                        window.append(plateau.grille[col + i][row])
                    else:
                        window.append(None)  # Empty cell
                score += self._evaluate_window(window, symbole, opponent)

        # Check vertical patterns
        for col in range(plateau.colonnes):
            for row in range(plateau.lignes - 3):
                window = []
                for i in range(4):
                    if row + i < plateau.hauteurs_colonnes[col]:
                        window.append(plateau.grille[col][row + i])
                    else:
                        window.append(None)  # Empty cell
                score += self._evaluate_window(window, symbole, opponent)

        # Check diagonal patterns (positive slope)
        for row in range(plateau.lignes - 3):
            for col in range(plateau.colonnes - 3):
                window = []
                for i in range(4):
                    if col + i < plateau.colonnes and row + i < plateau.hauteurs_colonnes[col + i]:
                        window.append(plateau.grille[col + i][row + i])
                    else:
                        window.append(None)
                score += self._evaluate_window(window, symbole, opponent)

        # Check diagonal patterns (negative slope)
        for row in range(3, plateau.lignes):
            for col in range(plateau.colonnes - 3):
                window = []
                for i in range(4):
                    if col + i < plateau.colonnes and row - i >= 0 and row - i < plateau.hauteurs_colonnes[col + i]:
                        window.append(plateau.grille[col + i][row - i])
                    else:
                        window.append(None)
                score += self._evaluate_window(window, symbole, opponent)

        return score

    def _evaluate_window(self, window, symbole, opponent):
        """Evaluate a window of 4 cells"""
        score = 0

        # Count pieces
        player_count = window.count(symbole)
        opponent_count = window.count(opponent)
        empty_count = window.count(None)

        # Score based on piece configurations
        if player_count == 4:
            score += self.pattern_weights[4]
        elif player_count == 3 and empty_count == 1:
            score += self.pattern_weights[3]
        elif player_count == 2 and empty_count == 2:
            score += self.pattern_weights[2]

        # Penalize opponent's patterns
        if opponent_count == 3 and empty_count == 1:
            score -= self.pattern_weights[3] * 1.2  # Prioritize blocking opponent's threats

        return score

    def _evaluate_threats(self, plateau, symbole):
        """Count the number of winning threats (can win in next move)"""
        threats = 0
        for col in plateau.colonnes_jouables:
            if self._is_winning_move(plateau, col, symbole):
                threats += 1
        return threats

    def _order_moves(self, plateau, ply):
        """Order moves for better alpha-beta pruning"""
        moves = list(plateau.colonnes_jouables)

        # Prioritize moves
        scored_moves = []
        center = plateau.colonnes // 2

        for col in moves:
            score = 0

            # Prioritize center columns
            score -= abs(col - center) * 10

            # Prioritize killer moves
            if ply in self.killer_moves and self.killer_moves[ply] == col:
                score += 1000

            # Check if the move would make a threat or block a threat
            removed = plateau.jouer_coup_reversible(col, self.symbole)
            if plateau.est_victoire(col):
                score += 10000
            plateau.annuler_coup(col, removed, self.symbole)

            # Check if opponent would win after this move
            next_symbol = self.opponent_symbol
            removed = plateau.jouer_coup_reversible(col, next_symbol)
            if plateau.est_victoire(col):
                score += 5000
            plateau.annuler_coup(col, removed, next_symbol)

            scored_moves.append((col, score))

        # Sort by score (descending)
        return [col for col, score in sorted(scored_moves, key=lambda x: x[1], reverse=True)]

    def _is_winning_move(self, plateau, col, symbole):
        """Check if playing in this column would result in a win"""
        if col not in plateau.colonnes_jouables:
            return False

        removed = plateau.jouer_coup_reversible(col, symbole)
        result = plateau.est_victoire(col)
        plateau.annuler_coup(col, removed, symbole)

        return result

    def _hash_position(self, plateau, current_player):
        """Create a unique hash of the current position using Zobrist hashing"""
        hash_value = 0

        # Hash the board position
        for col in range(plateau.colonnes):
            for row in range(plateau.hauteurs_colonnes[col]):
                piece = plateau.grille[col][row]
                hash_value ^= self.zobrist_table.get((col, row, piece), 0)

        # Hash the current player
        hash_value ^= hash(current_player)

        return hash_value