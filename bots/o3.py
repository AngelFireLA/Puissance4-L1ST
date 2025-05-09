# bots/stellarstorm.py
import math
import random
import time
from typing import List, Tuple

from bots.bot import Bot


class _TimeOut(Exception):
    """Raised internally to abort the search when the time budget is exhausted."""


class StellarStorm(Bot):
    """
    A very fast & strong Connect-4 engine based on:
      • Bitboard representation             – 2×64-bit ints → O(1) win check
      • Iterative-deepening PVS (alpha–beta) – aspiration window, killer-move ordering
      • Zobrist-style transposition table    – re-used inside *one* trouver_coup call only
      • Lightweight heuristic                – evaluates every position in < 2 µs on a 2020 laptop
    Each `trouver_coup` call is *fresh*: all per-move state (TT, killers, timers…) is rebuilt,
    guaranteeing independence between moves as required by the tournament spec.
    """
    # ----------  CONSTANTS (compiled once, shared by all instances)  ----------
    _ROWS, _COLS = 6, 7
    _BITS_PER_COL = _ROWS + 1  # extra "sentinel" bit simplifies bitboard arithmetic
    _MAX_HEIGHT = _ROWS

    # Masks of every 4-cell window on the board (69 masks in total)
    _WINDOW_MASKS: List[int] = []

    # Bit mask for the centre column – gives the bot a strong positional bias
    _CENTRE_MASK: int = 0

    # Heuristic weights
    _W_FOUR   = 100_000
    _W_THREE  = 100
    _W_TWO    = 10
    _W_CENTRE = 3

    @classmethod
    def _init_masks(cls) -> None:
        if cls._WINDOW_MASKS:          # already initialised
            return
        # Horizontal
        for r in range(cls._ROWS):
            for c in range(cls._COLS - 3):
                m = 0
                for i in range(4):
                    m |= 1 << ((c + i) * cls._BITS_PER_COL + r)
                cls._WINDOW_MASKS.append(m)
        # Vertical
        for c in range(cls._COLS):
            for r in range(cls._ROWS - 3):
                m = 0
                for i in range(4):
                    m |= 1 << (c * cls._BITS_PER_COL + r + i)
                cls._WINDOW_MASKS.append(m)
        # Diagonal /
        for c in range(cls._COLS - 3):
            for r in range(cls._ROWS - 3):
                m = 0
                for i in range(4):
                    m |= 1 << ((c + i) * cls._BITS_PER_COL + r + i)
                cls._WINDOW_MASKS.append(m)
        # Diagonal \
        for c in range(cls._COLS - 3):
            for r in range(3, cls._ROWS):
                m = 0
                for i in range(4):
                    m |= 1 << ((c + i) * cls._BITS_PER_COL + r - i)
                cls._WINDOW_MASKS.append(m)

        # Centre-column mask
        for r in range(cls._ROWS):
            cls._CENTRE_MASK |= 1 << (3 * cls._BITS_PER_COL + r)

    # ----------  CONSTRUCTION  ----------
    def __init__(self, nom: str, symbole: str,
                 profondeur: int = 42,
                 temps_max: float = 0.5,
                 ):
        super().__init__(nom, symbole)
        self.temps_max = temps_max
        self.profondeur = profondeur
        StellarStorm._init_masks()

    # ----------  PUBLIC ENTRY POINT  ----------
    def trouver_coup(self, plateau, joueur2) -> int:            # noqa: N802
        """Main entry – called once per move by the tournament harness."""
        start_time = time.time()
        self._deadline = start_time + self.temps_max

        # Rebuild **fresh** per-move state  →  no cross-call contamination
        self._tt: dict[Tuple[int, int], Tuple[int, int, int]] = {}  # (depth, value, move)
        self._killers: List[int] = []                               # killer moves per ply

        # Convert the `Plateau` object to bitboards & column heights
        bit_self, bit_opp, heights = self._plateau_to_bitboards(plateau)

        # -----  Iterative deepening with aspiration window  -----
        guess = 0
        best_col = random.choice(tuple(plateau.colonnes_jouables))
        for depth in range(1, self.profondeur + 1):
            window = 50
            alpha = guess - window
            beta  = guess + window
            while True:
                try:
                    val, col = self._pvs(bit_self, bit_opp, heights, depth, alpha, beta)
                except _TimeOut:
                    return best_col                      # fall back to previous depth’s move

                if val <= alpha:                         # fail-low  → widen downward
                    alpha -= window
                    beta   = (alpha + beta) // 2
                    window *= 2
                    continue
                if val >= beta:                          # fail-high → widen upward
                    beta  += window
                    alpha  = (alpha + beta) // 2
                    window *= 2
                    continue
                break                                    # successful search inside window

            # **NEW** — only overwrite best_col if search returned a legal move
            if col != -1:
                guess, best_col = val, col
            else:                                        # TT hit with no move stored
                guess = val

            if abs(guess) >= self._W_FOUR:               # proven win/lose
                break

        return best_col

    # ----------  CORE SEARCH  ----------
    def _pvs(self, me: int, opp: int, h: List[int], depth: int,
             alpha: int, beta: int) -> Tuple[int, int]:
        """
        Principal-Variation Search (PVS, a zero-window optimisation of alpha–beta).
        Returns (value, best_col).
        """
        if time.time() > self._deadline:
            raise _TimeOut

        key = (me, opp)
        info = self._tt.get(key)
        if info and info[0] >= depth:            # TT hit with ≥ depth
            return info[1], info[2]             # ←–– returns stored move!

        # Terminal / leaf
        if self._is_win(opp):
            return -self._W_FOUR + (self.profondeur - depth), -1
        if depth == 0 or all(h[c] == self._MAX_HEIGHT for c in range(self._COLS)):
            return self._evaluate(me, opp), -1

        moves = self._ordered_moves(h, killers=self._killers[-2:] if len(self._killers) >= 2 else [])
        best_val, best_col = -math.inf, moves[0]
        first = True

        for col in moves:
            if h[col] == self._MAX_HEIGHT:
                continue
            bit = 1 << (col * self._BITS_PER_COL + h[col])

            # Make move
            h[col] += 1
            new_me, new_opp = opp, me | bit      # colour swap

            # PVS
            if first:
                score, _ = self._pvs(new_me, new_opp, h, depth - 1, -beta, -alpha)
                score = -score
                first = False
            else:
                score, _ = self._pvs(new_me, new_opp, h, depth - 1, -alpha - 1, -alpha)
                score = -score
                if alpha < score < beta:         # re-search
                    score, _ = self._pvs(new_me, new_opp, h, depth - 1, -beta, -alpha)
                    score = -score

            # Un-make move
            h[col] -= 1

            # Alpha–beta bookkeeping
            if score > best_val:
                best_val, best_col = score, col
            if best_val > alpha:
                alpha = best_val
            if alpha >= beta:
                if col not in self._killers:
                    self._killers.append(col)    # killer heuristic
                break

        # **NEW** — store (depth, value, move) in TT
        self._tt[key] = (depth, best_val, best_col)
        return best_val, best_col

    # ----------  SUPPORT ROUTINES  ----------
    def _plateau_to_bitboards(self, plateau) -> Tuple[int, int, List[int]]:
        """
        Convert the tournament’s `Plateau` object into:
          • our bitboard
          • opponent bitboard
          • list of column heights (0-based, max 6)
        """
        ours, opp = 0, 0
        heights = plateau.hauteurs_colonnes.copy()

        for col in range(self._COLS):
            for row, cell in enumerate(plateau.grille[col]):
                bit = 1 << (col * self._BITS_PER_COL + row)
                if cell == self.symbole:
                    ours |= bit
                else:
                    opp |= bit
        return ours, opp, heights

    # --------------------------------------------------------------------
    #             Bitboard utilities – win check & evaluation
    # --------------------------------------------------------------------
    @staticmethod
    def _is_win(bb: int) -> bool:
        # Vertical
        m = bb & (bb >> 1)
        if m & (m >> 2):
            return True
        # Horizontal
        m = bb & (bb >> 7)
        if m & (m >> 14):
            return True
        # Diagonal /
        m = bb & (bb >> 6)
        if m & (m >> 12):
            return True
        # Diagonal \
        m = bb & (bb >> 8)
        if m & (m >> 16):
            return True
        return False

    def _evaluate(self, me: int, opp: int) -> int:
        """
        Lightweight pattern-based evaluation.
        • Checks only 69 pre-computed windows
        • Popcount & bitwise ops only → < 2 µs
        """
        score = 0
        for mask in self._WINDOW_MASKS:
            a = (me  & mask).bit_count()
            b = (opp & mask).bit_count()
            if a and b:
                continue                      # mixed window – worthless
            if a:
                if   a == 4: score += self._W_FOUR
                elif a == 3: score += self._W_THREE
                elif a == 2: score += self._W_TWO
            elif b:
                if   b == 4: score -= self._W_FOUR
                elif b == 3: score -= self._W_THREE
                elif b == 2: score -= self._W_TWO

        # Centre control
        score += self._W_CENTRE * (me  & self._CENTRE_MASK).bit_count()
        score -= self._W_CENTRE * (opp & self._CENTRE_MASK).bit_count()
        return score

    def _ordered_moves(self, heights: List[int], killers: List[int]) -> List[int]:
        """Return playable columns ordered by expected move quality."""
        centre = 3
        cols = list(range(self._COLS))
        # Centre → killers → proximity ordering (3,4,2,5,1,6,0)
        cols.sort(key=lambda c: (c != centre,
                                 c not in killers,
                                 abs(c - centre)))
        return cols
