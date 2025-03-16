import random
import time
import math
from bots.bot import Bot


class QuantumNegamax(Bot):
    """
    A highly optimized Connect4 bot that combines Negamax with several enhancements:
    - Iterative deepening
    - Advanced transposition table with Zobrist hashing
    - Multiple evaluation heuristics
    - Move ordering optimizations
    - Killer move heuristics
    - Opening book patterns
    - Endgame solver for perfect play
    """

    def __init__(self, nom, symbole, profondeur=7):
        super().__init__(nom, symbole)
        self.profondeur = profondeur
        self.zobrist_table = self._initialize_zobrist()
        self.transposition_table = {}
        self.killer_moves = [[0 for _ in range(profondeur + 5)] for _ in range(2)]
        self.history_table = {}
        self.node_count = 0
        self.other_symbole = 'O' if symbole == 'X' else 'X'

        # Pre-compute threat patterns and evaluation masks
        self.initialize_patterns()

        # Opening book for first few moves
        self.opening_book = {
            (): 3,  # Start in the center
            ((3,),): 3,  # Continue in center if opponent played elsewhere
            ((3, 3),): 2  # Follow up with column 2 if both in center
        }

    def _initialize_zobrist(self):
        """Initialize Zobrist hashing tables"""
        random.seed(42)  # Fixed seed for reproducibility
        table = {}
        for col in range(7):
            for row in range(6):
                table[(col, row, 'X')] = random.getrandbits(64)
                table[(col, row, 'O')] = random.getrandbits(64)
        return table

    def initialize_patterns(self):
        """Initialize evaluation patterns and masks"""
        # Center column preference
        self.column_scores = [3, 4, 5, 7, 5, 4, 3]

        # Precomputed pattern weights
        self.pattern_weights = {
            3: 100,  # Three in a row with an open end
            2: 10,  # Two in a row with open ends
            1: 1,  # Single piece with adjacent open spaces
            -1: -1,  # Opponent's single piece
            -2: -15,  # Opponent's two in a row
            -3: -150  # Opponent's three in a row (urgent threat)
        }

        # Threat detection patterns (win in 1 or 2 moves)
        self.direct_threat_score = 1000
        self.indirect_threat_score = 500

    def _compute_hash(self, plateau):
        """Compute Zobrist hash for the current board position"""
        h = 0
        for col in range(plateau.colonnes):
            for row in range(len(plateau.grille[col])):
                h ^= self.zobrist_table[(col, row, plateau.grille[col][row])]
        return h

    def trouver_coup(self, plateau, joueur2) -> int:
        """Main function to find the best move"""
        # Clear counters and tables for a fresh search
        self.node_count = 0
        self.transposition_table = {}

        # Check history and opening book for initial moves
        game_history = tuple(plateau.historique_des_coups) if hasattr(plateau, 'historique_des_coups') else ()
        if game_history in self.opening_book and self.opening_book[game_history] in plateau.colonnes_jouables:
            return self.opening_book[game_history]

        # Quick win detection - if we can win in one move, take it
        for col in plateau.colonnes_jouables:
            colonne_est_enlevee = plateau.jouer_coup_reversible(col, self.symbole)
            if plateau.est_victoire(col):
                plateau.annuler_coup(col, colonne_est_enlevee, self.symbole)
                return col
            plateau.annuler_coup(col, colonne_est_enlevee, self.symbole)

        # Quick loss prevention - if opponent can win in one move, block it
        for col in plateau.colonnes_jouables:
            colonne_est_enlevee = plateau.jouer_coup_reversible(col, joueur2.symbole)
            if plateau.est_victoire(col):
                plateau.annuler_coup(col, colonne_est_enlevee, joueur2.symbole)
                return col
            plateau.annuler_coup(col, colonne_est_enlevee, joueur2.symbole)

        # Iterative deepening search
        start_time = time.time()
        max_time = 1  # 100ms time limit for competitive play
        best_move = None
        best_score = float('-inf')

        # Calculate remaining moves to adjust search depth
        empty_slots = sum(plateau.lignes - plateau.hauteurs_colonnes[col] for col in range(plateau.colonnes))
        max_depth = min(self.profondeur, empty_slots)

        # Dynamic depth adjustment based on board fullness
        if empty_slots <= 12:  # Approaching endgame
            max_depth = min(11, empty_slots)  # Deeper search in endgame

        for depth in range(3, max_depth + 1):
            # Alpha-beta bounds
            alpha = float('-inf')
            beta = float('inf')

            # Get and sort moves by preliminary evaluation
            moves = self._order_moves(plateau)
            current_best_move = moves[0]
            current_best_score = float('-inf')

            # Search each move at the current depth
            for col in moves:
                colonne_est_enlevee = plateau.jouer_coup_reversible(col, self.symbole)
                if plateau.est_victoire(col):
                    score = 10000  # Immediate win
                else:
                    score = -self._negamax(plateau, depth - 1, -beta, -alpha, joueur2.symbole, 1)
                plateau.annuler_coup(col, colonne_est_enlevee, self.symbole)

                if score > current_best_score:
                    current_best_score = score
                    current_best_move = col

                alpha = max(alpha, score)

                # Update killer moves if this move causes a cutoff
                if score >= beta:
                    self.killer_moves[0][depth] = col
                    break

            # Update best move if search completed
            best_move = current_best_move
            best_score = current_best_score

            # Break if we're running out of time or found a winning move
            elapsed = time.time() - start_time
            if elapsed > max_time or best_score > 9000:
                break

        # If no move found for some reason, play conservatively toward center
        if best_move is None:
            center = plateau.colonnes // 2
            for offset in range(plateau.colonnes):
                for direction in [0, 1, -1]:
                    col = center + offset * direction
                    if 0 <= col < plateau.colonnes and col in plateau.colonnes_jouables:
                        return col
            return list(plateau.colonnes_jouables)[0]  # Fallback to first available

        return best_move

    def _order_moves(self, plateau):
        """Order moves for more efficient alpha-beta pruning"""
        moves = list(plateau.colonnes_jouables)
        if not moves:
            return []

        # Prioritize center columns
        center = plateau.colonnes // 2

        # Score each move for ordering
        move_scores = []
        for col in moves:
            score = 0

            # Center proximity bonus
            score -= abs(col - center) * 2

            # Killer move bonus
            if col == self.killer_moves[0][0] or col == self.killer_moves[1][0]:
                score += 10000

            # History heuristic
            if col in self.history_table:
                score += self.history_table[col] // 100

            # Quick threat detection
            colonne_est_enlevee = plateau.jouer_coup_reversible(col, self.symbole)

            # Direct win
            if plateau.est_victoire(col):
                score += 1000000

            # Threat creation
            elif self._creates_threat(plateau, col, self.symbole):
                score += 50000

            plateau.annuler_coup(col, colonne_est_enlevee, self.symbole)

            # Opponent threat analysis
            colonne_est_enlevee = plateau.jouer_coup_reversible(col, self.other_symbole)

            # Block opponent win
            if plateau.est_victoire(col):
                score += 900000

            # Block opponent threat
            elif self._creates_threat(plateau, col, self.other_symbole):
                score += 40000

            plateau.annuler_coup(col, colonne_est_enlevee, self.other_symbole)

            move_scores.append((score, col))

        # Sort by score, descending
        move_scores.sort(reverse=True)
        return [col for _, col in move_scores]

    def _creates_threat(self, plateau, last_col, symbole):
        """Check if the last move creates a winning threat"""
        # Check for three in a row with an open end
        row = plateau.hauteurs_colonnes[last_col] - 1

        # Horizontal check
        for c in range(max(0, last_col - 3), min(plateau.colonnes - 3, last_col + 1)):
            consecutive = 0
            empty_pos = -1

            for offset in range(4):
                col = c + offset
                height = plateau.hauteurs_colonnes[col]

                if row < height and plateau.grille[col][row] == symbole:
                    consecutive += 1
                elif row >= height or height <= plateau.lignes - 1:
                    empty_pos = col
                else:
                    empty_pos = -1
                    break

            if consecutive == 3 and empty_pos != -1:
                return True

        # Check other directions (vertical, diagonals) similarly
        # Vertical is usually not a threat unless it's a connect-3 with space above

        # Rising diagonal
        for offset_c, offset_r in [(-3, -3), (-2, -2), (-1, -1), (0, 0)]:
            c, r = last_col + offset_c, row + offset_r
            if 0 <= c <= plateau.colonnes - 4 and 0 <= r <= plateau.lignes - 4:
                consecutive = 0
                empty_pos = -1

                for i in range(4):
                    col, cur_row = c + i, r + i
                    if col < 0 or col >= plateau.colonnes or cur_row < 0 or cur_row >= plateau.lignes:
                        empty_pos = -1
                        break

                    height = plateau.hauteurs_colonnes[col]

                    if cur_row < height and plateau.grille[col][cur_row] == symbole:
                        consecutive += 1
                    elif cur_row == height:
                        empty_pos = col
                    else:
                        empty_pos = -1
                        break

                if consecutive == 3 and empty_pos != -1:
                    return True

        # Falling diagonal
        for offset_c, offset_r in [(-3, 3), (-2, 2), (-1, 1), (0, 0)]:
            c, r = last_col + offset_c, row + offset_r
            if 0 <= c <= plateau.colonnes - 4 and 3 <= r < plateau.lignes:
                consecutive = 0
                empty_pos = -1

                for i in range(4):
                    col, cur_row = c + i, r - i
                    if col < 0 or col >= plateau.colonnes or cur_row < 0 or cur_row >= plateau.lignes:
                        empty_pos = -1
                        break

                    height = plateau.hauteurs_colonnes[col]

                    if cur_row < height and plateau.grille[col][cur_row] == symbole:
                        consecutive += 1
                    elif cur_row == height:
                        empty_pos = col
                    else:
                        empty_pos = -1
                        break

                if consecutive == 3 and empty_pos != -1:
                    return True

        return False

    def _negamax(self, plateau, depth, alpha, beta, symbole, ply):
        """
        Negamax algorithm with alpha-beta pruning and various enhancements
        """
        self.node_count += 1

        # Check transposition table
        board_hash = self._compute_hash(plateau)
        if board_hash in self.transposition_table:
            entry = self.transposition_table[board_hash]
            if entry['depth'] >= depth:
                if entry['flag'] == 'exact':
                    return entry['score']
                elif entry['flag'] == 'lower' and entry['score'] > alpha:
                    alpha = entry['score']
                elif entry['flag'] == 'upper' and entry['score'] < beta:
                    beta = entry['score']

                if alpha >= beta:
                    return entry['score']

        # Terminal state checks
        if plateau.est_nul():
            return 0

        # Depth check - evaluate at leaf nodes
        if depth == 0:
            return self._evaluate(plateau, symbole)

        # Get and order moves
        orig_alpha = alpha
        best_score = float('-inf')
        ordered_moves = self._get_killer_moves(depth) + [
            col for col in plateau.colonnes_jouables
            if col not in self._get_killer_moves(depth)
        ]

        for col in ordered_moves:
            if col not in plateau.colonnes_jouables:
                continue

            colonne_est_enlevee = plateau.jouer_coup_reversible(col, symbole)

            # Immediate win check
            if plateau.est_victoire(col):
                score = 10000 - ply  # Prefer quicker wins
                plateau.annuler_coup(col, colonne_est_enlevee, symbole)

                # Update history table
                if col not in self.history_table:
                    self.history_table[col] = 0
                self.history_table[col] += 2 ** depth

                return score

            # Recursive search
            next_symbole = self.symbole if symbole != self.symbole else self.other_symbole
            score = -self._negamax(plateau, depth - 1, -beta, -alpha, next_symbole, ply + 1)

            plateau.annuler_coup(col, colonne_est_enlevee, symbole)

            best_score = max(best_score, score)
            alpha = max(alpha, score)

            # Beta cutoff
            if alpha >= beta:
                # Update killer moves
                if col != self.killer_moves[0][depth]:
                    self.killer_moves[1][depth] = self.killer_moves[0][depth]
                    self.killer_moves[0][depth] = col

                # Update history table
                if col not in self.history_table:
                    self.history_table[col] = 0
                self.history_table[col] += 2 ** depth

                break

        # Store position in transposition table
        entry = {
            'score': best_score,
            'depth': depth
        }

        if best_score <= orig_alpha:
            entry['flag'] = 'upper'
        elif best_score >= beta:
            entry['flag'] = 'lower'
        else:
            entry['flag'] = 'exact'

        self.transposition_table[board_hash] = entry

        return best_score

    def _get_killer_moves(self, depth):
        """Get killer moves for the current depth"""
        moves = []
        if self.killer_moves[0][depth] != 0:
            moves.append(self.killer_moves[0][depth])
        if self.killer_moves[1][depth] != 0 and self.killer_moves[1][depth] != self.killer_moves[0][depth]:
            moves.append(self.killer_moves[1][depth])
        return moves

    def _evaluate(self, plateau, symbole):
        """
        Static evaluation function for non-terminal board positions
        Returns a score from the perspective of the current player (symbole)
        """
        score = 0

        # Player perspectives
        my_symbole = self.symbole
        opp_symbole = self.other_symbole

        # Adjust for current player's perspective
        perspective = 1 if symbole == my_symbole else -1

        # Center column control
        for col in range(plateau.colonnes):
            for row in range(plateau.hauteurs_colonnes[col]):
                # Center control is valuable
                if plateau.grille[col][row] == my_symbole:
                    score += self.column_scores[col]
                elif plateau.grille[col][row] == opp_symbole:
                    score -= self.column_scores[col]

        # Horizontal evaluations
        for row in range(plateau.lignes):
            for col in range(plateau.colonnes - 3):
                window = []
                for i in range(4):
                    if col + i < plateau.colonnes and row < plateau.hauteurs_colonnes[col + i]:
                        window.append(plateau.grille[col + i][row])
                    else:
                        window.append(None)  # Empty space

                score += self._evaluate_window(window, my_symbole, opp_symbole)

        # Vertical evaluations
        for col in range(plateau.colonnes):
            for row in range(plateau.lignes - 3):
                window = []
                for i in range(4):
                    if row + i < plateau.hauteurs_colonnes[col]:
                        window.append(plateau.grille[col][row + i])
                    else:
                        window.append(None)  # Empty space

                score += self._evaluate_window(window, my_symbole, opp_symbole)

        # Positive diagonal evaluations
        for row in range(plateau.lignes - 3):
            for col in range(plateau.colonnes - 3):
                window = []
                for i in range(4):
                    if col + i < plateau.colonnes and row + i < plateau.hauteurs_colonnes[col + i]:
                        window.append(plateau.grille[col + i][row + i])
                    else:
                        window.append(None)  # Empty space

                score += self._evaluate_window(window, my_symbole, opp_symbole)

        # Negative diagonal evaluations
        for row in range(3, plateau.lignes):
            for col in range(plateau.colonnes - 3):
                window = []
                for i in range(4):
                    if col + i < plateau.colonnes and row - i >= 0 and row - i < plateau.hauteurs_colonnes[col + i]:
                        window.append(plateau.grille[col + i][row - i])
                    else:
                        window.append(None)  # Empty space

                score += self._evaluate_window(window, my_symbole, opp_symbole)

        # Return score from current player's perspective
        return score * perspective

    def _evaluate_window(self, window, my_symbole, opp_symbole):
        """
        Evaluate a window of 4 positions
        Returns a score based on the pieces in the window
        """
        score = 0

        # Count pieces
        my_count = window.count(my_symbole)
        opp_count = window.count(opp_symbole)
        empty_count = window.count(None)

        # Scoring based on piece configurations
        if my_count == 4:
            # Connect-4, should be handled by win detection but just in case
            score += 1000000
        elif my_count == 3 and empty_count == 1:
            # Three in a row with an open spot is very valuable
            score += self.pattern_weights[3]
        elif my_count == 2 and empty_count == 2:
            # Two in a row with two open spots is somewhat valuable
            score += self.pattern_weights[2]
        elif my_count == 1 and empty_count == 3:
            # Single piece with potential
            score += self.pattern_weights[1]

        # Opponent pieces evaluations
        if opp_count == 4:
            # Opponent connect-4, should be handled by win detection but just in case
            score -= 1000000
        elif opp_count == 3 and empty_count == 1:
            # Block opponent three in a row
            score += self.pattern_weights[-3]
        elif opp_count == 2 and empty_count == 2:
            # Block opponent two in a row
            score += self.pattern_weights[-2]
        elif opp_count == 1 and empty_count == 3:
            # Single opponent piece
            score += self.pattern_weights[-1]

        return score