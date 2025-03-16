import random
import time
from bots.bot import Bot

class ZobristNegamaxBot(Bot):
    def __init__(self, nom, symbole, temps_max=1):
        super().__init__(nom, symbole)
        self.zobrist_tables = {}  # Key: (cols, rows), value: Zobrist table
        self.lines_cache = {}      # Key: (cols, rows), value: list of lines
        self.transposition_table = None
        self.temps_max = temps_max

    def trouver_coup(self, plateau, joueur2) -> int:
        # Reset transposition table for each move
        self.transposition_table = {}
        cols = plateau.colonnes
        rows = plateau.lignes

        # Generate or retrieve Zobrist table and lines for the current board size
        if (cols, rows) not in self.zobrist_tables:
            self._generate_zobrist_table(cols, rows)
        zobrist_table = self.zobrist_tables[(cols, rows)]

        if (cols, rows) not in self.lines_cache:
            self.lines_cache[(cols, rows)] = self._generate_lines(cols, rows)
        lines = self.lines_cache[(cols, rows)]

        # Compute initial hash
        current_hash = self._compute_initial_hash(plateau, zobrist_table)
        opponent_symbole = joueur2.symbole

        best_move = None
        best_score = -float('inf')
        depth = 1
        self.start_time = time.time()

        # Iterative deepening loop
        while time.time() - self.start_time < self.temps_max:
            guess = best_score if depth > 1 else 0
            score, move = self._mtdf(plateau, depth, guess, zobrist_table, lines, current_hash, self.symbole, opponent_symbole)
            if score > best_score or best_move is None:
                best_score = score
                best_move = move
            depth += 1

        # Fallback to first available move if no move found
        if best_move is None or best_move not in plateau.colonnes_jouables:
            best_move = next(iter(plateau.colonnes_jouables)) if plateau.colonnes_jouables else 0

        return best_move

    def _mtdf(self, plateau, depth, initial_guess, zobrist_table, lines, current_hash, symbole, opponent_symbole):
        score = initial_guess
        upper = float('inf')
        lower = -float('inf')
        best_move = None

        while lower < upper and time.time() - self.start_time < self.temps_max:
            beta = max(score + 1, lower + 1)
            current_score, current_move = self._negamax(plateau, depth, beta - 1, beta, zobrist_table, lines, current_hash, symbole, opponent_symbole)
            if current_score < beta:
                upper = current_score
            else:
                lower = current_score
            score = current_score
            best_move = current_move if current_move is not None else best_move

        return score, best_move

    def _negamax(self, plateau, depth, alpha, beta, zobrist_table, lines, current_hash, symbole, opponent_symbole):
        # Transposition table lookup
        key = (current_hash, depth, symbole)
        entry = self.transposition_table.get(key, None)
        if entry:
            if entry['lower'] >= beta:
                return entry['lower'], entry['move']
            if entry['upper'] <= alpha:
                return entry['upper'], entry['move']
            alpha = max(alpha, entry['lower'])
            beta = min(beta, entry['upper'])

        # Terminal node check
        if depth == 0 or plateau.est_nul():
            eval_score = self._evaluate(plateau, lines, symbole, opponent_symbole)
            return eval_score, None

        moves = self._order_moves(plateau, symbole, opponent_symbole)
        best_score = -float('inf')
        best_move = None

        for move in moves:
            # Play move and update hash
            colonne_est_enlevee = plateau.jouer_coup_reversible(move, symbole)
            row = plateau.hauteurs_colonnes[move] - 1
            new_hash = current_hash ^ zobrist_table[move][row][symbole]

            # Check for immediate win
            if plateau.est_victoire(move):
                plateau.annuler_coup(move, colonne_est_enlevee, symbole)
                score = 1000 + depth
                if score > best_score:
                    best_score = score
                    best_move = move
                if best_score >= beta:
                    self._update_transposition_table(key, best_score, best_move, 'lower', alpha, beta)
                    return best_score, best_move
                continue

            # Recurse
            next_symbole = opponent_symbole if symbole == self.symbole else self.symbole
            score, _ = self._negamax(plateau, depth-1, -beta, -alpha, zobrist_table, lines, new_hash, next_symbole, opponent_symbole)
            score = -score

            # Undo move
            plateau.annuler_coup(move, colonne_est_enlevee, symbole)

            # Update best score and move
            if score > best_score:
                best_score = score
                best_move = move
                if score > alpha:
                    alpha = score
                if alpha >= beta:
                    break

        # Update transposition table
        self._update_transposition_table(key, best_score, best_move, 'exact', alpha, beta)
        return best_score, best_move

    def _evaluate(self, plateau, lines, symbole, opponent_symbole):
        score = 0
        for line in lines:
            count = 0
            opponent_count = 0
            empty = 0
            for (c, r) in line:
                if r >= plateau.hauteurs_colonnes[c]:
                    empty += 1
                    continue
                token = plateau.grille[c][r]
                if token == symbole:
                    count += 1
                elif token == opponent_symbole:
                    opponent_count += 1
                else:
                    empty += 1
            if count == 4:
                score += 100000
            elif opponent_count == 4:
                score -= 100000
            else:
                if count == 3 and empty == 1:
                    score += 1000
                elif count == 2 and empty == 2:
                    score += 10
                if opponent_count == 3 and empty == 1:
                    score -= 1000
                elif opponent_count == 2 and empty == 2:
                    score -= 10
        # Center control bonus
        center = plateau.colonnes // 2
        for c in [center-1, center, center+1]:
            if 0 <= c < plateau.colonnes and plateau.hauteurs_colonnes[c] > 0:
                if plateau.grille[c][-1] == symbole:
                    score += 5
                elif plateau.grille[c][-1] == opponent_symbole:
                    score -= 5
        return score

    def _order_moves(self, plateau, symbole, opponent_symbole):
        center = plateau.colonnes // 2
        playable = sorted(plateau.colonnes_jouables, key=lambda c: abs(c - center))
        return playable

    def _generate_zobrist_table(self, cols, rows):
        zobrist = []
        for c in range(cols):
            col = []
            for r in range(rows):
                col.append({
                    self.symbole: random.getrandbits(64),
                    self.opponent_symbol: random.getrandbits(64)
                })
            zobrist.append(col)
        self.zobrist_tables[(cols, rows)] = zobrist

    def _compute_initial_hash(self, plateau, zobrist_table):
        hash_val = 0
        for c in range(plateau.colonnes):
            for r in range(len(plateau.grille[c])):
                symbol = plateau.grille[c][r]
                hash_val ^= zobrist_table[c][r][symbol]
        return hash_val

    def _generate_lines(self, cols, rows):
        lines = []
        # Horizontal
        for c in range(cols - 3):
            for r in range(rows):
                lines.append([(c, r), (c+1, r), (c+2, r), (c+3, r)])
        # Vertical
        for c in range(cols):
            for r in range(rows - 3):
                lines.append([(c, r), (c, r+1), (c, r+2), (c, r+3)])
        # Diagonal down-right
        for c in range(cols - 3):
            for r in range(rows - 3):
                lines.append([(c, r), (c+1, r+1), (c+2, r+2), (c+3, r+3)])
        # Diagonal down-left
        for c in range(cols - 3):
            for r in range(3, rows):
                lines.append([(c, r), (c+1, r-1), (c+2, r-2), (c+3, r-3)])
        return lines

    def _update_transposition_table(self, key, score, move, entry_type, alpha, beta):
        entry = self.transposition_table.get(key, {'lower': -float('inf'), 'upper': float('inf'), 'move': None})
        if entry_type == 'exact':
            entry['lower'] = score
            entry['upper'] = score
        elif entry_type == 'lower':
            entry['lower'] = max(entry['lower'], score)
        elif entry_type == 'upper':
            entry['upper'] = min(entry['upper'], score)
        entry['move'] = move if move is not None else entry['move']
        self.transposition_table[key] = entry

    @property
    def opponent_symbol(self):
        return 'X' if self.symbole == 'O' else 'O'