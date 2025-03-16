import random
import math
from bots.bot import Bot


def other_symbol(symbol):
    return 'O' if symbol == 'X' else 'X'


class MCTSNode:
    def __init__(self, plateau, move=None, parent=None, player=None):
        self.plateau = plateau
        self.move = move
        self.parent = parent
        self.children = {}
        self.wins = 0
        self.visits = 0
        self.untried_moves = list(plateau.colonnes_jouables)
        self.player = player

    def UCT_select_child(self, exploration=1.41):  # Adjusted exploration parameter
        best_score = -float('inf')
        best_child = None
        for child in self.children.values():
            # UCT formula
            score = (child.wins / child.visits) + exploration * math.sqrt(math.log(self.visits) / child.visits)
            if score > best_score:
                best_score = score
                best_child = child
        return best_child

    def add_child(self, move, plateau, next_player):
        self.untried_moves.remove(move)
        child_node = MCTSNode(plateau, move, parent=self, player=next_player)
        self.children[move] = child_node
        return child_node

    def update(self, result, root_symbol):
        self.visits += 1
        if self.player == root_symbol:
            self.wins += result
        else:
            self.wins += (1 - result)


class ImprovedMCTSBot(Bot):
    def __init__(self, nom, symbole, iterations=2000):
        super().__init__(nom, symbole)
        self.iterations = iterations

    def _evaluate_position(self, plateau, move, player):
        """Simple heuristic for position evaluation during simulation"""
        score = 0

        # Prefer center columns
        column_weights = [3, 4, 5, 7, 5, 4, 3]  # Higher weight for center columns
        if 0 <= move < len(column_weights):
            score += column_weights[move] * 0.1

        # Check for potential threats (connect-3)
        # This would require implementing threat detection logic

        return score

    def _semi_random_move(self, plateau, player):
        """Return a move using a semi-random heuristic instead of pure random"""
        playable = list(plateau.colonnes_jouables)
        if not playable:
            return None

        # Check for immediate wins
        for move in playable:
            board_copy = plateau.copier_grille()
            board_copy.jouer_coup_reversible(move, player)
            if board_copy.est_victoire(move):
                return move

        # Weighted random selection based on column position
        weights = []
        for move in playable:
            # Center columns are preferred
            weight = 4 if move == 3 else 3 if move in (2, 4) else 2 if move in (1, 5) else 1
            weights.append(weight)

        return random.choices(playable, weights=weights, k=1)[0]

    def trouver_coup(self, plateau, joueur2) -> int:
        # 1. Check for immediate winning moves
        for move in list(plateau.colonnes_jouables):
            board_copy = plateau.copier_grille()
            board_copy.jouer_coup_reversible(move, self.symbole)
            if board_copy.est_victoire(move):
                return move

        # 2. Check for opponent's immediate winning moves to block
        for move in list(plateau.colonnes_jouables):
            board_copy = plateau.copier_grille()
            board_copy.jouer_coup_reversible(move, joueur2.symbole)
            if board_copy.est_victoire(move):
                return move

        # 3. Set up the MCTS root node
        root_plateau = plateau.copier_grille()
        root = MCTSNode(root_plateau, player=self.symbole)

        # Run MCTS iterations
        for _ in range(self.iterations):
            # Selection phase
            node = root
            state = root_plateau.copier_grille()
            current_player = self.symbole

            # Select a path through the tree
            while node.untried_moves == [] and node.children:
                node = node.UCT_select_child()
                state.jouer_coup_reversible(node.move, current_player)
                current_player = other_symbol(current_player)

            # Expansion phase
            if node.untried_moves:
                # Use move ordering to prioritize promising moves
                move = self._semi_random_move(state, current_player)
                if move in node.untried_moves:  # Ensure move is valid
                    state.jouer_coup_reversible(move, current_player)
                    node = node.add_child(move, state.copier_grille(), other_symbol(current_player))
                    current_player = other_symbol(current_player)
                else:
                    # Fallback to random if our heuristic failed
                    move = random.choice(node.untried_moves)
                    state.jouer_coup_reversible(move, current_player)
                    node = node.add_child(move, state.copier_grille(), other_symbol(current_player))
                    current_player = other_symbol(current_player)

            # Simulation phase - use semi-random playout instead of pure random
            winner = None
            playout_depth = 0
            max_playout_depth = 20  # Limit simulation length

            while playout_depth < max_playout_depth:
                playable_moves = list(state.colonnes_jouables)
                if not playable_moves:
                    break  # Draw

                # Use semi-random move selection for better simulation
                move = self._semi_random_move(state, current_player)
                state.jouer_coup_reversible(move, current_player)
                playout_depth += 1

                if state.est_victoire(move):
                    winner = current_player
                    break

                current_player = other_symbol(current_player)

            # Determine result
            if winner == self.symbole:
                result = 1
            elif winner is None:
                result = 0.5
            else:
                result = 0

            # Backpropagation
            node_to_update = node
            while node_to_update is not None:
                node_to_update.update(result, self.symbole)
                node_to_update = node_to_update.parent

        # Select best move
        best_move = None
        best_wins = -1
        min_visits = max(5, self.iterations * 0.01)  # Ensure minimum visit threshold

        # Consider both visit count and win rate with robustness check
        for move, child in root.children.items():
            if child.visits >= min_visits:
                win_rate = child.wins / child.visits
                robustness = child.visits / self.iterations
                score = win_rate * (0.6 + 0.4 * robustness)  # Balance win rate and visit count

                if score > best_wins:
                    best_wins = score
                    best_move = move

        # Fallback
        if best_move is None:
            playable = list(plateau.colonnes_jouables)
            # Prefer center columns if possible
            if 3 in playable:
                best_move = 3
            else:
                best_move = random.choice(playable)

        return best_move