import random
import time

from bots.bot import Bot
# Assuming 'moteur.joueur' and 'moteur.plateau' are in the Python path
# as per the provided file structure.
from moteur.joueur import Joueur

class StrategosPrime(Bot):  # Inherit from BaseBot or the tournament's Bot class
    def __init__(self, nom, symbole, profondeur=4, temps_max=0):
        super().__init__(nom, symbole)
        self.profondeur = profondeur  # Max depth for fixed search or cap for ID
        self.temps_max = temps_max  # Time limit in seconds for a move

        # State reset at the start of each trouver_coup call
        self.transposition_table = {}
        self.adversaire_symbole = None
        self.start_time = 0
        self.nodes_evaluated = 0

        # --- Tunable Parameters ---
        self.WIN_SCORE_BASE = 100000  # Base score for a guaranteed win

        # Heuristic evaluation weights
        self.EVAL_THREE_THREAT = 100  # For having 3 pieces in a window of 4 with 1 empty
        self.EVAL_OPP_THREE_THREAT_FACTOR = 1.5  # Prioritize blocking opponent's 3-threats

        self.EVAL_TWO_POTENTIAL = 10  # For having 2 pieces in a window of 4 with 2 empty
        self.EVAL_OPP_TWO_POTENTIAL_FACTOR = 1.5  # Prioritize blocking opponent's 2-potentials

        self.EVAL_CENTER_CONTROL = 5  # Bonus for each piece in a center column
        # --- End Tunable Parameters ---

    def _reset_search_state(self):
        """Resets state that should be fresh for each move decision."""
        self.transposition_table = {}
        self.nodes_evaluated = 0
        # If other state like killer moves were used, reset them here.

    def trouver_coup(self, plateau, joueur2) -> int:
        self._reset_search_state()
        self.adversaire_symbole = joueur2.symbole
        self.start_time = time.time()

        initial_ordered_cols = self._get_ordered_moves(plateau)
        if not initial_ordered_cols:
            # No playable moves, should mean game is over (draw/win already decided)
            return 0  # Fallback, though Partie should handle game end.

        # Default best move to the most central playable column initially
        best_move_overall = initial_ordered_cols[0]

        # 1. Check for immediate win for self (critical optimization)
        for col in initial_ordered_cols:
            if col not in plateau.colonnes_jouables: continue  # Should not happen with _get_ordered_moves

            # Simulate playing the move
            colonne_est_enlevee = plateau.jouer_coup_reversible(col, self.symbole)
            if plateau.est_victoire(col):
                plateau.annuler_coup(col, colonne_est_enlevee, self.symbole)
                return col  # Take the win
            plateau.annuler_coup(col, colonne_est_enlevee, self.symbole)

        # 2. Perform search (Iterative Deepening or Fixed Depth)
        if self.temps_max > 0:
            # Iterative deepening with time limit
            best_move_from_completed_iter = best_move_overall  # Start with initial guess

            for current_search_depth in range(1, self.profondeur + 1):
                if (time.time() - self.start_time) >= self.temps_max:
                    break  # Overall time limit for trouver_coup reached

                current_iter_best_score = -float('inf')
                current_iter_best_moves = []

                # Order moves: best from previous iteration first, then center-biased
                ordered_moves_for_this_iter = self._get_ordered_moves(plateau,
                                                                      best_move_previous_iter=(
                                                                          best_move_from_completed_iter if current_search_depth > 1 else None))

                time_ran_out_this_iteration = False
                for col in ordered_moves_for_this_iter:
                    if col not in plateau.colonnes_jouables: continue

                    # Check time before each potentially long negamax call
                    if (time.time() - self.start_time) >= self.temps_max:
                        time_ran_out_this_iteration = True
                        break

                    colonne_est_enlevee = plateau.jouer_coup_reversible(col, self.symbole)
                    # Score is from self.symbole's perspective
                    score = -self._negamax(plateau, current_search_depth - 1, -float('inf'), float('inf'),
                                           self.adversaire_symbole)
                    plateau.annuler_coup(col, colonne_est_enlevee, self.symbole)

                    if score > current_iter_best_score:
                        current_iter_best_score = score
                        current_iter_best_moves = [col]
                    elif score == current_iter_best_score:
                        current_iter_best_moves.append(col)

                if not time_ran_out_this_iteration and current_iter_best_moves:
                    # This iteration completed fully. Update our overall best move.
                    best_move_from_completed_iter = self._select_from_tied_moves(plateau, current_iter_best_moves)
                    # If a winning line is found by this iteration, we can trust this move and stop.
                    if current_iter_best_score >= (self.WIN_SCORE_BASE):  # Win found
                        return best_move_from_completed_iter
                elif time_ran_out_this_iteration:
                    # Iteration was cut short. Don't use its (potentially partial) results.
                    # Rely on best_move_from_completed_iter from *previous* full iteration.
                    break  # Break from depth iteration loop

            best_move_overall = best_move_from_completed_iter
        else:
            # Fixed depth search
            best_score = -float('inf')
            fixed_depth_best_moves = []

            for col in initial_ordered_cols:
                if col not in plateau.colonnes_jouables: continue

                colonne_est_enlevee = plateau.jouer_coup_reversible(col, self.symbole)
                score = -self._negamax(plateau, self.profondeur - 1, -float('inf'), float('inf'),
                                       self.adversaire_symbole)
                plateau.annuler_coup(col, colonne_est_enlevee, self.symbole)

                if score > best_score:
                    best_score = score
                    fixed_depth_best_moves = [col]
                elif score == best_score:
                    fixed_depth_best_moves.append(col)

            if fixed_depth_best_moves:
                best_move_overall = self._select_from_tied_moves(plateau, fixed_depth_best_moves)
            # else: best_move_overall remains the initial guess (e.g. first center column)

        # Final safety check for move validity (should ideally not be needed)
        if best_move_overall not in plateau.colonnes_jouables:
            print("fallback")
            playable_fallback = list(plateau.colonnes_jouables)
            return random.choice(playable_fallback) if playable_fallback else (
                initial_ordered_cols[0] if initial_ordered_cols else 0)

        return best_move_overall

    def _select_from_tied_moves(self, plateau, moves):
        """Selects a move from a list of moves with the same score, preferring central ones."""
        if not moves:  # Should not happen if called correctly
            playable = list(plateau.colonnes_jouables)
            if playable:
                center = plateau.colonnes // 2
                playable.sort(key=lambda m: abs(m - center))
                return playable[0]
            return 0  # Absolute fallback

        center = plateau.colonnes // 2
        # Sort a copy to not modify original list if it's used elsewhere, or sort in-place
        sorted_moves = sorted(moves, key=lambda m: abs(m - center))
        return sorted_moves[0]

    def _negamax(self, plateau, depth, alpha, beta, current_player_symbole):
        self.nodes_evaluated += 1

        # Time check (only if global time limit is set for the move)
        if self.temps_max > 0 and (time.time() - self.start_time) >= self.temps_max:
            return 0  # Return neutral score if time runs out during search

        # Transposition table lookup
        board_tuple = self._grille_a_tuple(plateau)
        tt_key = (board_tuple, depth, current_player_symbole)
        if tt_key in self.transposition_table:
            return self.transposition_table[tt_key]

        # Check for draw (board full, no win on previous move)
        if plateau.est_nul():
            self.transposition_table[tt_key] = 0
            return 0

        # Leaf node: if depth is 0, evaluate heuristically
        if depth == 0:
            eval_score = self._evaluate_board_for_player(plateau, current_player_symbole)
            self.transposition_table[tt_key] = eval_score
            return eval_score

        max_score = -float('inf')

        # Move ordering for internal nodes (PV move from TT, killers, then center-first)
        # For this version, using simple center-first ordering.
        ordered_moves = self._get_ordered_moves(plateau)  # No PV move passed here, simple ordering

        for col in ordered_moves:
            if col not in plateau.colonnes_jouables: continue

            colonne_est_enlevee = plateau.jouer_coup_reversible(col, current_player_symbole)

            # Check if current_player_symbole wins with this move
            if plateau.est_victoire(col):
                plateau.annuler_coup(col, colonne_est_enlevee, current_player_symbole)
                # Score is base win score + remaining depth (quicker wins are better)
                win_score = self.WIN_SCORE_BASE + depth
                self.transposition_table[tt_key] = win_score
                return win_score

            # Determine next player
            next_player_symbole = self.adversaire_symbole if current_player_symbole == self.symbole else self.symbole

            # Recursive call
            score = -self._negamax(plateau, depth - 1, -beta, -alpha, next_player_symbole)

            plateau.annuler_coup(col, colonne_est_enlevee, current_player_symbole)

            if score > max_score:
                max_score = score

            if max_score > alpha:  # Alpha stores best score found so far for current player
                alpha = max_score

            if alpha >= beta:  # Beta cutoff: opponent won't allow this path
                break

        self.transposition_table[tt_key] = max_score
        return max_score

    def _grille_a_tuple(self, plateau):
        """Creates a hashable tuple representation of the game board for TT keys."""
        # Ensures consistent representation for boards with varying column heights
        return tuple(tuple(col_data + ["."] * (plateau.lignes - len(col_data))) for col_data in plateau.grille)

    def _get_ordered_moves(self, plateau, best_move_previous_iter=None):
        """Orders playable moves: PV move first (if provided), then by centrality."""
        moves = list(plateau.colonnes_jouables)
        if not moves: return []

        center = plateau.colonnes // 2

        # Base sort: by distance to center
        moves.sort(key=lambda col_key: abs(col_key - center))

        # If a "best move from previous iteration" (PV move) is suggested and valid, prioritize it
        if best_move_previous_iter is not None and best_move_previous_iter in moves:
            moves.remove(best_move_previous_iter)
            moves.insert(0, best_move_previous_iter)

        return moves

    def _evaluate_board_for_player(self, plateau, player_symbole):
        """
        Heuristically evaluates the board from the perspective of player_symbole.
        Positive score is good for player_symbole, negative is bad.
        This is called at leaf nodes of the search (max depth or quiescent state).
        """
        opponent_symbole = self.adversaire_symbole if player_symbole == self.symbole else self.symbole
        score = 0

        # 1. Center column control
        center_col_indices = [plateau.colonnes // 2]
        if plateau.colonnes % 2 == 0:  # Even width board has two center columns
            center_col_indices.append(plateau.colonnes // 2 - 1)

        for c_idx in center_col_indices:
            # This check is mostly for safety, c_idx should be valid for standard boards
            if 0 <= c_idx < plateau.colonnes:
                for r_idx in range(plateau.hauteurs_colonnes[c_idx]):
                    if plateau.grille[c_idx][r_idx] == player_symbole:
                        score += self.EVAL_CENTER_CONTROL
                    elif plateau.grille[c_idx][r_idx] == opponent_symbole:
                        score -= self.EVAL_CENTER_CONTROL

        # 2. Evaluate potential lines (threats and potentials in windows of 4)
        # Iterate through all possible 4-cell windows on the board

        # Horizontal windows
        for r_idx in range(plateau.lignes):
            for c_idx in range(plateau.colonnes - 3):  # Max starting column for a window of 4
                window = []
                for i in range(4):  # Cells in the window
                    if r_idx < plateau.hauteurs_colonnes[c_idx + i]:  # Cell has a token
                        window.append(plateau.grille[c_idx + i][r_idx])
                    else:  # Cell is empty
                        window.append('.')
                score += self._evaluate_window(window, player_symbole, opponent_symbole)

        # Vertical windows
        for c_idx in range(plateau.colonnes):
            for r_idx in range(plateau.lignes - 3):  # Max starting row
                window = []
                for i in range(4):
                    if r_idx + i < plateau.hauteurs_colonnes[c_idx]:
                        window.append(plateau.grille[c_idx][r_idx + i])
                    else:
                        window.append('.')
                score += self._evaluate_window(window, player_symbole, opponent_symbole)

        # Positive Diagonal windows (\ slope)
        for r_idx in range(plateau.lignes - 3):
            for c_idx in range(plateau.colonnes - 3):
                window = []
                for i in range(4):
                    if r_idx + i < plateau.hauteurs_colonnes[c_idx + i]:
                        window.append(plateau.grille[c_idx + i][r_idx + i])
                    else:
                        window.append('.')
                score += self._evaluate_window(window, player_symbole, opponent_symbole)

        # Negative Diagonal windows (/ slope)
        for r_idx in range(3, plateau.lignes):  # Min starting row for this diagonal type
            for c_idx in range(plateau.colonnes - 3):
                window = []
                for i in range(4):
                    # Cell is (c_idx+i, r_idx-i)
                    if r_idx - i >= 0 and r_idx - i < plateau.hauteurs_colonnes[c_idx + i]:
                        window.append(plateau.grille[c_idx + i][r_idx - i])
                    else:
                        window.append('.')
                score += self._evaluate_window(window, player_symbole, opponent_symbole)

        return score

    def _evaluate_window(self, window, player_symbole, opponent_symbole):
        """Evaluates a single 4-cell window."""
        score = 0
        player_count = window.count(player_symbole)
        opponent_count = window.count(opponent_symbole)
        empty_count = window.count('.')  # Assuming '.' represents empty

        if player_count == 3 and empty_count == 1:  # Player has a 3-threat
            score += self.EVAL_THREE_THREAT
        elif player_count == 2 and empty_count == 2:  # Player has a 2-potential
            score += self.EVAL_TWO_POTENTIAL

        if opponent_count == 3 and empty_count == 1:  # Opponent has a 3-threat
            score -= int(self.EVAL_THREE_THREAT * self.EVAL_OPP_THREE_THREAT_FACTOR)
        elif opponent_count == 2 and empty_count == 2:  # Opponent has a 2-potential
            score -= int(self.EVAL_TWO_POTENTIAL * self.EVAL_OPP_TWO_POTENTIAL_FACTOR)

        return score