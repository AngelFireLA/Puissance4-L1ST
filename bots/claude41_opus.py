import time
from .bot import Bot


class Thunderstrike(Bot):
    """
    Thunderstrike - A lightning-fast Connect 4 engine combining advanced search
    techniques with pattern recognition for devastating play strength.
    """

    def __init__(self, nom, symbole, profondeur=8, temps_max=0):
        super().__init__(nom, symbole)
        self.profondeur = profondeur
        self.temps_max = temps_max
        self.symbole_adversaire = "O" if symbole == "X" else "X"

        # Transposition table (position -> (score, depth, flag))
        self.tt = {}
        self.tt_hits = 0

        # Killer moves table [depth][slot] -> column
        self.killers = [[None, None] for _ in range(50)]

        # History heuristic table [column] -> score
        self.history = [0] * 7

        # Move ordering priorities (center columns first)
        self.column_order = [3, 2, 4, 1, 5, 0, 6]

        # Pattern weights for evaluation
        self.FOUR = 100000
        self.THREE_OPEN = 5000
        self.THREE_BLOCKED = 500
        self.TWO_OPEN = 100
        self.TWO_BLOCKED = 10
        self.CENTER_BONUS = [0, 1, 3, 5, 3, 1, 0]  # Bonus for center columns

        # Search statistics
        self.nodes_searched = 0
        self.start_time = 0
        self.time_limit_reached = False

    def trouver_coup(self, plateau, joueur2) -> int:
        """Find the best move using iterative deepening with time control."""
        self.nodes_searched = 0
        self.tt_hits = 0
        self.time_limit_reached = False
        self.start_time = time.perf_counter()

        # Clear killer moves for new search
        self.killers = [[None, None] for _ in range(50)]

        # Quick win/block check
        for col in plateau.colonnes_jouables:
            # Check if we can win
            plateau.jouer_coup_reversible(col, self.symbole)
            if plateau.est_victoire(col):
                plateau.annuler_coup(col, True, self.symbole)
                # print(f"Thunderstrike: Instant win at column {col}")
                return col
            plateau.annuler_coup(col, False, self.symbole)

            # Check if we need to block
            plateau.jouer_coup_reversible(col, self.symbole_adversaire)
            if plateau.est_victoire(col):
                plateau.annuler_coup(col, True, self.symbole_adversaire)
                # print(f"Thunderstrike: Blocking win at column {col}")
                return col
            plateau.annuler_coup(col, False, self.symbole_adversaire)

        best_move = 3 if 3 in plateau.colonnes_jouables else list(plateau.colonnes_jouables)[0]
        best_score = -float('inf')

        # Iterative deepening
        max_depth = min(self.profondeur, 42 - sum(plateau.hauteurs_colonnes))

        for depth in range(1, max_depth + 1):
            if self.temps_max > 0 and time.perf_counter() - self.start_time > self.temps_max:
                break

            current_best = None
            current_score = -float('inf')

            # Try moves in order of likelihood
            moves = self._order_moves(plateau, list(plateau.colonnes_jouables), depth)

            for col in moves:
                if self.temps_max > 0 and time.perf_counter() - self.start_time > self.temps_max:
                    self.time_limit_reached = True
                    break

                removed = plateau.jouer_coup_reversible(col, self.symbole)

                if plateau.est_victoire(col):
                    score = self.FOUR
                elif plateau.est_nul():
                    score = 0
                else:
                    score = -self._negamax(plateau, depth - 1, -float('inf'), float('inf'),
                                           self.symbole_adversaire, False, depth)

                plateau.annuler_coup(col, removed, self.symbole)

                if score > current_score:
                    current_score = score
                    current_best = col

                if score >= self.FOUR:
                    # print(f"Thunderstrike: Found winning path at depth {depth}, column {col}")
                    return col

            if not self.time_limit_reached and current_best is not None:
                best_move = current_best
                best_score = current_score

            # print(f"Depth {depth}: best={best_move}, score={best_score}, nodes={self.nodes_searched}")

            if self.time_limit_reached:
                break

        # print(f"Thunderstrike chooses column {best_move} (score: {best_score}, nodes: {self.nodes_searched}, tt_hits: {self.tt_hits})")
        return best_move

    def _negamax(self, plateau, depth, alpha, beta, symbole, maximizing, root_depth):
        """Negamax with alpha-beta pruning, transposition table, and killer moves."""
        self.nodes_searched += 1

        if self.temps_max > 0 and self.nodes_searched % 1000 == 0:
            if time.perf_counter() - self.start_time > self.temps_max:
                self.time_limit_reached = True
                return 0

        # Transposition table lookup
        pos_key = self._hash_position(plateau)
        if pos_key in self.tt:
            tt_score, tt_depth, tt_flag = self.tt[pos_key]
            if tt_depth >= depth:
                self.tt_hits += 1
                if tt_flag == 0:  # EXACT
                    return tt_score
                elif tt_flag == -1 and tt_score <= alpha:  # UPPERBOUND
                    return tt_score
                elif tt_flag == 1 and tt_score >= beta:  # LOWERBOUND
                    return tt_score

        if depth == 0:
            return self._evaluate(plateau, symbole)

        moves = list(plateau.colonnes_jouables)
        if not moves:
            return 0  # Draw

        # Move ordering
        moves = self._order_moves(plateau, moves, root_depth - depth)

        best_score = -float('inf')
        tt_flag = -1  # UPPERBOUND

        for col in moves:
            removed = plateau.jouer_coup_reversible(col, symbole)

            if plateau.est_victoire(col):
                score = self.FOUR - (root_depth - depth)  # Prefer quicker wins
                plateau.annuler_coup(col, removed, symbole)

                # Store in transposition table
                self.tt[pos_key] = (score, depth, 0)

                # Update killers
                self._update_killers(root_depth - depth, col)

                return score

            next_symbole = self.symbole_adversaire if symbole == self.symbole else self.symbole
            score = -self._negamax(plateau, depth - 1, -beta, -alpha, next_symbole,
                                   not maximizing, root_depth)

            plateau.annuler_coup(col, removed, symbole)

            if self.time_limit_reached:
                return 0

            if score > best_score:
                best_score = score

                if score > alpha:
                    alpha = score
                    tt_flag = 0  # EXACT

                    # Update history heuristic
                    self.history[col] += depth * depth

                    if alpha >= beta:
                        # Beta cutoff - update killers
                        self._update_killers(root_depth - depth, col)
                        tt_flag = 1  # LOWERBOUND
                        break

        # Store in transposition table
        self.tt[pos_key] = (best_score, depth, tt_flag)

        return best_score

    def _evaluate(self, plateau, symbole):
        """Fast pattern-based evaluation function."""
        score = 0

        # Evaluate all possible 4-in-a-row windows
        # Horizontal
        for row in range(plateau.lignes):
            for col in range(plateau.colonnes - 3):
                window = []
                for i in range(4):
                    if row < plateau.hauteurs_colonnes[col + i]:
                        window.append(plateau.grille[col + i][row])
                    else:
                        window.append(None)
                score += self._evaluate_window(window, symbole)

        # Vertical
        for col in range(plateau.colonnes):
            for row in range(plateau.lignes - 3):
                window = []
                for i in range(4):
                    if row + i < plateau.hauteurs_colonnes[col]:
                        window.append(plateau.grille[col][row + i])
                    else:
                        window.append(None)
                score += self._evaluate_window(window, symbole)

        # Diagonal (positive slope)
        for row in range(plateau.lignes - 3):
            for col in range(plateau.colonnes - 3):
                window = []
                for i in range(4):
                    if row + i < plateau.hauteurs_colonnes[col + i]:
                        window.append(plateau.grille[col + i][row + i])
                    else:
                        window.append(None)
                score += self._evaluate_window(window, symbole)

        # Diagonal (negative slope)
        for row in range(3, plateau.lignes):
            for col in range(plateau.colonnes - 3):
                window = []
                for i in range(4):
                    if row - i < plateau.hauteurs_colonnes[col + i]:
                        window.append(plateau.grille[col + i][row - i])
                    else:
                        window.append(None)
                score += self._evaluate_window(window, symbole)

        # Add center column bonus
        for col in range(plateau.colonnes):
            for row in range(plateau.hauteurs_colonnes[col]):
                if plateau.grille[col][row] == symbole:
                    score += self.CENTER_BONUS[col]
                elif plateau.grille[col][row] == (self.symbole_adversaire if symbole == self.symbole else self.symbole):
                    score -= self.CENTER_BONUS[col]

        return score

    def _evaluate_window(self, window, symbole):
        """Evaluate a 4-cell window."""
        opp_symbole = self.symbole_adversaire if symbole == self.symbole else self.symbole

        my_count = window.count(symbole)
        opp_count = window.count(opp_symbole)
        empty_count = window.count(None)

        if my_count == 4:
            return self.FOUR
        elif my_count == 3 and empty_count == 1:
            return self.THREE_OPEN
        elif my_count == 2 and empty_count == 2:
            return self.TWO_OPEN
        elif opp_count == 3 and empty_count == 1:
            return -self.THREE_BLOCKED
        elif opp_count == 2 and empty_count == 2:
            return -self.TWO_BLOCKED

        return 0

    def _order_moves(self, plateau, moves, depth):
        """Order moves for better pruning."""
        scored_moves = []

        for col in moves:
            score = 0

            # Killer moves bonus
            if col == self.killers[depth][0]:
                score += 1000
            elif col == self.killers[depth][1]:
                score += 900

            # History heuristic
            score += self.history[col]

            # Center preference
            score += self.CENTER_BONUS[col] * 10

            # Immediate threat detection
            removed = plateau.jouer_coup_reversible(col, self.symbole)
            if plateau.est_victoire(col):
                score += 10000
            plateau.annuler_coup(col, removed, self.symbole)

            removed = plateau.jouer_coup_reversible(col, self.symbole_adversaire)
            if plateau.est_victoire(col):
                score += 5000
            plateau.annuler_coup(col, removed, self.symbole_adversaire)

            scored_moves.append((score, col))

        scored_moves.sort(reverse=True)
        return [col for _, col in scored_moves]

    def _update_killers(self, depth, col):
        """Update killer moves table."""
        if depth < len(self.killers):
            if self.killers[depth][0] != col:
                self.killers[depth][1] = self.killers[depth][0]
                self.killers[depth][0] = col

    def _hash_position(self, plateau):
        """Create a hash key for the current position."""
        # Simple but effective: tuple of column heights and top pieces
        key = []
        for col in range(plateau.colonnes):
            key.append(plateau.hauteurs_colonnes[col])
            if plateau.hauteurs_colonnes[col] > 0:
                key.append(plateau.grille[col][-1])
            else:
                key.append(0)
        return tuple(key)