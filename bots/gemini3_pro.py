import time
import random
from .bot import Bot


class ChronosBot(Bot):
    """
    ChronosBot: A high-performance Connect 4 AI utilizing bitboards,
    iterative deepening, transposition tables, and Alpha-Beta pruning.

    The 'Chronos' name reflects its ability to manage computational time
    and foresee future outcomes through deep search.
    """

    def __init__(self, nom, symbole, profondeur=8, temps_max=0):
        super().__init__(nom, symbole)
        self.profondeur = profondeur
        self.temps_max = temps_max

        # Transposition Table: {key: (score, flag, depth)}
        # We use a large dictionary. Python dicts are highly optimized.
        self.transposition_table = {}
        self.nodes_explored = 0
        self.start_time = 0

        # Precomputed column order (Center-out) for move ordering
        self.column_order = [3, 2, 4, 1, 5, 0, 6]

    def trouver_coup(self, plateau, joueur2) -> int:
        """
        Main entry point.
        1. Converts the Plateau object to efficient Bitboards.
        2. Runs Iterative Deepening Negamax.
        3. Returns the best column.
        """
        self.nodes_explored = 0
        self.start_time = time.perf_counter()

        # --- 1. Efficient State Conversion (Object -> Bitboard) ---
        # Connect 4 fits into 64-bits (7 cols * 7 height-with-buffer).
        # We use a sentinel row at the top of each column to avoid wrapping.
        # Bit layout: 0-5 (Col 0), 6 (Sentinel), 7-12 (Col 1), etc.

        position = 0  # Bitmap for 'self' (current player)
        mask = 0  # Bitmap for all occupied cells

        # We iterate columns then rows to build the bitmasks
        # This is the only slow part (Python loop), but done once per move.
        for c in range(7):
            top = plateau.hauteurs_colonnes[c]
            for r in range(top):
                # Standard layout: cell index = c * 7 + r
                shift = c * 7 + r
                mask |= (1 << shift)
                if plateau.grille[c][r] == self.symbole:
                    position |= (1 << shift)

        # --- 2. Iterative Deepening Search ---
        best_move = 3  # Default to center if panic
        possible_moves = self.get_valid_moves(mask)
        if not possible_moves:
            return 0  # Should not happen if game not over

        # If only one move is possible, don't search
        if len(possible_moves) == 1:
            return possible_moves[0]

        # Reset TT for new search or keep it?
        # Keeping it is better for performance, but we must ensure keys are unique.
        # We'll clear it if it gets too big to prevent memory bloat, otherwise keep.
        if len(self.transposition_table) > 2_000_000:
            self.transposition_table.clear()

        # Time management
        limit_time = self.temps_max if self.temps_max > 0 else 100.0

        # Search range
        min_depth = 1
        max_depth = 42  # Max moves in Connect 4
        if self.temps_max <= 0 and self.profondeur > 0:
            # Fixed depth mode
            min_depth = self.profondeur
            max_depth = self.profondeur
            limit_time = 99999.0

        alpha = -1000000
        beta = 1000000

        for depth in range(min_depth, max_depth + 1):

            score = self.negamax(position, mask, depth, alpha, beta)

            # Extract best move from TT or logic?
            # Negamax returns score, but we need the move.
            # We usually handle the root specifically to get the move.
            # To save complexity, we'll actually run the Root Search loop here.

            # --- Root Search Loop for current depth ---
            best_score = -10000000
            current_best_move = -1

            # Sort moves: prioritize the one found in previous iteration (if any)
            # or simply center-out.
            sorted_moves = [m for m in self.column_order if m in possible_moves]
            if current_best_move != -1 and current_best_move in sorted_moves:
                sorted_moves.remove(current_best_move)
                sorted_moves.insert(0, current_best_move)

            for col in sorted_moves:
                # Make move
                new_pos = position ^ mask  # Switch turn: opponents pos becomes my new pos (after update)
                new_mask = mask | (mask + (1 << (col * 7)))  # Only works if column not full

                # Check immediate win? No, negamax handles it.
                # But we must invert logic: -negamax(...)

                # Careful: 'position' is US. 'new_pos' is OPPONENT.
                # We need to pass the updated board.
                # The move we just made is for US.
                # Bitboard update for current player:
                # 1. Identify move bit: (mask + (1 << (col*7))) ^ mask
                move_bit = (mask + (1 << (col * 7))) ^ mask
                child_position = position | move_bit  # We placed a piece
                child_mask = mask | move_bit

                # Now pass to negamax. Negamax view is from the OTHER player.
                # So we pass 'position' as the OTHER player (which is 'position ^ mask' before move,
                # but simplified: input to negamax is (P_current, Mask).
                # Next state: P_next = P_current_opponent = (position ^ mask)
                # Mask_next = child_mask

                val = -self.negamax(position ^ mask, child_mask, depth - 1, -beta, -alpha)

                if val > best_score:
                    best_score = val
                    current_best_move = col

                alpha = max(alpha, val)

                # Time Check inside root loop
                if self.temps_max > 0 and (time.perf_counter() - self.start_time) > self.temps_max:
                    break

            # Update best move found at this full depth completion
            if (self.temps_max <= 0) or (time.perf_counter() - self.start_time <= self.temps_max):
                best_move = current_best_move
                # print(f"Depth {depth} done. Best: {best_move} Score: {best_score} Nodes: {self.nodes_explored}")
            else:
                # print(f"Depth {depth} interrupted.")
                break

            # If we found a winning mate, stop searching deeper
            if best_score > 900000:  # Winning score threshold
                break
            if best_score < -900000:  # Losing no matter what
                break

        return best_move

    def negamax(self, position, mask, depth, alpha, beta):
        self.nodes_explored += 1

        # Check Trivial Win (Last move made by opponent caused a win?)
        # NOTE: In Negamax, we check if the PREVIOUS player won.
        # But efficiently, we check if 'position' (current player) creates a win?
        # No, usually checking if opponent won is done before calling or at start.
        # Optimized Bitboard approach:
        # We just entered this state. The LAST move was made by the opponent.
        # Opponent's stones are: position ^ mask.
        # Let's check if Opponent has 4-in-a-row.
        # Actually, simpler: We check for alignment of the player who just moved *before* recursing.
        # But to keep structure clean:

        # Helper: Check unique key for TT
        key = mask + position  # Simple hash key for Bitboards

        # TT Lookup
        if key in self.transposition_table:
            res_score, res_flag, res_depth = self.transposition_table[key]
            if res_depth >= depth:
                if res_flag == 0:  # Exact
                    return res_score
                elif res_flag == 1:  # Lowerbound (Alpha)
                    alpha = max(alpha, res_score)
                elif res_flag == 2:  # Upperbound (Beta)
                    beta = min(beta, res_score)
                if alpha >= beta:
                    return res_score

        # Check Draw (Board full)
        if mask & 0x1FFFFFFFFFFFF == 0x1FFFFFFFFFFFF:  # All valid cells filled
            return 0

        # Heuristic / Terminal at Max Depth
        if depth == 0:
            return self.evaluate_position(position, mask)

        # Move Generation
        # Possible moves are columns where the top bit is not set
        # Bitboard trick: (mask + bottom_row_mask) & valid_board_mask
        # Logic: We try to drop a piece in every column.

        # Iterate cols center-out
        best_val = -1000000000

        # To avoid generating moves for full columns, we check top row bits.
        # Top row bits for cols 0..6: 5, 12, 19, 26, 33, 40, 47
        top_mask = 0b1000000_1000000_1000000_1000000_1000000_1000000_1000000

        valid_cols = []
        for col in self.column_order:
            # Check if column is full
            # (mask >> (col * 7 + 5)) & 1  -- Checks the 6th row (index 5)
            # Actually simplest is: if (mask & (1 << (col*7 + 5))) == 0
            if (mask & (1 << (col * 7 + 5))) == 0:
                valid_cols.append(col)

        for col in valid_cols:
            # Execute Move
            # Find the first 0 bit in the column
            # In bitboards: move_bit = (mask + (1 << (col*7))) ^ mask is WRONG if col empty?
            # Standard formula: move_bit = (mask + bottom_mask_col) & column_mask
            # Simplified: Since we have a sentinel, `move_bit = (mask + (1<<(col*7))) & (1<<(col*7 + 6) - 1)` isn't quite right.
            # Easiest Python way without complex lookups:
            # The lowest 0 bit in the column 'col'.
            # We know the column shift is col*7.
            # We can compute move_bit by (mask >> (col*7)) ...
            # Actually, standard fast way:
            move_bit = (mask + (1 << (col * 7))) & (0x3F << (col * 7))  # 0x3F is 111111 binary

            if move_bit == 0: continue  # Should be covered by valid_cols check, but safety

            new_position = position | move_bit
            new_mask = mask | move_bit

            # Check Win *immediately* after move to prune.
            # This is the "Current Player Wins" check.
            if self.check_win(new_position):
                # If we make this move and win, the score is huge.
                # Score decay by depth to prefer faster wins.
                val = 1000000 - (self.profondeur - depth)
                # Note: We prefer shorter wins, so higher score for larger remaining depth?
                # Actually standard is: Score - moves_played.
                # Here: 1000000 + depth (deeper depth = faster win in recursive context)
                best_val = 1000000 + depth
                alpha = max(alpha, best_val)
                # Store exact
                self.transposition_table[key] = (best_val, 0, depth)
                return best_val

            # Recurse
            # Swap roles: passed 'position' is opponent's position in next node.
            # Opponent is (position ^ mask) currently.
            # Next node Opponent is ME (new_position).
            # Next node Mask is new_mask.
            # Arg 1 to negamax is "Current Player" for that node.
            # That is (position ^ mask) [my opponent].
            val = -self.negamax(position ^ mask, new_mask, depth - 1, -beta, -alpha)

            if val > best_val:
                best_val = val

            alpha = max(alpha, val)
            if alpha >= beta:
                break  # Cutoff

        # Store in TT
        flag = 0
        if best_val <= alpha:
            flag = 2  # Upper bound ? No, standard definition varies.
        elif best_val >= beta:
            flag = 1  # Lower bound
        else:
            flag = 0  # Exact

        self.transposition_table[key] = (best_val, flag, depth)
        return best_val

    def check_win(self, pos):
        """
        Bitwise Connect 4 Win Check.
        Checks if 'pos' has 4 connected bits.
        """
        # Horizontal (Shift 7)
        m = pos & (pos >> 7)
        if m & (m >> 14): return True

        # Diagonal \ (Shift 6)
        m = pos & (pos >> 6)
        if m & (m >> 12): return True

        # Diagonal / (Shift 8)
        m = pos & (pos >> 8)
        if m & (m >> 16): return True

        # Vertical (Shift 1)
        m = pos & (pos >> 1)
        if m & (m >> 2): return True

        return False

    def evaluate_position(self, position, mask):
        """
        Heuristic evaluation for non-terminal nodes.
        Calculates a score based on 'threes' and 'twos' potential.
        """
        # Opponent position
        opp_position = position ^ mask

        # Score Accumulator
        score = 0

        # Weights
        W_3 = 100
        W_2 = 10

        # --- Evaluate MY threats ---
        # We simulate adding a stone in every possible slot (that is currently 0)
        # Actually, simpler: check for "3 stones + 1 empty" patterns via bitshifts.

        # Optimized approach:
        # A 4-window is playable if (opp_pos & window) == 0.
        # If (my_pos & window) has 3 bits -> Strong Score.
        # If (my_pos & window) has 2 bits -> Weak Score.

        # Vertical is easy:
        # 3 in a row vertically requires space on top.
        # (pos & (pos >> 1) & (pos >> 2)) gives bottom of 3-stack.
        # We need to check if the bit above is empty (not in mask).

        # This is computationally heavy for Python loops.
        # We use a simplified center-bias + lightweight structure count.

        # Center column preference (Start with this)
        # Col 3 (indices 21-26)
        center_mask = 0b111111 << 21
        my_center = (position & center_mask).bit_count()
        opp_center = (opp_position & center_mask).bit_count()
        score += (my_center - opp_center) * 5

        # Simple Threat Detection
        # This is a bit rough but fast.

        # My 3-in-a-row (Horizontal)
        # Pattern: 1110, 1101, 1011, 0111
        # We can implement 1110 by: m = pos & (pos >> 7) & (pos >> 14). Then check empty.

        # For Python speed, purely counting bits in the center and
        # relying on search depth is often better than complex Python eval.
        # However, to be "NewBot", we add a bitwise specific check for 3s.

        def count_patterns(p, m):
            count = 0

            # Horizontal (Shift 7) - Check XXX. pattern
            # m = p & (p >> 7) & (p >> 14) # 3 aligned
            # check if next is empty: (~m) & (m >> 7) ? No.

            # Use 'Popcount' of logical ANDs for quick adjacency estimation
            # Horizontal 2s
            h2 = p & (p >> 7)
            count += h2.bit_count() * W_2
            # Horizontal 3s
            h3 = h2 & (p >> 14)
            count += h3.bit_count() * W_3

            # Vertical 2s
            v2 = p & (p >> 1)
            count += v2.bit_count() * W_2
            # Vertical 3s
            v3 = v2 & (p >> 2)
            count += v3.bit_count() * W_3

            # Diag 2s
            d1_2 = p & (p >> 6)
            d2_2 = p & (p >> 8)
            count += (d1_2.bit_count() + d2_2.bit_count()) * W_2

            # Diag 3s
            d1_3 = d1_2 & (p >> 12)
            d2_3 = d2_2 & (p >> 16)
            count += (d1_3.bit_count() + d2_3.bit_count()) * W_3

            return count

        score += count_patterns(position, mask)
        score -= count_patterns(opp_position, mask)  # Subtract opponent potential

        return score

    def get_valid_moves(self, mask):
        moves = []
        for c in range(7):
            # Check if top row (row 5) is empty
            if (mask & (1 << (c * 7 + 5))) == 0:
                moves.append(c)
        return moves