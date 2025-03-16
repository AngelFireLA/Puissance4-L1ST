import random
import time
from collections import deque

from bots.bot import Bot


def tri_coups(plateau):
    centre = plateau.colonnes // 2
    # Sort playable columns by how close they are to the center.
    return sorted(list(plateau.colonnes_jouables), key=lambda col: abs(col - centre))


class MTDfbBot(Bot):  # Unique name: MTDfbBot
    def __init__(self, nom, symbole, profondeur=6, temps_max=1):
        super().__init__(nom, symbole)
        self.profondeur = profondeur
        self.temps_max = temps_max
        self.table_transposition = {}
        self.temps_ecoule = 0
        self.killer_moves = [deque(maxlen=2) for _ in range(self.profondeur + 5)]  # +5 for iterative deepening
        self.history_moves = [[0] * 7 for _ in range(2)]  # 0 for player 1, 1 for player 2
        self.node_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.player_index = 0

    def reset(self):
        self.table_transposition = {}
        self.temps_ecoule = 0
        self.killer_moves = [deque(maxlen=2) for _ in range(self.profondeur + 5)]  # +5 for iterative deepening
        self.history_moves = [[0] * 7 for _ in range(2)]  # 0 for player 1, 1 for player 2
        self.node_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.player_index = 0

    def trouver_coup(self, plateau, joueur2) -> int:
        self.reset()
        self.player_index = 0 if self.symbole == 'X' else 1
        start_time = time.time()
        meilleur_coup = self.iterative_deepening(plateau, joueur2, start_time)
        self.temps_ecoule = time.time() - start_time
        # print(f"Temps écoulé: {self.temps_ecoule:.4f}s, Noeuds: {self.node_count}, Cache Hits: {self.cache_hits}, Cache Misses: {self.cache_misses}")
        return meilleur_coup

    def iterative_deepening(self, plateau, joueur2, start_time):
        meilleur_coup = random.choice(list(plateau.colonnes_jouables))
        profondeur_actuelle = 1

        while time.time() - start_time < self.temps_max and profondeur_actuelle <= self.profondeur:
            coup, _ = self.mtdf(plateau, 0, profondeur_actuelle, joueur2)
            if coup is not None:
                meilleur_coup = coup
            profondeur_actuelle += 1
            if self.temps_ecoule > self.temps_max:
                break

        return meilleur_coup

    def mtdf(self, plateau, f, profondeur, joueur2):
        g = f
        upperbound = float('inf')
        lowerbound = float('-inf')
        meilleur_coup = None

        while lowerbound < upperbound:
            if g == lowerbound:
                beta = g + 1
            else:
                beta = g
            meilleur_coup, g = self.negamax(plateau, profondeur, beta - 1, beta, 1, joueur2)  # null window search
            if self.temps_ecoule > self.temps_max:
                break
            if g < beta:
                upperbound = g
            else:
                lowerbound = g

        return meilleur_coup, g

    def negamax(self, plateau, profondeur, alpha, beta, couleur, joueur2):
        self.node_count += 1
        original_alpha = alpha
        hash_key = self.get_hash_key(plateau)
        entry = self.table_transposition.get(hash_key)

        if entry and entry["profondeur"] >= profondeur:
            self.cache_hits += 1
            if entry["type"] == "exact":
                return entry["coup"], entry["valeur"]
            elif entry["type"] == "lowerbound":
                alpha = max(alpha, entry["valeur"])
            elif entry["type"] == "upperbound":
                beta = min(beta, entry["valeur"])
            if alpha >= beta:
                return entry["coup"], entry["valeur"]
        else:
            self.cache_misses += 1

        if profondeur == 0 or plateau.est_nul():
            return None, couleur * self.heuristique(plateau, joueur2)

        meilleur_coup = None
        meilleur_valeur = float('-inf')

        for coup in self.order_moves(plateau, profondeur):
            colonne_est_enlevée = plateau.jouer_coup_reversible(coup, self.symbole if couleur == 1 else joueur2.symbole)
            if plateau.est_victoire(coup):
                plateau.annuler_coup(coup, colonne_est_enlevée, self.symbole if couleur == 1 else joueur2.symbole)
                valeur = 1000 + profondeur
                self.store_entry(hash_key, valeur, coup, profondeur, "exact")
                return coup, valeur

            _, valeur = self.negamax(plateau, profondeur - 1, -beta, -alpha, -couleur, joueur2)
            valeur = -valeur
            plateau.annuler_coup(coup, colonne_est_enlevée, self.symbole if couleur == 1 else joueur2.symbole)

            if valeur > meilleur_valeur:
                meilleur_valeur = valeur
                meilleur_coup = coup

            alpha = max(alpha, valeur)
            if alpha >= beta:
                if not plateau.grille[coup]:
                    self.killer_moves[profondeur].appendleft(coup)
                self.history_moves[self.player_index][coup] += profondeur * profondeur
                break

        if meilleur_valeur <= original_alpha:
            entry_type = "upperbound"
        elif meilleur_valeur >= beta:
            entry_type = "lowerbound"
        else:
            entry_type = "exact"

        self.store_entry(hash_key, meilleur_valeur, meilleur_coup, profondeur, entry_type)
        return meilleur_coup, meilleur_valeur

    def order_moves(self, plateau, profondeur):
        moves = list(plateau.colonnes_jouables)
        centre = plateau.colonnes // 2
        move_scores = []

        for move in moves:
            score = 0
            # Killer move heuristic
            if move in self.killer_moves[profondeur]:
                score += 1000

            # History heuristic (scaled down to avoid overpowering killer moves)
            score += self.history_moves[self.player_index][move] / 100

            # Center bias
            score += (plateau.colonnes - abs(move - centre))

            move_scores.append((move, score))

        # Sort moves based on their scores, highest score first
        ordered_moves = [move for move, score in sorted(move_scores, key=lambda x: x[1], reverse=True)]
        return ordered_moves

    def store_entry(self, hash_key, valeur, coup, profondeur, entry_type):
        self.table_transposition[hash_key] = {"valeur": valeur, "coup": coup, "profondeur": profondeur,
                                              "type": entry_type}

    def get_hash_key(self, plateau):
        flat_board = [cell if cell else '.' for sublist in plateau.grille for cell in sublist]
        return tuple(flat_board), tuple(plateau.hauteurs_colonnes)

    def heuristique(self, plateau, joueur2):
        score = 0
        # Check for potential wins and threats
        for col in plateau.colonnes_jouables:
            # Simulate my move
            plateau.jouer_coup_reversible(col, self.symbole)
            if plateau.est_victoire(col):
                score += 500  # Prioritize winning moves
            plateau.annuler_coup(col, True, self.symbole)  # Always undo

            # Simulate opponent's move
            plateau.jouer_coup_reversible(col, joueur2.symbole)
            if plateau.est_victoire(col):
                score -= 500  # Block opponent's winning moves
            plateau.annuler_coup(col, True, joueur2.symbole)

        # Evaluate board position (central control, connectivity)
        score += self.evaluate_central_control(plateau) * 5
        score += self.evaluate_connectivity(plateau, self.symbole) * 3
        score -= self.evaluate_connectivity(plateau, joueur2.symbole) * 3

        return score

    def evaluate_central_control(self, plateau):
        center_columns = [2, 3, 4]  # Middle columns (0-indexed)
        control_score = 0
        for col in center_columns:
            for cell in plateau.grille[col]:
                if cell == self.symbole:
                    control_score += 1
                elif cell != '.':  # Opponent's token
                    control_score -= 1
        return control_score

    def evaluate_connectivity(self, plateau, symbole):
        connectivity_score = 0
        for col in range(plateau.colonnes):
            for row in range(plateau.hauteurs_colonnes[col]):
                if plateau.grille[col][row] == symbole:
                    connectivity_score += self.count_connected(plateau, col, row, symbole)
        return connectivity_score

    def count_connected(self, plateau, col, row, symbole):
        count = 0
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]  # Horizontal, vertical, diagonals
        for dx, dy in directions:
            # Count in positive direction
            count += self.count_direction(plateau, col, row, dx, dy, symbole)
            # Count in negative direction
            count += self.count_direction(plateau, col, row, -dx, -dy, symbole)
        return count

    def count_direction(self, plateau, col, row, dx, dy, symbole):
        count = 0
        x, y = col + dx, row + dy
        while 0 <= x < plateau.colonnes and 0 <= y < plateau.lignes and y < len(plateau.grille[x]) and plateau.grille[x][
            y] == symbole:
            count += 1
            x += dx
            y += dy
        return count