# bots/new_bot.py
import time
import math
import random
from typing import Optional, Tuple, Dict

from .bot import Bot  # must inherit from Bot


class Aetherion(Bot):
    """
    Aetherion — a deterministic, high-performance Connect 4 engine.

    Fixes vs previous draft:
      - Correct PVS re-search windows (use -alpha, not -score).
      - Zobrist side-to-move toggled exactly once per move (no conditional “set”).
      - TT flags computed against ORIGINAL alpha/beta (not the updated alpha).

    Core:
      - Iterative Deepening PVS (Principal Variation Search) + Alpha-Beta.
      - Transposition Table with Zobrist hashing (incremental updates).
      - Killer moves + History heuristic + center-first ordering.
      - Solid static evaluation (windows-of-4 + center bias + threat blocking).
      - Root fast checks: immediate win / single forced block.

    Config:
      Aetherion(nom, symbole, profondeur=8, temps_max=0.0,
                use_tt=True, use_killers=True, use_history=True)

    # DEBUG: Uncomment print lines marked with "DEBUG" to trace decisions.
    """

    # Board constants
    COLS = 7
    ROWS = 6
    SYM_TO_IDX = {"X": 0, "O": 1}

    # Evaluation weights
    W_CENTER = 4
    W_3      = 80
    W_2      = 8
    W_1      = 1
    W_BLOCK3 = 100
    W_BLOCK2 = 6

    WIN_SCORE = 10_000_000  # Must dominate all heuristic terms

    def __init__(self, nom, symbole, profondeur: int = 8, temps_max: float = 0.0,
                 use_tt: bool = True, use_killers: bool = True, use_history: bool = True):
        super().__init__(nom, symbole)
        self.profondeur = max(1, int(profondeur))
        self.temps_max = float(temps_max) if temps_max else 0.0

        # metrics
        self.coups = 0
        self.best_move_last = None
        self.best_score_last = 0
        self.depth_reached_last = 0

        # time
        self._deadline = 0.0
        self._stop = False

        # transposition table: key -> (depth, score, flag, move)
        # flag: -1=UPPERBOUND (score <= val), 0=EXACT, 1=LOWERBOUND (score >= val)
        self._tt: Dict[int, Tuple[int, int, int, Optional[int]]] = {}
        self._tt_enabled = use_tt

        # heuristics
        self._killers = [[] for _ in range(64)] if use_killers else None  # two per depth ideal
        self._history = [0] * self.COLS if use_history else None

        # deterministic RNG for zobrist seed / tie-breaking
        self._rng = random.Random(0xA37E1F)

        # zobrist (col,row,side)
        self._zob = [[[self._rng.randrange(1 << 63) for _ in range(2)]
                      for _ in range(self.ROWS)] for _ in range(self.COLS)]
        self._zob_turn = self._rng.randrange(1 << 63)

        # precompute all windows of 4
        self._windows = self._precompute_windows()

    # ---------------- Public API ----------------
    def trouver_coup(self, plateau, joueur2) -> int:
        """Return chosen column index for the current position."""
        self.coups = 0
        self._stop = False
        self.best_move_last = None
        self.best_score_last = 0
        self.depth_reached_last = 0

        me = self.symbole
        opp = joueur2.symbole if joueur2 else ("O" if me == "X" else "X")

        # deadline
        self._deadline = time.perf_counter() + self.temps_max if self.temps_max > 0 else float('inf')

        # initial zobrist hash (me to move)
        cur_hash = self._compute_hash(plateau, me_to_move=True)

        valid_cols = self._ordered_moves(plateau, None, None)
        if not valid_cols:
            return 0

        # Immediate winning move at root
        for c in valid_cols:
            undo_flag = plateau.jouer_coup_reversible(c, me)
            if plateau.est_victoire(c):
                plateau.annuler_coup(c, undo_flag, me)
                self.best_move_last = c
                self.best_score_last = self.WIN_SCORE
                self.depth_reached_last = 1
                return c
            plateau.annuler_coup(c, undo_flag, me)

        # Single forced block (opponent has exactly one immediate win)
        opp_wins = []
        for c in valid_cols:
            undo_flag = plateau.jouer_coup_reversible(c, opp)
            if plateau.est_victoire(c):
                opp_wins.append(c)
            plateau.annuler_coup(c, undo_flag, opp)
        if len(opp_wins) == 1:
            self.best_move_last = opp_wins[0]
            self.best_score_last = 0
            self.depth_reached_last = 1
            return opp_wins[0]

        # Iterative deepening with aspiration windows
        alpha = -self.WIN_SCORE
        beta = self.WIN_SCORE
        guess = 0

        best_move = valid_cols[0]
        max_depth = self._choose_max_depth()

        for depth in range(1, max_depth + 1):
            if self._time_up():
                break
            self._clear_depth_bookkeeping(depth)

            # small aspiration window around previous guess
            window = 30
            a = max(alpha, guess - window)
            b = min(beta, guess + window)

            score, move = self._pvs_root(plateau, depth, a, b, me, opp, cur_hash)

            # aspiration fail low/high → full window re-search
            if score <= a and not self._time_up():
                score, move = self._pvs_root(plateau, depth, -self.WIN_SCORE, guess, me, opp, cur_hash)
            elif score >= b and not self._time_up():
                score, move = self._pvs_root(plateau, depth, guess, self.WIN_SCORE, me, opp, cur_hash)

            if self._time_up():
                break

            if move is not None:
                best_move = move
                guess = score
                self.best_move_last = best_move
                self.best_score_last = score
                self.depth_reached_last = depth

            # tighten window around last score
            alpha = max(alpha, score - 4)
            beta = min(beta, score + 4)

        # DEBUG:
        # print(f"[Aetherion] depth={self.depth_reached_last} best={self.best_move_last} "
        #       f"score={self.best_score_last} nodes={self.coups}")

        return best_move

    # ---------------- Core Search ----------------
    def _pvs_root(self, plateau, depth: int, alpha: int, beta: int,
                  me: str, opp: str, hsh: int):
        best_score = -self.WIN_SCORE
        best_move = None

        moves = self._ordered_moves(plateau, depth, hsh)

        for i, col in enumerate(moves):
            if self._time_up():
                break
            if col not in plateau.colonnes_jouables:
                continue

            row = plateau.hauteurs_colonnes[col]
            undo_flag = plateau.jouer_coup_reversible(col, me)
            h2 = self._zob_apply(hsh, col, row, me)  # toggle side exactly once

            if plateau.est_victoire(col):
                score = self.WIN_SCORE - 1
            elif plateau.est_nul():
                score = 0
            else:
                if i == 0:
                    score = -self._pvs(plateau, depth - 1, -beta, -alpha, False, me, opp, h2, 1)
                else:
                    # zero-window probe
                    score = -self._pvs(plateau, depth - 1, -alpha - 1, -alpha, False, me, opp, h2, 1)
                    if alpha < score < beta:
                        # full-window re-search (FIX: use -beta, -alpha, not -score)
                        score = -self._pvs(plateau, depth - 1, -beta, -alpha, False, me, opp, h2, 1)

            plateau.annuler_coup(col, undo_flag, me)

            if score > best_score:
                best_score = score
                best_move = col
            if best_score > alpha:
                alpha = best_score
            if alpha >= beta:
                self._on_cut(depth, col)
                break

        return best_score, best_move

    def _pvs(self, plateau, depth: int, alpha: int, beta: int, me_to_move: bool,
             me_sym: str, opp_sym: str, hsh: int, ply: int) -> int:
        """Negamax with PVS; scores from the side-to-move perspective."""
        self.coups += 1
        if self._time_up():
            return self._evaluate(plateau, me_sym, opp_sym)

        if depth <= 0:
            return self._evaluate(plateau, me_sym, opp_sym)

        # TT probe
        if self._tt_enabled:
            tte = self._tt.get(hsh)
            if tte:
                ttd, ttscore, ttflag, _ = tte
                if ttd >= depth:
                    if ttflag == 0:  # EXACT
                        return ttscore
                    elif ttflag == -1 and ttscore <= alpha:  # UPPERBOUND
                        return ttscore
                    elif ttflag == 1 and ttscore >= beta:   # LOWERBOUND
                        return ttscore

        alpha0, beta0 = alpha, beta  # keep originals for TT flag
        moves = self._ordered_moves(plateau, depth, hsh)

        best = -self.WIN_SCORE
        best_move = None
        first = True

        cur_sym = me_sym if me_to_move else opp_sym
        next_me_to_move = not me_to_move

        for col in moves:
            if self._time_up():
                break
            if col not in plateau.colonnes_jouables:
                continue

            row = plateau.hauteurs_colonnes[col]
            undo_flag = plateau.jouer_coup_reversible(col, cur_sym)
            h2 = self._zob_apply(hsh, col, row, cur_sym)  # toggle side exactly once

            if plateau.est_victoire(col):
                score = self.WIN_SCORE - ply  # prefer faster wins
            elif plateau.est_nul():
                score = 0
            else:
                if first:
                    score = -self._pvs(plateau, depth - 1, -beta, -alpha, next_me_to_move, me_sym, opp_sym, h2, ply + 1)
                    first = False
                else:
                    # zero-window probe
                    score = -self._pvs(plateau, depth - 1, -alpha - 1, -alpha, next_me_to_move, me_sym, opp_sym, h2, ply + 1)
                    if alpha < score < beta:
                        # full-window re-search (FIX)
                        score = -self._pvs(plateau, depth - 1, -beta, -alpha, next_me_to_move, me_sym, opp_sym, h2, ply + 1)

            plateau.annuler_coup(col, undo_flag, cur_sym)

            if score > best:
                best = score
                best_move = col

            if best > alpha:
                alpha = best
            if alpha >= beta:
                self._on_cut(depth, col)
                break

        # Store to TT with correct flag against alpha0/beta0
        if self._tt_enabled and not self._time_up():
            flag = 0
            if best <= alpha0:
                flag = -1  # UPPERBOUND
            elif best >= beta0:
                flag = 1   # LOWERBOUND
            self._tt[hsh] = (depth, best, flag, best_move)

        return best

    # ---------------- Move Ordering & Heuristics ----------------
    def _ordered_moves(self, plateau, depth: Optional[int], hsh: Optional[int]):
        valid = list(plateau.colonnes_jouables)
        if not valid:
            return valid

        center = self.COLS // 2
        base = sorted(valid, key=lambda c: abs(c - center))  # center-first baseline

        tt_move = None
        if self._tt_enabled and hsh is not None:
            e = self._tt.get(hsh)
            if e and e[3] in base:
                tt_move = e[3]

        killers = []
        if self._killers is not None and depth is not None:
            killers = [k for k in self._killers[min(depth, len(self._killers)-1)] if k in base]

        hist = self._history if self._history is not None else [0] * self.COLS

        def key(c):
            score = 0
            if tt_move is not None and c == tt_move:
                score += 10_000
            if c in killers:
                score += 5_000
            score += (self.COLS - abs(c - center)) * 50  # center bias
            score += hist[c]
            return -score  # smaller is earlier

        return sorted(base, key=key)

    def _on_cut(self, depth: int, col: int):
        # killer moves
        if self._killers is not None and depth < len(self._killers):
            km = self._killers[depth]
            if col not in km:
                if len(km) < 2:
                    km.append(col)
                else:
                    km[1] = km[0]
                    km[0] = col
        # history
        if self._history is not None:
            self._history[col] += depth * depth

    # ---------------- Evaluation ----------------
    def _evaluate(self, plateau, me: str, opp: str) -> int:
        score = 0

        # center column preference
        center_col = self.COLS // 2
        hc = plateau.hauteurs_colonnes[center_col]
        center_me = sum(1 for r in range(hc) if plateau.grille[center_col][r] == me)
        center_opp = sum(1 for r in range(hc) if plateau.grille[center_col][r] == opp)
        score += (center_me - center_opp) * self.W_CENTER

        # windows
        get = self._get_cell
        for win in self._windows:
            m = o = e = 0
            for (c, r) in win:
                v = get(plateau, c, r)
                if v == me:
                    m += 1
                elif v == opp:
                    o += 1
                else:
                    e += 1

            if m and o:
                # contested window: skip (neutral)
                continue

            if m == 4:
                return self.WIN_SCORE - 1
            if o == 4:
                return -self.WIN_SCORE + 1

            if m == 3 and e == 1:
                score += self.W_3
            elif m == 2 and e == 2:
                score += self.W_2
            elif m == 1 and e == 3:
                score += self.W_1

            if o == 3 and e == 1:
                score -= self.W_BLOCK3
            elif o == 2 and e == 2:
                score -= self.W_BLOCK2

        return score

    @staticmethod
    def _get_cell(plateau, c: int, r: int):
        return plateau.grille[c][r] if r < plateau.hauteurs_colonnes[c] else None

    def _precompute_windows(self):
        wins = []

        # horizontal
        for r in range(self.ROWS):
            for c in range(self.COLS - 3):
                wins.append([(c + i, r) for i in range(4)])

        # vertical
        for c in range(self.COLS):
            for r in range(self.ROWS - 3):
                wins.append([(c, r + i) for i in range(4)])

        # diag up-right
        for c in range(self.COLS - 3):
            for r in range(self.ROWS - 3):
                wins.append([(c + i, r + i) for i in range(4)])

        # diag down-right
        for c in range(self.COLS - 3):
            for r in range(3, self.ROWS):
                wins.append([(c + i, r - i) for i in range(4)])

        return wins

    # ---------------- Zobrist ----------------
    def _compute_hash(self, plateau, me_to_move: bool):
        h = 0
        for c in range(self.COLS):
            hc = plateau.hauteurs_colonnes[c]
            for r in range(hc):
                v = plateau.grille[c][r]
                idx = self.SYM_TO_IDX[v]
                h ^= self._zob[c][r][idx]
        if me_to_move:
            h ^= self._zob_turn
        return h

    def _zob_apply(self, h: int, col: int, row: int, sym: str) -> int:
        """Apply a move to hash: XOR piece and toggle side-to-move exactly once."""
        idx = self.SYM_TO_IDX[sym]
        h ^= self._zob[col][row][idx]  # place piece
        h ^= self._zob_turn            # toggle side-to-move
        return h

    # ---------------- Time / Depth helpers ----------------
    def _time_up(self) -> bool:
        if self._stop:
            return True
        if time.perf_counter() >= self._deadline:
            self._stop = True
            return True
        return False

    def _choose_max_depth(self) -> int:
        if self.temps_max and self.temps_max > 0:
            return min(42, max(self.profondeur, 42))  # allow deepening; practical cap
        return self.profondeur

    def _clear_depth_bookkeeping(self, depth: int):
        if self._killers is not None and depth < len(self._killers):
            self._killers[depth].clear()
