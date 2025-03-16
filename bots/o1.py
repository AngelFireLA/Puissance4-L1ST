import math
import random
import time
from bots.bot import Bot

class GrandMasterBot(Bot):
    """
    A powerful Connect4 bot using an advanced Negamax (Alpha-Beta) search with
    a custom evaluation function and basic move ordering. Each call to 'trouver_coup'
    is independent, resetting transposition tables and other state to avoid
    cross-call contamination.
    """
    def __init__(self, nom, symbole, profondeur=8):
        """
        :param nom: Bot name.
        :param symbole: 'X' or 'O' for the bot.
        :param profondeur: Maximum search depth for Negamax/Alpha-Beta.
        """
        super().__init__(nom, symbole)
        self.profondeur = profondeur

    def trouver_coup(self, plateau, joueur2):
        """
        Determines and returns the column where this bot will play.
        :param plateau: The current game state (Plateau).
        :param joueur2: The opposing player's object (use joueur2.symbole for their token).
        :return: Integer column index where to place the piece.
        """
        # --------------------------------------------------------------
        # 1) Fast checks for immediate wins or blocks
        # --------------------------------------------------------------
        # Attempt a winning move if available
        for col in self._order_moves(plateau):
            if self._is_winning_move(plateau, col, self.symbole):
                return col

        # Attempt to block opponent's winning move if needed
        adv_symb = joueur2.symbole
        for col in self._order_moves(plateau):
            if self._is_winning_move(plateau, col, adv_symb):
                return col

        # --------------------------------------------------------------
        # 2) Perform a deeper search (Negamax w/ alpha-beta)
        # --------------------------------------------------------------
        self.transpo = {}  # Fresh transposition table each call
        best_score = -math.inf
        best_cols = []
        alpha, beta = -math.inf, math.inf
        depth = self.profondeur

        # Move ordering: center columns first
        for col in self._order_moves(plateau):
            col_removed = plateau.jouer_coup_reversible(col, self.symbole)
            if plateau.est_victoire(col):
                # Immediate winning move (just in case we missed above)
                plateau.annuler_coup(col, col_removed, self.symbole)
                return col

            # Negamax: next player is the opponent
            score = -self._negamax(
                plateau, depth - 1, -beta, -alpha, self._autre_symbole(self.symbole)
            )

            plateau.annuler_coup(col, col_removed, self.symbole)

            # Track best score
            if score > best_score:
                best_score = score
                best_cols = [col]
            elif abs(score - best_score) < 1e-9:
                best_cols.append(col)

            if score > alpha:
                alpha = score
            if alpha >= beta:
                break  # alpha-beta cutoff

        if not best_cols:
            # In theory, should never happen, but fallback
            return random.choice(list(plateau.colonnes_jouables))

        # --------------------------------------------------------------
        # 3) Final choice among best moves
        #    We slightly weight moves toward the center of the board.
        # --------------------------------------------------------------
        center_col = plateau.colonnes // 2
        # We want columns near the center to have higher weight
        # so the bot doesn't always pick leftmost from the best set.
        weights = [1 + (3 - abs(c - center_col)) for c in best_cols]
        return random.choices(best_cols, weights=weights, k=1)[0]

    # ----------------------------------------------------------------------
    #  INTERNAL FUNCTIONS
    # ----------------------------------------------------------------------

    def _negamax(self, plateau, profondeur, alpha, beta, symbole):
        """
        Negamax search with alpha-beta pruning.
        :param plateau: Game state.
        :param profondeur: Remaining search depth.
        :param alpha: Current alpha cutoff.
        :param beta: Current beta cutoff.
        :param symbole: Symbol of the current player in this search state.
        :return: Score (float).
        """
        # Check for draw or depth limit
        if profondeur == 0 or plateau.est_nul():
            return self._eval(plateau)

        # Transposition table check
        hash_key = (self._grille_to_tuple(plateau), profondeur, symbole)
        if hash_key in self.transpo:
            return self.transpo[hash_key]

        max_score = -math.inf
        for col in self._order_moves(plateau):
            col_removed = plateau.jouer_coup_reversible(col, symbole)
            if plateau.est_victoire(col):
                # A direct win at this depth gets a big bonus
                plateau.annuler_coup(col, col_removed, symbole)
                # Keep a small depth factor so quick wins are valued higher
                score = 100000.0 + profondeur
                self.transpo[hash_key] = score
                return score

            # Negamax recursion
            suivant = self._autre_symbole(symbole)
            score = -self._negamax(plateau, profondeur - 1, -beta, -alpha, suivant)

            plateau.annuler_coup(col, col_removed, symbole)

            if score > max_score:
                max_score = score
            if max_score > alpha:
                alpha = max_score
            if alpha >= beta:
                break  # alpha-beta cutoff

        self.transpo[hash_key] = max_score
        return max_score

    def _eval(self, plateau):
        """
        Board evaluation heuristic:
          - Simple but effective count of potential 4-in-a-rows,
            with weighting for center columns.
        """
        score = 0
        # Basic idea:
        #   + Count lines-of-2 and lines-of-3 for self
        #   - Count lines-of-2 and lines-of-3 for opponent
        #   + Small preference for center columns
        me = self.symbole
        opp = self._autre_symbole(me)

        # Quick center preference
        center_col = plateau.colonnes // 2
        for c in range(plateau.colonnes):
            # Add small center bonus
            center_bonus = max(0, 3 - abs(c - center_col))
            score += center_bonus * self._column_factor(plateau, c, me)

        # Evaluate partial lines
        # (User can expand or refine for more nuanced heuristics)
        score += self._count_alignments(plateau, me, length=2) * 3
        score += self._count_alignments(plateau, me, length=3) * 10
        score -= self._count_alignments(plateau, opp, length=2) * 3
        score -= self._count_alignments(plateau, opp, length=3) * 10
        return score

    def _column_factor(self, plateau, col, symbole):
        """
        Simple measure of how favorable a column is based on
        pieces in it belonging to 'symbole'.
        """
        col_height = plateau.hauteurs_colonnes[col]
        total_pieces = col_height
        if total_pieces == 0:
            return 0
        same = sum(1 for x in plateau.grille[col] if x == symbole)
        return same

    def _count_alignments(self, plateau, symbole, length=2):
        """
        Counts how many lines of exactly 'length' consecutive
        'symbole' appear in the entire board's 2D layout
        (vertical, horizontal, diagonal).
        """
        count = 0
        nb_cols, nb_rows = plateau.colonnes, plateau.lignes
        # Convert columns-of-lists -> 2D array-like
        # col c => x, row r => y
        # plateau.grille[c][r] => symbol
        grid = [["." for _ in range(nb_rows)] for _ in range(nb_cols)]
        for c in range(nb_cols):
            for r, val in enumerate(plateau.grille[c]):
                grid[c][r] = val

        for c in range(nb_cols):
            for r in range(nb_rows):
                if grid[c][r] == symbole:
                    # Horizontal
                    if c + length - 1 < nb_cols:
                        if all(grid[c + k][r] == symbole for k in range(length)):
                            count += 1
                    # Vertical
                    if r + length - 1 < nb_rows:
                        if all(grid[c][r + k] == symbole for k in range(length)):
                            count += 1
                    # Diagonal up-right
                    if c + length - 1 < nb_cols and r + length - 1 < nb_rows:
                        if all(grid[c + k][r + k] == symbole for k in range(length)):
                            count += 1
                    # Diagonal down-right
                    if c + length - 1 < nb_cols and r - (length - 1) >= 0:
                        if all(grid[c + k][r - k] == symbole for k in range(length)):
                            count += 1
        return count

    def _autre_symbole(self, s):
        return 'O' if s == 'X' else 'X'

    def _is_winning_move(self, plateau, col, symbole):
        """
        Check if playing 'col' with 'symbole' is an immediate winning move.
        """
        if col not in plateau.colonnes_jouables:
            return False
        col_removed = plateau.jouer_coup_reversible(col, symbole)
        is_win = plateau.est_victoire(col)
        plateau.annuler_coup(col, col_removed, symbole)
        return is_win

    def _order_moves(self, plateau):
        """
        Returns a list of playable columns, sorted so that
        columns near the center come first. This helps
        the search converge faster toward promising moves.
        """
        center = plateau.colonnes // 2
        return sorted(list(plateau.colonnes_jouables), key=lambda c: abs(c - center))

    def _grille_to_tuple(self, plateau):
        """
        Creates a hashable representation of the board
        for transposition-table usage.
        """
        # We'll create a tuple of tuples, each column
        # padded with "." up to 'lignes'.
        return tuple(
            tuple(col + ["."] * (plateau.lignes - len(col))) for col in plateau.grille
        )
