# bots/graviton.py
"""
Graviton - High-performance Connect 4 AI

A deterministic Connect 4 engine using:
- Negamax with alpha-beta pruning and PVS
- Iterative deepening with time control
- Transposition table with exact/bound flags
- Killer moves and history heuristic for move ordering
- Late move reductions for deep searches
- Threat-aware evaluation function
"""

from .bot import Bot
import time


class Graviton(Bot):
    """
    Graviton - A powerful Connect 4 AI designed for competitive play.
    """

    WIN_SCORE = 100000

    # Pre-computed center-biased move ordering (center columns first)
    MOVE_ORDER = (3, 2, 4, 1, 5, 0, 6)

    # Column weights for evaluation (center is more valuable)
    COL_WEIGHTS = (1, 2, 3, 4, 3, 2, 1)

    def __init__(self, nom, symbole, profondeur=12, temps_max=0):
        """
        Initialize Graviton.

        Args:
            nom: Bot name
            symbole: Bot's piece symbol ('X' or 'O')
            profondeur: Maximum search depth when temps_max=0 (default 12)
            temps_max: Maximum time per move in seconds (0 = use fixed depth)
        """
        super().__init__(nom, symbole)
        self.profondeur = profondeur
        self.temps_max = temps_max
        self.coups = 0  # Nodes evaluated (for compatibility)

        # Search state
        self._tt = {}
        self._killers = None
        self._history = None
        self._start_time = 0
        self._time_up = False
        self._my_sym = None
        self._opp_sym = None

    def trouver_coup(self, plateau, joueur2) -> int:
        """Find the best move for the current position."""
        self.coups = 0
        self._start_time = time.perf_counter()
        self._time_up = False
        self._tt = {}
        self._killers = [[-1, -1] for _ in range(50)]
        self._history = [[0] * 7 for _ in range(2)]

        self._my_sym = self.symbole
        self._opp_sym = joueur2.symbole

        # Default: prefer center
        best_move = 3 if 3 in plateau.colonnes_jouables else next(iter(plateau.colonnes_jouables))

        # Check for immediate win
        for col in self.MOVE_ORDER:
            if col not in plateau.colonnes_jouables:
                continue
            undo = plateau.jouer_coup_reversible(col, self._my_sym)
            win = plateau.est_victoire(col)
            plateau.annuler_coup(col, undo, self._my_sym)
            if win:
                return col

        # Check for blocking opponent's immediate win
        block_col = -1
        for col in self.MOVE_ORDER:
            if col not in plateau.colonnes_jouables:
                continue
            undo = plateau.jouer_coup_reversible(col, self._opp_sym)
            win = plateau.est_victoire(col)
            plateau.annuler_coup(col, undo, self._opp_sym)
            if win:
                block_col = col
                break

        if self.temps_max > 0:
            # Iterative deepening
            for depth in range(1, 50):
                move, score = self._search_root(plateau, depth)

                if self._time_up:
                    break

                if move >= 0:
                    best_move = move

                # Early exit on forced win
                if score >= self.WIN_SCORE - 50:
                    break
        else:
            move, _ = self._search_root(plateau, self.profondeur)
            if move >= 0:
                best_move = move

        # If we must block, verify our choice blocks
        if block_col >= 0 and best_move != block_col:
            # Search didn't find better, must block
            if self._search_score(plateau, best_move) < self.WIN_SCORE - 50:
                best_move = block_col

        return best_move

    def _search_score(self, plateau, move):
        """Get the score for a specific move (for verification)."""
        undo = plateau.jouer_coup_reversible(move, self._my_sym)
        if plateau.est_victoire(move):
            plateau.annuler_coup(move, undo, self._my_sym)
            return self.WIN_SCORE
        score = -self._negamax(plateau, 1, -self.WIN_SCORE - 1, self.WIN_SCORE + 1, self._opp_sym, 1)
        plateau.annuler_coup(move, undo, self._my_sym)
        return score

    def _search_root(self, plateau, depth):
        """Root search with move ordering and PVS."""
        alpha = -self.WIN_SCORE - 1
        beta = self.WIN_SCORE + 1
        best_move = -1
        best_score = -self.WIN_SCORE - 1

        # Get TT move for ordering
        key = self._make_key(plateau)
        tt_move = self._tt[key][3] if key in self._tt else -1

        moves = []
        if tt_move >= 0 and tt_move in plateau.colonnes_jouables:
            moves.append(tt_move)
        for col in self.MOVE_ORDER:
            if col in plateau.colonnes_jouables and col not in moves:
                moves.append(col)

        first = True
        for col in moves:
            if self.temps_max > 0 and time.perf_counter() - self._start_time > self.temps_max * 0.95:
                self._time_up = True
                break

            undo = plateau.jouer_coup_reversible(col, self._my_sym)

            if plateau.est_victoire(col):
                plateau.annuler_coup(col, undo, self._my_sym)
                self._tt[key] = (depth, 0, self.WIN_SCORE, col)
                return col, self.WIN_SCORE

            if first:
                score = -self._negamax(plateau, depth - 1, -beta, -alpha, self._opp_sym, 1)
                first = False
            else:
                # PVS
                score = -self._negamax(plateau, depth - 1, -alpha - 1, -alpha, self._opp_sym, 1)
                if score > alpha and score < beta and not self._time_up:
                    score = -self._negamax(plateau, depth - 1, -beta, -score, self._opp_sym, 1)

            plateau.annuler_coup(col, undo, self._my_sym)

            if self._time_up:
                break

            if score > best_score:
                best_score = score
                best_move = col
            if score > alpha:
                alpha = score

        if best_move >= 0:
            self._tt[key] = (depth, 0, best_score, best_move)

        return best_move, best_score

    def _negamax(self, plateau, depth, alpha, beta, current_sym, ply):
        """Negamax with alpha-beta, TT, killers, history, and LMR."""
        self.coups += 1

        # Time check
        if self.temps_max > 0 and (self.coups & 2047) == 0:
            if time.perf_counter() - self._start_time > self.temps_max:
                self._time_up = True
                return 0

        if self._time_up:
            return 0

        if plateau.est_nul():
            return 0

        # TT lookup
        key = self._make_key(plateau)
        tt_entry = self._tt.get(key)
        tt_move = -1

        if tt_entry:
            tt_depth, tt_flag, tt_score, tt_move = tt_entry
            if tt_depth >= depth:
                if tt_flag == 0:
                    return tt_score
                elif tt_flag == 1 and tt_score >= beta:
                    return tt_score
                elif tt_flag == 2 and tt_score <= alpha:
                    return tt_score

        if depth == 0:
            return self._evaluate(plateau, current_sym)

        opp_sym = self._opp_sym if current_sym == self._my_sym else self._my_sym
        orig_alpha = alpha
        best_score = -self.WIN_SCORE - 1
        best_move = -1

        # Move ordering
        moves = self._get_moves(plateau, ply, tt_move)

        move_num = 0
        for col in moves:
            move_num += 1
            undo = plateau.jouer_coup_reversible(col, current_sym)

            if plateau.est_victoire(col):
                plateau.annuler_coup(col, undo, current_sym)
                score = self.WIN_SCORE - ply
                self._tt[key] = (depth, 0, score, col)
                return score

            # LMR
            reduction = 0
            if move_num > 3 and depth >= 3 and ply >= 2:
                reduction = 1

            if reduction > 0:
                score = -self._negamax(plateau, depth - 1 - reduction, -alpha - 1, -alpha, opp_sym, ply + 1)
                if score > alpha and not self._time_up:
                    score = -self._negamax(plateau, depth - 1, -beta, -alpha, opp_sym, ply + 1)
            else:
                if move_num == 1:
                    score = -self._negamax(plateau, depth - 1, -beta, -alpha, opp_sym, ply + 1)
                else:
                    score = -self._negamax(plateau, depth - 1, -alpha - 1, -alpha, opp_sym, ply + 1)
                    if score > alpha and score < beta and not self._time_up:
                        score = -self._negamax(plateau, depth - 1, -beta, -score, opp_sym, ply + 1)

            plateau.annuler_coup(col, undo, current_sym)

            if self._time_up:
                return 0

            if score > best_score:
                best_score = score
                best_move = col

            if score > alpha:
                alpha = score

            if alpha >= beta:
                # Killer update
                if ply < len(self._killers) and self._killers[ply][0] != col:
                    self._killers[ply][1] = self._killers[ply][0]
                    self._killers[ply][0] = col
                # History update
                self._history[0 if current_sym == self._my_sym else 1][col] += depth * depth
                break

        # TT store
        if best_move >= 0:
            flag = 2 if best_score <= orig_alpha else (1 if best_score >= beta else 0)
            self._tt[key] = (depth, flag, best_score, best_move)

        return best_score

    def _get_moves(self, plateau, ply, tt_move):
        """Get ordered moves: TT, killers, history-sorted."""
        playable = plateau.colonnes_jouables
        moves = []

        if tt_move >= 0 and tt_move in playable:
            moves.append(tt_move)

        if ply < len(self._killers):
            for k in self._killers[ply]:
                if k >= 0 and k in playable and k not in moves:
                    moves.append(k)

        remaining = [(c, self._history[0][c] + self._history[1][c])
                     for c in self.MOVE_ORDER if c in playable and c not in moves]
        remaining.sort(key=lambda x: -x[1])

        for c, _ in remaining:
            moves.append(c)

        return moves

    def _make_key(self, plateau):
        """Create hashable position key."""
        return tuple(tuple(c) for c in plateau.grille)

    def _evaluate(self, plateau, current_sym):
        """Fast evaluation: center control + threats."""
        opp_sym = self._opp_sym if current_sym == self._my_sym else self._my_sym
        score = 0

        # Center control
        for col in range(7):
            w = self.COL_WEIGHTS[col]
            for row in range(plateau.hauteurs_colonnes[col]):
                if plateau.grille[col][row] == current_sym:
                    score += w
                else:
                    score -= w

        # Threat counting
        score += self._count_threats(plateau, current_sym) * 12
        score -= self._count_threats(plateau, opp_sym) * 12

        return score

    def _count_threats(self, plateau, symbol):
        """Count 3-in-a-row positions where 4th is playable."""
        threats = 0
        heights = plateau.hauteurs_colonnes
        grille = plateau.grille

        # Horizontal
        for row in range(6):
            for col in range(4):
                cnt = empty_c = 0
                ok = True
                for i in range(4):
                    c = col + i
                    if row < heights[c]:
                        if grille[c][row] == symbol:
                            cnt += 1
                        else:
                            ok = False
                            break
                    elif empty_c < 0:
                        empty_c = c
                    else:
                        ok = False
                        break
                if ok and cnt == 3 and empty_c >= 0 and heights[empty_c] == row:
                    threats += 1

        # Vertical
        for col in range(7):
            h = heights[col]
            if 3 <= h < 6:
                if all(grille[col][h - 1 - i] == symbol for i in range(3)):
                    threats += 1

        return threats