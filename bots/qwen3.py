import time
from bots.bot import Bot

class ThreatHunterBot(Bot):
    def __init__(self, nom, symbole, profondeur=6, temps_max=0.5):
        super().__init__(nom, symbole)
        self.profondeur = profondeur
        self.temps_max = temps_max
        self.transposition_table = {}
        self.history_table = [0] * 7  # One entry per column

    def grille_à_tuple(self, plateau):
        return tuple(tuple(col + ["."] * (plateau.lignes - len(col))) for col in plateau.grille)

    def evaluate(self, plateau, symbole):
        opponent = 'O' if symbole == 'X' else 'X'
        score = 0

        # All possible directions for a Connect-4 line
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]

        for col in range(plateau.colonnes):
            for row in range(len(plateau.grille[col])):
                for dx, dy in directions:
                    self_count = 0
                    opp_count = 0
                    for i in range(4):
                        x = col + dx * i
                        y = row + dy * i
                        if 0 <= x < plateau.colonnes and 0 <= y < len(plateau.grille[x]):
                            cell = plateau.grille[x][y]
                            if cell == symbole:
                                self_count += 1
                            elif cell == opponent:
                                opp_count += 1
                    # Scoring system based on potential threats
                    if self_count > 0 and opp_count == 0:
                        score += {1: 1, 2: 10, 3: 100, 4: 1000}.get(self_count, 0)
                    elif opp_count > 0 and self_count == 0:
                        score -= {1: 1, 2: 10, 3: 100, 4: 1000}.get(opp_count, 0)

        # Center control bonus
        center = plateau.colonnes // 2
        for col in range(plateau.colonnes):
            if col == center:
                score += 10 * plateau.hauteurs_colonnes[col]
            elif abs(col - center) == 1:
                score += 5 * plateau.hauteurs_colonnes[col]

        return score

    def trouver_coup(self, plateau, joueur2):
        start_time = time.time()
        best_move = None
        best_score = -float('inf')
        self.transposition_table = {}
        self.history_table = [0] * 7
        max_depth = self.profondeur
        best_move_so_far = None

        for depth in range(1, max_depth + 1):
            alpha = -float('inf')
            beta = float('inf')
            current_best = -float('inf')
            current_move = None

            # Try immediate win first
            for col in list(plateau.colonnes_jouables):
                removed = plateau.jouer_coup_reversible(col, self.symbole)
                if plateau.est_victoire(col):
                    plateau.annuler_coup(col, removed, self.symbole)
                    return col
                plateau.annuler_coup(col, removed, self.symbole)

            # Order moves: history + center
            center = plateau.colonnes // 2
            moves = sorted(plateau.colonnes_jouables,
                           key=lambda c: (-self.history_table[c], abs(c - center)))

            for col in moves:
                removed = plateau.jouer_coup_reversible(col, self.symbole)
                if plateau.est_victoire(col):
                    plateau.annuler_coup(col, removed, self.symbole)
                    self.history_table[col] += depth * depth
                    return col
                score = -self.negamax(plateau, depth - 1, joueur2.symbole, -beta, -alpha)
                plateau.annuler_coup(col, removed, self.symbole)

                if score > current_best:
                    current_best = score
                    current_move = col
                if current_best > alpha:
                    alpha = current_best
                if alpha >= beta:
                    self.history_table[col] += depth * depth
                    break

            if current_best > best_score:
                best_score = current_best
                best_move_so_far = current_move

            if time.time() - start_time > self.temps_max:
                break

        return best_move_so_far or next(iter(plateau.colonnes_jouables))

    def negamax(self, plateau, depth, symbole, alpha, beta):
        key = self.grille_à_tuple(plateau)
        if key in self.transposition_table:
            entry = self.transposition_table[key]
            if entry['depth'] >= depth:
                if entry['type'] == 'exact':
                    return entry['score']
                elif entry['type'] == 'lowerbound':
                    alpha = max(alpha, entry['score'])
                elif entry['type'] == 'upperbound':
                    beta = min(beta, entry['score'])
                if alpha >= beta:
                    return entry['score']

        if depth == 0:
            return self.evaluate(plateau, symbole)

        best_score = -float('inf')
        center = plateau.colonnes // 2
        moves = sorted(plateau.colonnes_jouables,
                       key=lambda c: (-self.history_table[c], abs(c - center)))

        for col in moves:
            removed = plateau.jouer_coup_reversible(col, symbole)
            if plateau.est_victoire(col):
                plateau.annuler_coup(col, removed, symbole)
                score = 100000  # Winning move
                self.transposition_table[key] = {'depth': depth, 'score': score, 'type': 'exact'}
                return score

            next_symbole = self.symbole if symbole != self.symbole else 'O' if self.symbole == 'X' else 'X'
            score = -self.negamax(plateau, depth - 1, next_symbole, -beta, -alpha)
            plateau.annuler_coup(col, removed, symbole)

            if score > best_score:
                best_score = score
            if best_score > alpha:
                alpha = best_score
            if alpha >= beta:
                self.history_table[col] += depth * depth
                self.transposition_table[key] = {'depth': depth, 'score': best_score, 'type': 'lowerbound'}
                return best_score

        self.transposition_table[key] = {'depth': depth, 'score': best_score, 'type': 'exact'}
        return best_score