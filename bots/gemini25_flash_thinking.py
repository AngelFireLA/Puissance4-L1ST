import random
import time
import sys

# Assuming the provided classes are in a 'moteur' directory
# and this bot file is in a 'bots' directory relative to the game root.
# Adjust imports if your file structure is different.
from bots.bot import Bot
from moteur.plateau import Plateau


# Constants for the board dimensions (standard Connect4)
COLONNES = 7
LIGNES = 6

# Scoring constants for the evaluation function
# These weights determine the relative value of different board patterns.
# WIN_SCORE must be greater than any possible score from patterns.
WIN_SCORE = 1000000
SCORE_4 = WIN_SCORE # Should ideally not be reached in evaluation if win check is done first
SCORE_3 = 1000 # Value of an open 3-in-a-row
SCORE_2 = 10 # Value of an open 2-in-a-row

# Transposition Table constants
TT_EXACT = 0 # The stored score is the exact minimax value
TT_LOWER = 1 # The stored score is a lower bound (alpha cut)
TT_UPPER = 2 # The stored score is an upper bound (beta cut)

# Maximum search depth (can be adjusted)
# Deeper search is stronger but slower.
# Iterative deepening in trouver_coup can manage time.
MAX_SEARCH_DEPTH = 10 # Starting with a reasonable fixed depth

# Zobrist Hashing Table
# Used for fast board state hashing for the transposition table.
# Initialized once per bot instance.
_zobrist_table = None

def _initialize_zobrist():
    """Initializes the Zobrist table with random 64-bit integers."""
    global _zobrist_table
    if _zobrist_table is None:
        # 3 states per cell: empty (0), player 1 (1), player 2 (2)
        _zobrist_table = [[[random.getrandbits(64) for _ in range(3)]
                           for _ in range(COLONNES)]
                          for _ in range(LIGNES)]

def _get_zobrist_key(plateau: Plateau, my_symbol: str, opp_symbol: str) -> int:
    """Calculates the Zobrist hash for the current board state."""
    _initialize_zobrist()
    h = 0
    for c in range(plateau.colonnes):
        for r in range(plateau.hauteurs_colonnes[c]):
            token = plateau.grille[c][r]
            state = 0 # empty is not stored in grille, only tokens
            if token == my_symbol:
                state = 1
            elif token == opp_symbol:
                state = 2
            # Only XOR if the cell is not empty (empty cells below height are implicit)
            if state != 0:
                 h ^= _zobrist_table[r][c][state]

    # Note: Zobrist hashing for Connect4 often includes the current player's turn
    # in the hash, but since the TT is cleared per move and the player is
    # implicit in the search depth/negamax structure, we omit it for simplicity.
    return h

def _update_zobrist_key(current_hash: int, r: int, c: int, old_state: int, new_state: int) -> int:
    """Updates the Zobrist hash incrementally after a move or undo."""
    global _zobrist_table
    # XOR out the old state
    h = current_hash ^ _zobrist_table[r][c][old_state]
    # XOR in the new state
    h ^= _zobrist_table[r][c][new_state]
    return h

def _get_state_index(symbol: str, my_symbol: str, opp_symbol: str) -> int:
    """Maps a symbol to its Zobrist state index."""
    if symbol == my_symbol:
        return 1
    elif symbol == opp_symbol:
        return 2
    return 0 # Should not happen for tokens in grille

def _check_win_at_pos(plateau: Plateau, r: int, c: int, symbol: str, opponent_symbol: str) -> bool:
    """
    Checks if placing 'symbol' at (r, c) would create a win.
    Assumes the token is *not* actually placed on the board yet.
    This is used for hypothetical checks in evaluation/ordering.
    """
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)] # Horizontal, Vertical, Diag \, Diag /

    for dr, dc in directions:
        # Check segments of 4 cells that include (r, c)
        # A segment is defined by its starting cell (sr, sc) and direction (dr, dc)
        # The hypothetical cell (r, c) can be the 0th, 1st, 2nd, or 3rd cell in the segment.
        for i in range(4): # i is the index of (r, c) within the 4-cell segment
            sr, sc = r - i * dr, c - i * dc # Starting cell of the segment

            # Check if the segment starting at (sr, sc) in direction (dr, dc) is valid
            # and contains (r, c) at index i.
            # The segment cells are (sr + j*dr, sc + j*dc) for j in [0, 1, 2, 3].
            # We need to check if (r, c) == (sr + i*dr, sc + i*dc) which is true by definition of sr, sc.
            # We also need to check if all cells in the segment are within bounds.
            is_valid_segment = True
            segment_tokens = []
            for j in range(4):
                curr_r, curr_c = sr + j * dr, sc + j * dc

                # Check bounds
                if not (0 <= curr_r < plateau.lignes and 0 <= curr_c < plateau.colonnes):
                    is_valid_segment = False
                    break

                # Get the token at (curr_r, curr_c)
                if curr_c < 0 or curr_c >= plateau.colonnes: # Safety check
                     is_valid_segment = False; break
                if curr_r < 0 or curr_r >= plateau.lignes: # Safety check
                     is_valid_segment = False; break

                if curr_r < plateau.hauteurs_colonnes[curr_c]:
                    # Cell is filled
                    segment_tokens.append(plateau.grille[curr_c][curr_r])
                elif curr_r == r and curr_c == c:
                    # This is the hypothetical spot
                    segment_tokens.append(symbol)
                else:
                    # This is an empty spot above the current height, or a different hypothetical spot
                    # For win check, we only care if it's empty or has the target symbol
                    # If it's empty, it doesn't break the potential line yet.
                    segment_tokens.append(".") # Represent empty

            if not is_valid_segment:
                continue

            # Check if this segment contains 4 of the target symbol and no opponent symbols
            if segment_tokens.count(symbol) == 4 and opponent_symbol not in segment_tokens:
                return True # Found a winning line through (r, c)

    return False

def _count_open_segments(plateau: Plateau, my_symbol: str, opp_symbol: str) -> int:
    """
    Evaluates the board by counting 'open' segments of 2, 3, and 4 tokens.
    An 'open' segment is a 4-cell line containing only tokens of one player
    and empty cells, where all empty cells are at or above the current
    height of their respective columns (i.e., they are potentially playable).
    """
    score = 0
    # Directions to check: Horizontal, Vertical, Diagonal (\), Diagonal (/)
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

    for r in range(plateau.lignes):
        for c in range(plateau.colonnes):
            # Check segments starting at (r, c) in each direction
            for dr, dc in directions:
                # Only check horizontal and diagonal starting points once
                if dr == 0 and dc == 1 and c > plateau.colonnes - 4: continue # Horizontal
                if dr == 1 and dc == 0 and r > plateau.lignes - 4: continue # Vertical
                if dr == 1 and dc == 1 and (r > plateau.lignes - 4 or c > plateau.colonnes - 4): continue # Diag \
                if dr == 1 and dc == -1 and (r > plateau.lignes - 4 or c < 3): continue # Diag /

                # Check the 4 cells in the segment starting at (r, c)
                my_tokens = 0
                opp_tokens = 0
                empty_cells = 0
                segment_is_valid = True # Check if segment is within bounds and doesn't contain mixed tokens

                for i in range(4):
                    curr_r, curr_c = r + i * dr, c + i * dc

                    # Check bounds
                    if not (0 <= curr_r < plateau.lignes and 0 <= curr_c < plateau.colonnes):
                        segment_is_valid = False
                        break # Segment goes out of bounds

                    # Get the token at (curr_r, curr_c)
                    if curr_r < plateau.hauteurs_colonnes[curr_c]:
                        # Cell is filled
                        token = plateau.grille[curr_c][curr_r]
                        if token == my_symbol:
                            my_tokens += 1
                        elif token == opp_symbol:
                            opp_tokens += 1
                        else:
                             # Should not happen in a valid game state
                             segment_is_valid = False
                             break
                    else:
                        # Cell is empty (at or above current height)
                        empty_cells += 1

                # A segment is 'open' and contributes to score if it's valid,
                # contains only one player's tokens (or empty), and has at least one token.
                if not segment_is_valid or (my_tokens > 0 and opp_tokens > 0) or (my_tokens == 0 and opp_tokens == 0):
                    continue # Invalid segment, mixed tokens, or all empty

                # Evaluate the open segment based on tokens
                if my_tokens > 0: # Segment contains my tokens (and possibly empty)
                    if opp_tokens == 0: # Ensure no opponent tokens
                        if my_tokens == 4:
                            score += SCORE_4 # Should be caught by win check, but high value
                        elif my_tokens == 3 and empty_cells == 1:
                            score += SCORE_3
                        elif my_tokens == 2 and empty_cells == 2:
                            score += SCORE_2
                        # Add more weights if needed (e.g., 1 token + 3 empty)
                        # elif my_tokens == 1 and empty_cells == 3:
                        #     score += SCORE_1 # Define SCORE_1 if used

                elif opp_tokens > 0: # Segment contains opponent tokens (and possibly empty)
                     if my_tokens == 0: # Ensure no my tokens
                        if opp_tokens == 4:
                            score -= SCORE_4
                        elif opp_tokens == 3 and empty_cells == 1:
                            score -= SCORE_3
                        elif opp_tokens == 2 and empty_cells == 2:
                            score -= SCORE_2
                        # elif opp_tokens == 1 and empty_cells == 3:
                        #     score -= SCORE_1 # Define SCORE_1 if used


    return score


class BetaBot(Bot):
    """
    A Connect4 bot using Negamax search with Alpha-Beta pruning,
    Transposition Table (Zobrist Hashing), and a pattern-based evaluation function.
    """
    def __init__(self, nom, symbole, profondeur=MAX_SEARCH_DEPTH):
        """
        Initializes the AlphaConnectBot.

        Args:
            nom (str): The name of the bot.
            symbole (str): The token symbol for the bot ('X' or 'O').
            profondeur (int): The maximum search depth for Negamax.
        """
        super().__init__(nom, symbole)
        self.profondeur = profondeur
        self._my_symbol = symbole
        self._opp_symbol = 'O' if symbole == 'X' else 'X'

        # Transposition table: maps Zobrist hash to (score, depth, node_type)
        # Cleared at the start of each trouver_coup call to ensure statelessness.
        self.transposition_table = {}

        # Zobrist hashing setup
        _initialize_zobrist() # Ensure the global table is initialized
        self._current_hash = 0 # Will be calculated at the start of trouver_coup

        # Store board dimensions (assuming standard 7x6, but good practice)
        self.colonnes = COLONNES
        self.lignes = LIGNES

        # Store the last move made to check for wins in Negamax base case
        # This needs to be managed carefully within the recursive calls.
        # The root call doesn't have a 'last_col' from its perspective.
        # The recursive calls will pass the column they just played.
        # Let's handle this by passing last_col in the negamax signature.


    def trouver_coup(self, plateau: Plateau, joueur2: Bot) -> int:
        """
        Finds the best move for the current board state.

        Args:
            plateau (Plateau): The current game board state.
            joueur2 (Bot): The opponent's bot instance (used to get their symbol).

        Returns:
            int: The chosen column number (0-indexed).
        """
        # Ensure statelessness: Clear the transposition table for this new move search.
        self.transposition_table = {}

        # Calculate the initial Zobrist hash for the current board state.
        self._current_hash = _get_zobrist_key(plateau, self._my_symbol, self._opp_symbol)

        # Get playable columns
        playable_cols = list(plateau.colonnes_jouables)

        # --- Immediate Win/Block Check ---
        # Prioritize moves that win immediately or block opponent's immediate win.
        for col in playable_cols:
            row = plateau.hauteurs_colonnes[col] # Row where token would land

            # Check if playing here wins for me
            # Pass my symbol and opponent's symbol
            if _check_win_at_pos(plateau, row, col, self._my_symbol, self._opp_symbol):
                 return col # Found an immediate winning move

        # Check if opponent has an immediate winning move and block it
        for col in playable_cols:
            row = plateau.hauteurs_colonnes[col] # Row where token would land

            # Check if playing here blocks opponent's win
            # Pass opponent's symbol and my symbol (as opponent's opponent)
            if _check_win_at_pos(plateau, row, col, self._opp_symbol, self._my_symbol):
                 return col # Found an immediate losing move for opponent, block it

        # --- Negamax Search ---
        # If no immediate win or block, perform Negamax search.
        best_score = -float('inf')
        best_moves = []

        # Order moves: Center columns first is a good heuristic
        ordered_cols = sorted(playable_cols, key=lambda col: abs(col - self.colonnes // 2))

        # Iterative Deepening (Optional, using fixed depth for now)
        # for depth in range(1, self.profondeur + 1):
        #     # Perform search for current depth...
        #     # If time allows, continue to next depth.
        #     # Store best move found so far.
        #     pass # Skipping iterative deepening for simplicity with fixed depth

        # Perform search at the maximum configured depth
        current_depth = self.profondeur

        # Alpha-beta pruning bounds for the root node
        alpha = -float('inf')
        beta = float('inf')

        # Store scores for move ordering at the root (optional, mainly for iterative deepening)
        # move_scores = {}

        for col in ordered_cols:
            # Make the move temporarily
            row = plateau.hauteurs_colonnes[col] # Row where token will land
            col_removed = plateau.jouer_coup_reversible(col, self._my_symbol)

            # Update Zobrist hash incrementally
            state_after = _get_state_index(self._my_symbol, self._my_symbol, self._opp_symbol)
            # The cell was empty (state 0) before the move
            new_hash = _update_zobrist_key(self._current_hash, row, col, 0, state_after)

            # Call negamax for the next player (opponent)
            # The score is negated because it's from the opponent's perspective
            # Pass the column just played (col) as last_col
            score = -self._negamax(plateau, current_depth - 1, -beta, -alpha, self._opp_symbol, col, new_hash)

            # Undo Zobrist hash update (restore hash to state before this move)
            # XOR out the new state, XOR in the old state (empty)
            # Note: We need to use the hash *before* the move for the TT lookup/store
            # associated with the state *before* the move.
            # The hash passed to the recursive call is the hash *after* the move.
            # The hash used for TT lookup/store *within* the recursive call is the one passed to it.
            # The hash used for TT lookup/store *after* the recursive call returns
            # (at the current level) should be the hash *before* the move was made at this level.
            # Let's revert the hash *after* the recursive call returns and before undoing the move.
            self._current_hash = _update_zobrist_key(new_hash, row, col, state_after, 0)


            # Undo the move
            plateau.annuler_coup(col, col_removed, self._my_symbol)

            # Update best score and moves
            if score > best_score:
                best_score = score
                best_moves = [col]
            elif score == best_score:
                best_moves.append(col)

            # Update alpha for the root node
            alpha = max(alpha, score)

            # Store score for potential future use (e.g., iterative deepening move ordering)
            # move_scores[col] = score

            # Alpha-beta pruning at the root (optional but can save time if a move is clearly bad)
            # if alpha >= beta:
            #     break # Pruning at root is less common as you want to evaluate all root moves

        # If no moves were found (shouldn't happen in a non-full board), default to center
        if not best_moves:
             # This case should ideally not be reached if playable_cols is not empty
             # and the search is performed. But as a fallback:
             if playable_cols:
                 return playable_cols[len(playable_cols) // 2]
             else:
                 return 0 # Board is full or error state

        # Select a move from the best moves.
        # Prioritize center columns among equally good moves.
        # Sort best moves by distance to center.
        best_moves.sort(key=lambda col: abs(col - self.colonnes // 2))

        # Return the best move closest to the center
        return best_moves[0]


    def _negamax(self, plateau: Plateau, depth: int, alpha: float, beta: float, current_symbol: str, last_col: int, current_hash: int) -> float:
        """
        Recursive Negamax search function with Alpha-Beta pruning and Transposition Table.

        Args:
            plateau (Plateau): The current board state (modified temporarily during search).
            depth (int): The remaining search depth.
            alpha (float): The alpha bound for pruning.
            beta (float): The beta bound for pruning.
            current_symbol (str): The symbol of the player whose turn it is in this node.
            last_col (int): The column where the previous player placed their token.
                            Used to check for wins in the base case. None for the root call.
            current_hash (int): The Zobrist hash of the current board state *before* the current player's move.

        Returns:
            float: The score of the position from the perspective of the current_symbol player.
        """
        # --- Transposition Table Lookup ---
        # Check if this state is already in the transposition table
        tt_entry = self.transposition_table.get(current_hash)
        if tt_entry is not None:
            tt_score, tt_depth, tt_type = tt_entry
            # If the stored entry is from a search of sufficient depth
            if tt_depth >= depth:
                # Adjust score based on node type and bounds
                if tt_type == TT_EXACT:
                    return tt_score
                elif tt_type == TT_LOWER:
                    alpha = max(alpha, tt_score)
                elif tt_type == TT_UPPER:
                    beta = min(beta, tt_score)

                # If the bounds cross, we can prune
                if alpha >= beta:
                    return tt_score # Return the score that caused the cutoff

        # --- Base Cases ---
        # 1. Check for win (the player who just moved wins)
        # The player who just moved is the opponent of current_symbol
        # last_col is the column where the winning token was placed.
        if last_col is not None and plateau.est_victoire(last_col):
            # The previous player (opponent of current_symbol) won.
            # This is a loss for the current_symbol player.
            # Score is negative infinity, adjusted by depth (prefer losing later).
            # Add depth to the score so that wins found higher up the tree (closer to root)
            # are preferred (or losses are less bad).
            # WIN_SCORE + depth ensures wins at depth 0 are better than wins at depth 1 etc.
            # From current_symbol's perspective, this is a loss: -(WIN_SCORE + depth)
            score = -(WIN_SCORE + depth)
            # Store in TT as an exact score (terminal node)
            self.transposition_table[current_hash] = (score, depth, TT_EXACT)
            return score

        # 2. Check for draw
        if plateau.est_nul():
            # Draw state, score is 0
            self.transposition_table[current_hash] = (0, depth, TT_EXACT)
            return 0

        # 3. Depth limit reached
        if depth == 0:
            # Evaluate the position from the perspective of current_symbol
            score = _count_open_segments(plateau, current_symbol, self._autre_symbole(current_symbol))
            # Store in TT as an exact score (evaluation is considered exact at depth 0)
            self.transposition_table[current_hash] = (score, depth, TT_EXACT)
            return score

        # --- Recursive Step ---
        max_score = -float('inf')
        playable_cols = list(plateau.colonnes_jouables)

        # If no playable columns, it's a draw (already handled by est_nul, but defensive)
        if not playable_cols:
             self.transposition_table[current_hash] = (0, depth, TT_EXACT)
             return 0

        # Move Ordering: Center columns first heuristic
        # For deeper search, ordering based on shallow evaluation or TT move hint is better.
        # Using simple center ordering for now.
        ordered_cols = sorted(playable_cols, key=lambda col: abs(col - self.colonnes // 2))

        # Store the best move found at this node for TT (optional, but helps ordering)
        # best_move_at_node = None # Not strictly needed for TT store type

        # Store the original alpha value for TT storage
        original_alpha = alpha

        for col in ordered_cols:
            # Make the move temporarily
            row = plateau.hauteurs_colonnes[col] # Row where token will land
            col_removed = plateau.jouer_coup_reversible(col, current_symbol)

            # Calculate the hash *after* making the move
            state_after = _get_state_index(current_symbol, self._my_symbol, self._opp_symbol)
            # The cell was empty (state 0) before the move
            hash_after_move = _update_zobrist_key(current_hash, row, col, 0, state_after)

            # Recursive call for the next player (opponent)
            # Pass the hash *after* the move just made
            score = -self._negamax(plateau, depth - 1, -beta, -alpha, self._autre_symbole(current_symbol), col, hash_after_move)

            # Undo the move
            plateau.annuler_coup(col, col_removed, current_symbol)

            # Update max_score
            if score > max_score:
                max_score = score
                # best_move_at_node = col # Store the move that resulted in the best score

            # Alpha-Beta Pruning
            alpha = max(alpha, max_score)
            if alpha >= beta:
                # Beta cutoff: The opponent will avoid this line of play.
                # The score is a lower bound (alpha) from the current player's perspective.
                # Store in TT as a lower bound.
                # Use the hash *before* the move for the TT entry for this node.
                self.transposition_table[current_hash] = (max_score, depth, TT_LOWER)
                return max_score # Prune this branch

        # --- Transposition Table Store ---
        # If no cutoff occurred, the score is the exact value if max_score > original_alpha,
        # otherwise it's an upper bound (beta failed high).
        # Use the hash *before* the move for the TT entry for this node.
        tt_type = TT_EXACT if max_score >= original_alpha else TT_UPPER
        self.transposition_table[current_hash] = (max_score, depth, tt_type)

        return max_score

    def _autre_symbole(self, symbole: str) -> str:
        """Returns the opponent's symbol."""
        return 'O' if symbole == 'X' else 'X'