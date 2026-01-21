from .bot import Bot
import time
import math
import random

# A strong, fast alpha-beta/PVS Connect 4 bot with iterative deepening, transposition table,
# killer/history heuristics, center-biased move ordering, and a compact heuristic evaluation.
# Deterministic by design.


class OrionBlade(Bot):
    def __init__(
        self,
        nom,
        symbole,
        profondeur=9,           # max search depth (iterative deepening will ramp up to this)
        temps_max=0,         # time budget per move in seconds; 0 disables and uses fixed depth
        tt_size=1_000_003,      # approx hash table slots (prime)
        use_tt=True,
        use_iterative=True,
    ):
        super().__init__(nom, symbole)
        self.profondeur = int(profondeur)
        self.temps_max = float(temps_max)
        self.use_tt = bool(use_tt)
        self.use_iterative = bool(use_iterative)

        # Debug counters
        self.coups = 0  # number of positions explored in last move

        # Deterministic RNG for zobrist and any ordering ties
        self._rng = random.Random(0xA0BEEF)

        # Zobrist keys per board size (cols, rows) -> (keys, side_to_move_key)
        self._zobrist_cache = {}
        # Precomputed windows per board size (cols, rows)
        self._windows_cache = {}
        # Center order per board size
        self._center_order_cache = {}

        # Transposition Table (in-move); key -> (depth, flag, value, best_move)
        # flags: 0=EXACT, -1=ALPHA (lower bound), +1=BETA (upper bound)
        self._tt = {}
        self._tt_size = int(tt_size)

        # Killer moves, history heuristic
        self._killer1 = None
        self._killer2 = None
        self._history = None

        # Deadline control
        self._deadline = None
        self._time_exceeded = False

        # Constants
        self._INF = 10**9
        self._WIN = 10**7  # win score base
        self._CHECK_TIME_EVERY = 2047  # check deadline every N nodes

    # ------------- Public API -------------

    def trouver_coup(self, plateau, joueur2) -> int:
        # Setup search state for this move
        self.coups = 0
        my = self.symbole
        opp = joueur2.symbole
        cols = plateau.colonnes
        rows = plateau.lignes

        self._ensure_tables(cols, rows)

        # Reset per-move structures
        self._tt = {} if self.use_tt else None
        self._killer1 = [-1] * 64
        self._killer2 = [-1] * 64
        self._history = [0] * cols
        self._time_exceeded = False

        # Time budget
        if self.temps_max and self.temps_max > 0:
            self._deadline = time.perf_counter() + self.temps_max
        else:
            self._deadline = None

        # Quick tactical checks first
        # 1) Immediate winning move (play now and win)
        for c in self._center_order(cols):
            if c in plateau.colonnes_jouables:
                removed = plateau.jouer_coup_reversible(c, my)
                if plateau.est_victoire(c):
                    plateau.annuler_coup(c, removed, my)
                    # print(f"[OrionBlade] Immediate win in column {c}")
                    return c
                plateau.annuler_coup(c, removed, my)

        # 2) Immediate block required? (opponent can win next move if we do nothing)
        opp_wins = []
        for c in self._center_order(cols):
            if c in plateau.colonnes_jouables:
                removed = plateau.jouer_coup_reversible(c, opp)
                if plateau.est_victoire(c):
                    opp_wins.append(c)
                plateau.annuler_coup(c, removed, opp)
        if len(opp_wins) >= 1:
            # If multiple threats, pick one in center order (can't block all)
            # print(f"[OrionBlade] Forced block in column {opp_wins[0]}")
            return opp_wins[0]

        # Root default move (center bias)
        default_move = self._default_move(plateau)

        # Root hash
        root_hash = self._compute_hash(plateau, my_to_move=True)

        # Iterative deepening PVS
        best_move = default_move
        best_score = -self._INF
        prev_score = None

        max_depth = self.profondeur if self.profondeur > 0 else 7

        # Simple aspiration window control
        def aspiration_bounds(pscore):
            w = 128  # window
            return pscore - w, pscore + w

        try:
            if self.use_iterative:
                for depth in range(1, max_depth + 1):
                    if self._timeout():
                        break
                    alpha = -self._INF
                    beta = self._INF
                    if prev_score is not None:
                        a, b = aspiration_bounds(prev_score)
                        if a < b:
                            alpha, beta = a, b
                    score, move = self._search_root(plateau, depth, alpha, beta, my, opp, root_hash)
                    # Aspiration re-search if needed
                    if score <= alpha and not self._timeout():
                        score, move = self._search_root(plateau, depth, -self._INF, beta, my, opp, root_hash)
                    elif score >= beta and not self._timeout():
                        score, move = self._search_root(plateau, depth, alpha, self._INF, my, opp, root_hash)

                    if not self._timeout() and move is not None:
                        best_score, best_move = score, move
                        prev_score = score
                    else:
                        break
            else:
                # Fixed-depth only
                score, move = self._search_root(plateau, max_depth, -self._INF, self._INF, my, opp, root_hash)
                if move is not None:
                    best_score, best_move = score, move
        except _SearchTimeout:
            pass

        # Fallback if something odd happened
        if best_move is None:
            best_move = default_move

        # print(f"[OrionBlade] chose {best_move} score {best_score} depth_reached {depth if self.use_iterative else max_depth} nodes {self.coups}")
        return best_move

    # ------------- Core search -------------

    def _search_root(self, plateau, depth, alpha, beta, my, opp, hash_key):
        # Root ordering with "safety" filter (avoid giving opponent an immediate reply win if alternatives exist)
        moves_all = [c for c in self._center_order(plateau.colonnes) if c in plateau.colonnes_jouables]
        if not moves_all:
            return 0, None

        tt_move = None
        if self.use_tt:
            entry = self._tt_get(hash_key)
            if entry is not None:
                _, _, _, mv = entry
                if mv in plateau.colonnes_jouables:
                    tt_move = mv

        winning_moves = []
        safe_moves = []
        losing_moves = []

        # Evaluate safety: after we play c, can opp win immediately?
        # We only do this at root to avoid overhead.
        for c in moves_all:
            # Check if it's an instant win (already handled at top of trouver_coup, but cheap to repeat)
            removed = plateau.jouer_coup_reversible(c, my)
            if plateau.est_victoire(c):
                plateau.annuler_coup(c, removed, my)
                winning_moves.append(c)
                continue
            opp_can_win = False
            for oc in moves_all:
                if oc in plateau.colonnes_jouables:
                    r2 = plateau.jouer_coup_reversible(oc, opp)
                    if plateau.est_victoire(oc):
                        opp_can_win = True
                        plateau.annuler_coup(oc, r2, opp)
                        break
                    plateau.annuler_coup(oc, r2, opp)
            plateau.annuler_coup(c, removed, my)
            if opp_can_win:
                losing_moves.append(c)
            else:
                safe_moves.append(c)

        ordered = []
        # TT move first if exists (and not yet added)
        if tt_move is not None and tt_move in winning_moves:
            ordered.append(tt_move)
            winning_moves = [m for m in winning_moves if m != tt_move]
        ordered.extend(winning_moves)

        # killers just for ordering after wins
        k1 = self._killer1[0]
        k2 = self._killer2[0]
        def add_if_ok(lst, m):
            if m != -1 and m in plateau.colonnes_jouables and m not in lst and m not in ordered:
                lst.append(m)

        killers = []
        add_if_ok(killers, k1)
        add_if_ok(killers, k2)

        # Safe moves by center closeness and history heuristic
        def score_move(c):
            # center bias + history
            center = plateau.colonnes // 2
            return -abs(c - center) * 10 + self._history[c]

        safe_moves.sort(key=score_move, reverse=True)
        losing_moves.sort(key=score_move, reverse=True)

        # TT move if not yet placed and not a winning move
        if tt_move is not None and tt_move not in ordered and tt_move in plateau.colonnes_jouables:
            ordered.append(tt_move)

        ordered.extend(killers)
        # Then safe moves
        for m in safe_moves:
            if m not in ordered:
                ordered.append(m)
        # then losing moves (if nothing else)
        for m in losing_moves:
            if m not in ordered:
                ordered.append(m)

        best_score = -self._INF
        best_move = None
        first = True

        for c in ordered:
            if self._timeout():
                break

            # play
            removed = plateau.jouer_coup_reversible(c, my)
            row = plateau.hauteurs_colonnes[c] - 1
            h2 = hash_key ^ self._zobrist_piece(c, row, my) ^ self._zobrist_side()

            # principal variation search
            if first:
                score = -self._pvs(plateau, depth - 1, -beta, -alpha, c, opp, my, h2, ply=1)
                first = False
            else:
                score = -self._pvs(plateau, depth - 1, -alpha - 1, -alpha, c, opp, my, h2, ply=1)
                if score > alpha and score < beta:
                    score = -self._pvs(plateau, depth - 1, -beta, -alpha, c, opp, my, h2, ply=1)

            # unplay
            plateau.annuler_coup(c, removed, my)

            if score > best_score:
                best_score = score
                best_move = c
            if best_score > alpha:
                alpha = best_score
            if alpha >= beta:
                self._store_killer(0, c)
                break

        # Store in TT
        if self.use_tt and not self._timeout():
            flag = 0
            if best_score <= -self._INF + 1:
                flag = -1
            elif best_score >= self._INF - 1:
                flag = 1
            self._tt_put(hash_key, depth, best_score, best_move, alpha, beta)

        return best_score, best_move

    def _pvs(self, plateau, depth, alpha, beta, last_col, to_move_sym, other_sym, hash_key, ply):
        # Negamax-style PVS: score is from perspective of "current player" (to_move_sym)
        # Returns scalar score (higher is better for player to move)
        self.coups += 1
        if (self.coups & self._CHECK_TIME_EVERY) == 0 and self._timeout():
            raise _SearchTimeout()

        # Terminal checks: did opponent just win with last_col?
        # If previous move (by other_sym) created a win, current side has lost.
        if last_col is not None and plateau.est_victoire(last_col):
            # So, previous player won -> bad for current player. Use depth to prefer faster wins/slower losses.
            return -self._WIN + ply

        if plateau.est_nul():
            return 0

        if depth <= 0:
            return self._evaluate_for(plateau, to_move_sym, other_sym)

        # TT probe
        if self.use_tt:
            entry = self._tt_get(hash_key)
            if entry is not None:
                edepth, flag, val, mv = entry
                if edepth >= depth:
                    if flag == 0:
                        return val
                    elif flag == -1 and val <= alpha:
                        return val
                    elif flag == 1 and val >= beta:
                        return val

        moves = self._ordered_moves(plateau, to_move_sym, other_sym, ply)
        if not moves:
            return 0

        best_score = -self._INF
        best_move = moves[0]
        first = True

        old_alpha = alpha

        for c in moves:
            # play
            removed = plateau.jouer_coup_reversible(c, to_move_sym)
            row = plateau.hauteurs_colonnes[c] - 1
            h2 = hash_key ^ self._zobrist_piece(c, row, to_move_sym) ^ self._zobrist_side()

            # Early win detection speeds pruning
            if plateau.est_victoire(c):
                score = self._WIN - ply
            else:
                # PVS null-window on non-PV moves
                if first:
                    score = -self._pvs(plateau, depth - 1, -beta, -alpha, c, other_sym, to_move_sym, h2, ply + 1)
                    first = False
                else:
                    score = -self._pvs(plateau, depth - 1, -alpha - 1, -alpha, c, other_sym, to_move_sym, h2, ply + 1)
                    if score > alpha and score < beta:
                        score = -self._pvs(plateau, depth - 1, -beta, -alpha, c, other_sym, to_move_sym, h2, ply + 1)

            # unplay
            plateau.annuler_coup(c, removed, to_move_sym)

            if score > best_score:
                best_score = score
                best_move = c
            if best_score > alpha:
                alpha = best_score
            if alpha >= beta:
                # Cutoff: record killer/history
                self._store_killer(ply, c)
                self._history[c] += depth * depth
                break

        # Store TT
        if self.use_tt:
            flag = 0
            if best_score <= old_alpha:
                flag = -1
            elif best_score >= beta:
                flag = 1
            self._tt_put(hash_key, depth, best_score, best_move, old_alpha, beta)

        return best_score

    # ------------- Move ordering -------------

    def _ordered_moves(self, plateau, to_move_sym, other_sym, ply):
        # Combine TT best, immediate wins, killers, center bias, and history
        cols = plateau.colonnes
        moves = [c for c in self._center_order(cols) if c in plateau.colonnes_jouables]
        if not moves:
            return []

        tt_move = None
        if self.use_tt:
            # We can't access hash here; it is passed into pvs; but we are probing at this node with given hash.
            # So probe is handled before calling this in _pvs. Here we just grab nothing.
            pass

        # Identify immediate wins for ordering
        winning = []
        non_winning = []
        for c in moves:
            removed = plateau.jouer_coup_reversible(c, to_move_sym)
            if plateau.est_victoire(c):
                winning.append(c)
                plateau.annuler_coup(c, removed, to_move_sym)
                continue
            plateau.annuler_coup(c, removed, to_move_sym)
            non_winning.append(c)

        k1 = self._killer1[ply] if ply < len(self._killer1) else -1
        k2 = self._killer2[ply] if ply < len(self._killer2) else -1

        # Order non-winning by killers and then by center/history bias
        def score_move(c):
            center = plateau.colonnes // 2
            s = -abs(c - center) * 10 + self._history[c]
            if c == k1:
                s += 1000
            elif c == k2:
                s += 900
            return s

        non_winning.sort(key=score_move, reverse=True)

        ordered = []
        ordered.extend(winning)
        ordered.extend(non_winning)
        return ordered

    def _store_killer(self, ply, move):
        if ply >= len(self._killer1):
            return
        if self._killer1[ply] != move:
            self._killer2[ply] = self._killer1[ply]
            self._killer1[ply] = move

    # ------------- Heuristic evaluation -------------

    def _evaluate_for(self, plateau, my, opp):
        # Simple but punchy evaluation based on 4-cell window counts + center bias
        cols = plateau.colonnes
        rows = plateau.lignes
        grid = plateau.grille
        heights = plateau.hauteurs_colonnes

        score = 0

        # Center bias: prefer stacking in middle column(s)
        center_col = cols // 2
        if 0 <= center_col < cols:
            h = heights[center_col]
            col_list = grid[center_col]
            for r in range(h):
                piece = col_list[r]
                if piece == my:
                    score += 6
                elif piece == opp:
                    score -= 6

        # Slight bias to near-center columns
        for c in range(cols):
            if c == center_col:
                continue
            bias = max(0, 3 - abs(c - center_col))
            h = heights[c]
            col_list = grid[c]
            for r in range(h):
                piece = col_list[r]
                if piece == my:
                    score += bias
                elif piece == opp:
                    score -= bias

        # Evaluate all 4-in-a-row windows
        for window in self._windows(cols, rows):
            my_count = 0
            opp_count = 0
            empty = 0
            # Unrolled loop for speed
            for (cx, ry) in window:
                if ry < heights[cx]:
                    piece = grid[cx][ry]
                    if piece == my:
                        my_count += 1
                    elif piece == opp:
                        opp_count += 1
                    else:
                        empty += 1
                else:
                    empty += 1

            if my_count and opp_count:
                continue

            # Tuned weights
            if my_count == 4:
                score += 100000
            elif my_count == 3 and empty == 1:
                score += 120
            elif my_count == 2 and empty == 2:
                score += 10
            elif my_count == 1 and empty == 3:
                score += 2

            if opp_count == 4:
                score -= 100000
            elif opp_count == 3 and empty == 1:
                score -= 130  # a bit more than ours to encourage blocking
            elif opp_count == 2 and empty == 2:
                score -= 12
            elif opp_count == 1 and empty == 3:
                score -= 2

        return score

    # ------------- Helpers: windows, zobrist, hash, ordering -------------

    def _windows(self, cols, rows):
        key = (cols, rows)
        return self._windows_cache[key]

    def _center_order(self, cols):
        if cols in self._center_order_cache:
            return self._center_order_cache[cols]
        center = cols // 2
        order = [center]
        for d in range(1, cols):
            if center - d >= 0:
                order.append(center - d)
            if center + d < cols:
                order.append(center + d)
        self._center_order_cache[cols] = order
        return order

    def _ensure_tables(self, cols, rows):
        # Precompute windows
        key = (cols, rows)
        if key not in self._windows_cache:
            wins = []
            # horizontal
            for r in range(rows):
                for c in range(cols - 3):
                    wins.append(((c, r), (c + 1, r), (c + 2, r), (c + 3, r)))
            # vertical
            for c in range(cols):
                for r in range(rows - 3):
                    wins.append(((c, r), (c, r + 1), (c, r + 2), (c, r + 3)))
            # diag up-right
            for c in range(cols - 3):
                for r in range(rows - 3):
                    wins.append(((c, r), (c + 1, r + 1), (c + 2, r + 2), (c + 3, r + 3)))
            # diag down-right
            for c in range(cols - 3):
                for r in range(3, rows):
                    wins.append(((c, r), (c + 1, r - 1), (c + 2, r - 2), (c + 3, r - 3)))
            self._windows_cache[key] = wins

        # Zobrist keys
        if key not in self._zobrist_cache:
            zkeys = [[[self._rng.getrandbits(64) for _ in range(2)] for _ in range(rows)] for _ in range(cols)]
            zside = self._rng.getrandbits(64)
            self._zobrist_cache[key] = (zkeys, zside)

    def _zobrist_piece(self, c, r, sym):
        cols = len(self._zobrist_cache)
        keys, _ = self._zobrist_cache[next(iter(self._zobrist_cache))]
        # We must pick correct key for current board size; safer:
        # get last created, but better to get via plateau dims; we always call after _ensure_tables.
        zkeys, _ = list(self._zobrist_cache.values())[-1]
        idx = 0 if sym == 'X' else 1
        return zkeys[c][r][idx]

    def _zobrist_side(self):
        _, zside = list(self._zobrist_cache.values())[-1]
        return zside

    def _compute_hash(self, plateau, my_to_move=True):
        cols = plateau.colonnes
        rows = plateau.lignes
        zkeys, zside = self._zobrist_cache[(cols, rows)]
        h = 0
        grid = plateau.grille
        heights = plateau.hauteurs_colonnes
        for c in range(cols):
            hcol = heights[c]
            col_list = grid[c]
            for r in range(hcol):
                piece = col_list[r]
                idx = 0 if piece == 'X' else 1
                h ^= zkeys[c][r][idx]
        if my_to_move:
            h ^= zside
        return h

    def _default_move(self, plateau):
        # Prefer center-most playable column
        for c in self._center_order(plateau.colonnes):
            if c in plateau.colonnes_jouables:
                return c
        # fallback (shouldn't happen)
        return list(plateau.colonnes_jouables)[0]

    # ------------- Transposition table -------------

    def _tt_get(self, key):
        if not self.use_tt:
            return None
        return self._tt.get(key, None)

    def _tt_put(self, key, depth, value, best_move, alpha, beta):
        if not self.use_tt:
            return
        flag = 0
        if value <= alpha:
            flag = -1
        elif value >= beta:
            flag = 1
        # Replacement scheme: store if new or deeper
        prev = self._tt.get(key)
        if prev is None or prev[0] <= depth:
            if len(self._tt) > self._tt_size:
                # Light cleanup: drop random ~1% keys
                for _ in range(1000):
                    k = next(iter(self._tt))
                    del self._tt[k]
            self._tt[key] = (depth, flag, value, best_move)

    # ------------- Deadline -------------

    def _timeout(self):
        if self._deadline is None:
            return False
        if self._time_exceeded:
            return True
        if time.perf_counter() >= self._deadline:
            self._time_exceeded = True
            return True
        return False


class _SearchTimeout(Exception):
    pass