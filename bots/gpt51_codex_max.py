import math
import time
from typing import Dict, List, Optional, Sequence, Tuple

from .bot import Bot


class HeliosMonarch(Bot):
    """
    A strong, deterministic Connect 4 AI using iterative-deepening Negamax with
    alpha-beta pruning, move ordering, and a handcrafted positional heuristic.
    The search respects a configurable time (temps_max) or depth (profondeur) budget.
    """

    def __init__(
        self,
        nom: str,
        symbole: str,
        profondeur: int = 4,
        temps_max: float = 0,
        aspiration: float = 1.5,
    ):
        """
        :param nom: Bot name.
        :param symbole: Bot symbol, e.g., "X" or "O".
        :param profondeur: Maximum search depth if no time is given or time runs long.
        :param temps_max: Time budget in seconds per move (<=0 disables time control).
        :param aspiration: Aspiration window radius around previous score (helps ordering).
        """
        super().__init__(nom, symbole)
        self.profondeur = max(1, profondeur)
        self.temps_max = max(0.0, temps_max)
        self.aspiration = max(0.1, aspiration)
        self._deadline: float = 0.0
        self._transpo: Dict[Tuple, Tuple[int, float, int]] = {}  # key -> (depth, value, flag)
        self._last_best_col: Optional[int] = None
        self._opp_symbole: Optional[str] = None

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #
    def trouver_coup(self, plateau, joueur2) -> int:
        """
        Entry point used by the game engine. Chooses the best column.
        """
        self._opp_symbole = joueur2.symbole
        playable = list(plateau.colonnes_jouables)
        if len(playable) == 1:
            return playable[0]

        self._transpo.clear()
        start_time = time.perf_counter()
        self._deadline = (
            start_time + self.temps_max if self.temps_max > 0 else float("inf")
        )

        # Fast tactical checks: immediate win, then block opponent win.
        winning = self._find_forcing_move(plateau, self.symbole)
        if winning is not None:
            return winning
        block = self._find_forcing_move(plateau, self._opp_symbole)
        if block is not None:
            return block

        best_col = playable[0]
        best_score = -math.inf

        # Iterative deepening with aspiration window
        window_center = 0.0
        for depth in range(1, self.profondeur + 1):
            if time.perf_counter() > self._deadline:
                break

            alpha = window_center - self.aspiration
            beta = window_center + self.aspiration
            score, col = self._search_root(plateau, depth, alpha, beta)

            # If aspiration failed, re-search with full window
            if score <= alpha or score >= beta:
                score, col = self._search_root(plateau, depth, -math.inf, math.inf)

            if col is not None:
                best_col = col
                best_score = score
                window_center = score
                self._last_best_col = col

        # Fallback if time expired very early
        if self._last_best_col is not None:
            best_col = self._last_best_col

        return best_col

    # ------------------------------------------------------------------ #
    # Search internals                                                   #
    # ------------------------------------------------------------------ #
    def _search_root(
        self, plateau, depth: int, alpha: float, beta: float
    ) -> Tuple[float, Optional[int]]:
        best_col = None
        best_score = -math.inf

        for col in self._ordered_moves(plateau):
            if time.perf_counter() > self._deadline:
                break

            undo = plateau.jouer_coup_reversible(col, self.symbole)
            terminal = plateau.est_victoire(col)
            if terminal:
                score = 1_000_000 - (self.profondeur - depth)  # prefer faster wins
            elif plateau.est_nul():
                score = 0
            else:
                score = -self._negamax(
                    plateau,
                    depth - 1,
                    -beta,
                    -alpha,
                    self._opp_symbole,
                    self.symbole,
                )
            plateau.annuler_coup(col, undo, self.symbole)

            if score > best_score:
                best_score = score
                best_col = col
            alpha = max(alpha, score)
            if alpha >= beta:
                break

        return best_score, best_col

    def _negamax(
        self,
        plateau,
        depth: int,
        alpha: float,
        beta: float,
        to_play: str,
        other: str,
    ) -> float:
        # Time check
        if time.perf_counter() > self._deadline:
            return 0  # Neutral cutoff; root handles fallback

        # Terminal or depth cutoff
        if depth == 0 or plateau.est_nul():
            return self._evaluate(plateau, to_play, other)

        key = self._hash_state(plateau, to_play)
        if key in self._transpo:
            stored_depth, stored_val, flag = self._transpo[key]
            if stored_depth >= depth:
                if flag == 0:  # exact
                    return stored_val
                if flag == -1:  # lower bound
                    alpha = max(alpha, stored_val)
                elif flag == 1:  # upper bound
                    beta = min(beta, stored_val)
                if alpha >= beta:
                    return stored_val

        best_val = -math.inf
        for col in self._ordered_moves(plateau):
            undo = plateau.jouer_coup_reversible(col, to_play)
            win = plateau.est_victoire(col)
            if win:
                val = 1_000_000 - (self.profondeur - depth)
            elif plateau.est_nul():
                val = 0
            else:
                val = -self._negamax(plateau, depth - 1, -beta, -alpha, other, to_play)
            plateau.annuler_coup(col, undo, to_play)

            if val > best_val:
                best_val = val
            alpha = max(alpha, val)
            if alpha >= beta:
                break

        flag = 0  # exact
        if best_val <= alpha:
            flag = 1  # upper bound
        elif best_val >= beta:
            flag = -1  # lower bound
        self._transpo[key] = (depth, best_val, flag)
        return best_val

    # ------------------------------------------------------------------ #
    # Move ordering                                                      #
    # ------------------------------------------------------------------ #
    def _ordered_moves(self, plateau) -> List[int]:
        # Center-first ordering; if we have a remembered best move, prioritize it.
        center = (plateau.colonnes - 1) / 2
        moves = list(plateau.colonnes_jouables)
        moves.sort(key=lambda c: (abs(c - center), -plateau.hauteurs_colonnes[c]))
        if self._last_best_col in moves:
            moves.remove(self._last_best_col)
            moves.insert(0, self._last_best_col)
        return moves

    def _find_forcing_move(self, plateau, symbole: str) -> Optional[int]:
        for col in self._ordered_moves(plateau):
            undo = plateau.jouer_coup_reversible(col, symbole)
            if plateau.est_victoire(col):
                plateau.annuler_coup(col, undo, symbole)
                return col
            plateau.annuler_coup(col, undo, symbole)
        return None

    # ------------------------------------------------------------------ #
    # Evaluation                                                         #
    # ------------------------------------------------------------------ #
    def _evaluate(self, plateau, to_play: str, other: str) -> float:
        """
        Heuristic: weighted windows of 4, center control, and immediate threats.
        Positive favors `to_play`.
        """
        score = 0.0
        score += self._center_score(plateau, to_play, other) * 3.5
        score += self._window_score(plateau, to_play, other)
        score += self._threat_score(plateau, to_play, other) * 2.0
        return score

    def _center_score(self, plateau, to_play: str, other: str) -> float:
        center_col = plateau.colonnes // 2
        own = sum(1 for cell in plateau.grille[center_col] if cell == to_play)
        opp = sum(1 for cell in plateau.grille[center_col] if cell == other)
        return own - opp

    def _window_score(self, plateau, to_play: str, other: str) -> float:
        def window_value(count_self, count_opp, empties):
            if count_self > 0 and count_opp > 0:
                return 0  # blocked window
            if count_self == 4:
                return 50_000
            if count_self == 3 and empties == 1:
                return 200
            if count_self == 2 and empties == 2:
                return 20
            if count_opp == 4:
                return -50_000
            if count_opp == 3 and empties == 1:
                return -220
            if count_opp == 2 and empties == 2:
                return -22
            return 0

        total = 0
        lignes, cols = plateau.lignes, plateau.colonnes
        grid = plateau.grille
        heights = plateau.hauteurs_colonnes

        directions: Sequence[Tuple[int, int]] = (
            (1, 0),  # horizontal
            (0, 1),  # vertical
            (1, 1),  # diag up
            (1, -1),  # diag down
        )

        for c in range(cols):
            for r in range(lignes):
                for dc, dr in directions:
                    window_cells: List[str] = []
                    for k in range(4):
                        cc = c + dc * k
                        rr = r + dr * k
                        if 0 <= cc < cols and 0 <= rr < lignes and rr < heights[cc]:
                            window_cells.append(grid[cc][rr])
                        else:
                            window_cells.append(".")
                    count_self = sum(1 for x in window_cells if x == to_play)
                    count_opp = sum(1 for x in window_cells if x == other)
                    empties = window_cells.count(".")
                    total += window_value(count_self, count_opp, empties)
        return total

    def _threat_score(self, plateau, to_play: str, other: str) -> float:
        """
        Count immediate 3-in-a-row with an open end (single-move wins).
        """
        score = 0
        for col in plateau.colonnes_jouables:
            undo = plateau.jouer_coup_reversible(col, to_play)
            if plateau.est_victoire(col):
                score += 5_000
            plateau.annuler_coup(col, undo, to_play)

            undo = plateau.jouer_coup_reversible(col, other)
            if plateau.est_victoire(col):
                score -= 5_500  # prioritize blocking opponent threat
            plateau.annuler_coup(col, undo, other)
        return score

    # ------------------------------------------------------------------ #
    # Hashing                                                            #
    # ------------------------------------------------------------------ #
    def _hash_state(self, plateau, to_play: str) -> Tuple:
        # Deterministic, but simple (sufficient for small board).
        grid_key = tuple(tuple(col) for col in plateau.grille)
        heights_key = tuple(plateau.hauteurs_colonnes)
        return (grid_key, heights_key, to_play)
