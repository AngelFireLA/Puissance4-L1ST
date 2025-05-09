# bots/quantumnexus.py

import math
from bots.bot import Bot

COLUMNS = 7
ROWS = 6
HEIGHT = ROWS + 1  # include sentinel row
WIDTH = COLUMNS
# Precompute masks for board operations:
COL_MASK = [((1 << HEIGHT) - 1) << (i * HEIGHT) for i in range(WIDTH)]
BOTTOM_MASK = [1 << (i * HEIGHT) for i in range(WIDTH)]
# Full playable mask (rows 0..ROWS-1)
FULL_PLAY = sum(
    (((1 << ROWS) - 1) << (i * HEIGHT)) for i in range(WIDTH)
)
class QuantumNexus(Bot):
    """
    A bitboard-based Connect4 bot using alpha-beta negamax with:
      - immediate win/threat detection
      - transposition table
      - centre-biased move ordering
    """
    COLUMNS = 7
    ROWS = 6
    HEIGHT = ROWS + 1            # include sentinel row
    WIDTH = COLUMNS
    # Precompute masks for board operations:
    COL_MASK    = [((1 << HEIGHT) - 1) << (i * HEIGHT) for i in range(WIDTH)]
    BOTTOM_MASK = [1 << (i * HEIGHT) for i in range(WIDTH)]
    # Full playable mask (rows 0..ROWS-1)
    FULL_PLAY   = sum(
        (((1 << ROWS) - 1) << (i * HEIGHT)) for i in range(WIDTH)
    )

    def __init__(self, nom, symbole, profondeur=8):
        super().__init__(nom, symbole)
        self.profondeur = profondeur
        self.tt = {}  # transposition table

    def trouver_coup(self, plateau, joueur2) -> int:
        self.tt = {}  # transposition table
        # --- 1) build bitboards from plateau ---
        pos = opp = mask = 0
        for c in range(self.WIDTH):
            for r, cell in enumerate(plateau.grille[c]):
                bit = 1 << (c * self.HEIGHT + r)
                mask |= bit
                if cell == self.symbole:
                    pos |= bit
                else:
                    opp |= bit

        # --- 2) move ordering: closest to centre first ---
        centre = self.COLUMNS // 2
        moves = sorted(plateau.colonnes_jouables, key=lambda c: abs(c - centre))

        # --- 3) immediate win ---
        for col in moves:
            bit = (mask + self.BOTTOM_MASK[col]) & self.COL_MASK[col]
            if bit and self.is_win(pos | bit):
                return col

        # --- 4) block opponent's immediate win ---
        for col in moves:
            bit = (mask + self.BOTTOM_MASK[col]) & self.COL_MASK[col]
            if bit and self.is_win(opp | bit):
                return col

        # --- 5) full negamax search ---
        best_score = -math.inf
        best_move  = moves[0]
        alpha = -math.inf
        beta  =  math.inf

        for col in moves:
            bit = (mask + self.BOTTOM_MASK[col]) & self.COL_MASK[col]
            if not bit:
                continue
            score = -self._negamax(opp,
                                    pos | bit,
                                    mask | bit,
                                    self.profondeur - 1,
                                    -beta,
                                    -alpha)
            if score > best_score:
                best_score = score
                best_move  = col
            if score > alpha:
                alpha = score

        return best_move

    def _negamax(self, pos, opp, mask, depth, alpha, beta):
        """
        Standard negamax with alpha-beta and a small TT.
        pos  = current side's bitboard
        opp  = other side's bitboard
        mask = pos | opp
        """
        key = (pos, mask, depth)
        if key in self.tt:
            return self.tt[key]

        # Generate legal moves
        moves = [
            c for c in range(self.WIDTH)
            if not (mask & (1 << (c * self.HEIGHT + self.ROWS - 1)))
        ]
        if depth == 0 or not moves:
            return 0  # draw or leaf

        centre = self.COLUMNS // 2
        # order moves around centre
        moves.sort(key=lambda c: abs(c - centre))

        for col in moves:
            bit = (mask + self.BOTTOM_MASK[col]) & self.COL_MASK[col]
            # immediate win
            if self.is_win(pos | bit):
                val = (depth + 1) * 1000
                self.tt[key] = val
                return val

            score = -self._negamax(opp,
                                    pos | bit,
                                    mask | bit,
                                    depth - 1,
                                    -beta,
                                    -alpha)
            if score >= beta:
                self.tt[key] = score
                return score
            if score > alpha:
                alpha = score

        self.tt[key] = alpha
        return alpha

    @staticmethod
    def is_win(bitboard):
        """
        Fast bitboard win detection in four directions.
        """
        # vertical (shift by 1)
        m = bitboard & (bitboard >> 1)
        if m & (m >> 2):
            return True
        # horizontal (shift by HEIGHT)
        h = QuantumNexus.HEIGHT
        m = bitboard & (bitboard >> h)
        if m & (m >> (2 * h)):
            return True
        # diagonal /
        m = bitboard & (bitboard >> (h - 1))
        if m & (m >> (2 * (h - 1))):
            return True
        # diagonal \
        m = bitboard & (bitboard >> (h + 1))
        if m & (m >> (2 * (h + 1))):
            return True
        return False
