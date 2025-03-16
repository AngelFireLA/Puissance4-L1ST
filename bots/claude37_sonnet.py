import random
import time
import math
from collections import defaultdict
from bots.bot import Bot


class AlphaBetaMCTSHybrid(Bot):
    """
    A powerful Connect4 bot that combines alpha-beta pruning with Monte Carlo Tree Search,
    enhanced pattern recognition, and iterative deepening.
    """

    def __init__(self, nom, symbole, profondeur=5, temps_max=0.5):
        super().__init__(nom, symbole)
        self.profondeur = profondeur  # Initial search depth
        self.temps_max = temps_max  # Maximum thinking time per move
        self.table_transposition = {}  # Transposition table for faster search
        self.history_heuristic = defaultdict(int)  # For move ordering
        self.opponent_symbole = 'O' if symbole == 'X' else 'X'

        # Pattern recognition values
        self.pattern_values = {
            (self.symbole, self.symbole, self.symbole, '.'): 500,  # Three in a row with space
            (self.symbole, self.symbole, '.', self.symbole): 500,
            (self.symbole, '.', self.symbole, self.symbole): 500,
            ('.', self.symbole, self.symbole, self.symbole): 500,

            (self.opponent_symbole, self.opponent_symbole, self.opponent_symbole, '.'): 800,  # Block opponent three
            (self.opponent_symbole, self.opponent_symbole, '.', self.opponent_symbole): 800,
            (self.opponent_symbole, '.', self.opponent_symbole, self.opponent_symbole): 800,
            ('.', self.opponent_symbole, self.opponent_symbole, self.opponent_symbole): 800,

            (self.symbole, self.symbole, '.', '.'): 50,  # Two in a row with spaces
            (self.symbole, '.', self.symbole, '.'): 50,
            (self.symbole, '.', '.', self.symbole): 50,
            ('.', self.symbole, self.symbole, '.'): 50,
            ('.', self.symbole, '.', self.symbole): 50,
            ('.', '.', self.symbole, self.symbole): 50,

            (self.opponent_symbole, self.opponent_symbole, '.', '.'): 70,  # Block opponent two
            (self.opponent_symbole, '.', self.opponent_symbole, '.'): 70,
            (self.opponent_symbole, '.', '.', self.opponent_symbole): 70,
            ('.', self.opponent_symbole, self.opponent_symbole, '.'): 70,
            ('.', self.opponent_symbole, '.', self.opponent_symbole): 70,
            ('.', '.', self.opponent_symbole, self.opponent_symbole): 70,
        }

        # MCTS parameters
        self.C = 1.41  # Exploration constant for UCB1

    def trouver_coup(self, plateau, joueur2) -> int:
        """Find the best move using iterative deepening alpha-beta with MCTS rollouts."""
        self.start_time = time.time()
        self.joueur2 = joueur2
        self.table_transposition = {}

        # Check for immediate winning moves
        for col in self.tri_coups(plateau):
            if col in plateau.colonnes_jouables:
                colonne_est_enlevee = plateau.jouer_coup_reversible(col, self.symbole)
                if plateau.est_victoire(col):
                    plateau.annuler_coup(col, colonne_est_enlevee, self.symbole)
                    return col
                plateau.annuler_coup(col, colonne_est_enlevee, self.symbole)

        # Check for opponent immediate winning moves to block
        for col in self.tri_coups(plateau):
            if col in plateau.colonnes_jouables:
                colonne_est_enlevee = plateau.jouer_coup_reversible(col, joueur2.symbole)
                if plateau.est_victoire(col):
                    plateau.annuler_coup(col, colonne_est_enlevee, joueur2.symbole)
                    return col
                plateau.annuler_coup(col, colonne_est_enlevee, joueur2.symbole)

        # For early game, use MCTS to explore more broadly
        early_game_threshold = 10
        total_pieces = sum(plateau.hauteurs_colonnes)
        if total_pieces < early_game_threshold:
            return self.mcts_search(plateau)

        # For mid to late game, use iterative deepening alpha-beta
        return self.iterative_deepening_search(plateau)

    def mcts_search(self, plateau):
        """Monte Carlo Tree Search implementation."""
        root = MCTSNode(plateau, None, None)

        # Run MCTS until time is up
        num_simulations = 0
        while time.time() - self.start_time < self.temps_max * 0.7:  # Use 70% of time for MCTS
            # Selection & Expansion
            node = self.select_node(root)

            # Simulation
            result = self.rollout(node.plateau)

            # Backpropagation
            self.backpropagate(node, result)

            num_simulations += 1

        # Choose the best child
        if not root.children:
            # Fallback if no simulations completed
            return random.choice(list(plateau.colonnes_jouables))

        best_child = max(root.children.values(), key=lambda n: n.visits)
        return best_child.move

    def select_node(self, node):
        """Select a node for expansion using UCB1."""
        current = node

        # Traverse the tree until we find a node that isn't fully expanded
        while current.is_fully_expanded() and not current.is_terminal():
            current = current.select_best_child(self.C)

        # If the node is terminal, return it
        if current.is_terminal():
            return current

        # Otherwise, expand it
        return self.expand(current)

    def expand(self, node):
        """Expand a node by adding a child."""
        # Get the list of unexpanded moves
        unexpanded_moves = node.get_unexpanded_moves()

        if not unexpanded_moves:
            return node

        # Choose a random unexpanded move
        move = random.choice(unexpanded_moves)

        # Create a new plateau for the child node
        child_plateau = node.plateau.copier_grille()
        colonne_est_enlevee = child_plateau.jouer_coup_reversible(move,
                                                                  self.symbole if node.is_my_turn else self.joueur2.symbole)

        # Create a child node
        child = MCTSNode(
            plateau=child_plateau,
            parent=node,
            move=move,
            is_my_turn=not node.is_my_turn,
            is_victory=child_plateau.est_victoire(move)
        )

        # Add the child to the parent
        node.children[move] = child

        return child

    def rollout(self, plateau):
        """Perform a random rollout from a plateau state."""
        sim_plateau = plateau.copier_grille()
        current_player_is_me = True

        while True:
            # Check for end of game
            if not sim_plateau.colonnes_jouables:
                return 0  # Draw

            # Choose a random move
            move = random.choice(list(sim_plateau.colonnes_jouables))

            # Apply the move
            symbole = self.symbole if current_player_is_me else self.joueur2.symbole
            colonne_est_enlevee = sim_plateau.jouer_coup_reversible(move, symbole)

            # Check for victory
            if sim_plateau.est_victoire(move):
                return 1 if current_player_is_me else -1

            # Next player
            current_player_is_me = not current_player_is_me

    def backpropagate(self, node, result):
        """Backpropagate the result up the tree."""
        current = node

        while current is not None:
            current.visits += 1
            # Adjust reward depending on whose turn it was
            adjusted_result = result if not current.is_my_turn else -result
            current.score += adjusted_result
            current = current.parent

    def iterative_deepening_search(self, plateau):
        """Perform iterative deepening alpha-beta search."""
        best_move = random.choice(list(plateau.colonnes_jouables))
        best_score = float('-inf')

        depth = 1
        while time.time() - self.start_time < self.temps_max and depth <= self.profondeur + 6:
            move, score = self.alpha_beta_root(plateau, depth)

            # Update best move if we found a better one
            if score > best_score:
                best_move = move
                best_score = score

            depth += 1

            # If we found a winning move, no need to search deeper
            if best_score > 9000:
                break

        return best_move

    def alpha_beta_root(self, plateau, depth):
        """Alpha beta search from the root position."""
        alpha = float('-inf')
        beta = float('inf')
        best_move = None
        best_score = float('-inf')

        # Try each move in order of predicted strength
        for move in self.tri_coups(plateau, use_history=True):
            if move not in plateau.colonnes_jouables:
                continue

            colonne_est_enlevee = plateau.jouer_coup_reversible(move, self.symbole)

            # Check for immediate win
            if plateau.est_victoire(move):
                plateau.annuler_coup(move, colonne_est_enlevee, self.symbole)
                return move, 10000 + depth

            # Evaluate the position after this move
            score = -self.alpha_beta(plateau, depth - 1, -beta, -alpha, self.joueur2.symbole)
            plateau.annuler_coup(move, colonne_est_enlevee, self.symbole)

            # Update best move if necessary
            if score > best_score:
                best_score = score
                best_move = move

            # Update alpha
            alpha = max(alpha, score)

            # Update history heuristic for move ordering
            self.history_heuristic[(self.symbole, move)] += 2 ** depth

        return best_move, best_score

    def alpha_beta(self, plateau, depth, alpha, beta, symbole):
        """Alpha-beta pruning algorithm."""
        if time.time() - self.start_time > self.temps_max:
            return 0  # Time's up

        # Check for leaf node
        if depth == 0 or not plateau.colonnes_jouables:
            return self.evaluate_position(plateau, symbole)

        # Generate key for transposition table
        key = self.generate_key(plateau)

        # Check transposition table
        if key in self.table_transposition and self.table_transposition[key][0] >= depth:
            return self.table_transposition[key][1]

        original_alpha = alpha
        best_score = float('-inf')

        next_symbole = self.symbole if symbole != self.symbole else self.joueur2.symbole

        # Try each move in order of predicted strength
        for move in self.tri_coups(plateau, use_history=True):
            if move not in plateau.colonnes_jouables:
                continue

            colonne_est_enlevee = plateau.jouer_coup_reversible(move, symbole)

            # Check for victory
            if plateau.est_victoire(move):
                score = 10000 + depth
                plateau.annuler_coup(move, colonne_est_enlevee, symbole)
                return score

            # Recursive call
            score = -self.alpha_beta(plateau, depth - 1, -beta, -alpha, next_symbole)
            plateau.annuler_coup(move, colonne_est_enlevee, symbole)

            # Update best score
            best_score = max(best_score, score)

            # Update alpha
            alpha = max(alpha, score)

            # Update history heuristic for move ordering
            self.history_heuristic[(symbole, move)] += 2 ** depth

            # Beta cutoff
            if alpha >= beta:
                break

        # Store in transposition table
        self.table_transposition[key] = (depth, best_score)

        return best_score

    def evaluate_position(self, plateau, symbole):
        """Evaluate the current board position."""
        # 1. Check for victory
        for col in range(plateau.colonnes):
            if plateau.hauteurs_colonnes[col] > 0 and plateau.est_victoire(col):
                return 10000 if plateau.grille[col][-1] == self.symbole else -10000

        # 2. Check for patterns
        score = 0

        # 2.1 Check horizontal patterns
        for row in range(plateau.lignes):
            for col in range(plateau.colonnes - 3):
                pattern = []
                for i in range(4):
                    if row < plateau.hauteurs_colonnes[col + i]:
                        pattern.append(plateau.grille[col + i][row])
                    else:
                        pattern.append('.')

                pattern_tuple = tuple(pattern)
                if pattern_tuple in self.pattern_values:
                    score += self.pattern_values[pattern_tuple]

        # 2.2 Check vertical patterns
        for col in range(plateau.colonnes):
            for row in range(plateau.lignes - 3):
                pattern = []
                for i in range(4):
                    if row + i < plateau.hauteurs_colonnes[col]:
                        pattern.append(plateau.grille[col][row + i])
                    else:
                        pattern.append('.')

                pattern_tuple = tuple(pattern)
                if pattern_tuple in self.pattern_values:
                    score += self.pattern_values[pattern_tuple]

        # 2.3 Check diagonal patterns (rising)
        for col in range(plateau.colonnes - 3):
            for row in range(plateau.lignes - 3):
                pattern = []
                for i in range(4):
                    if row + i < plateau.hauteurs_colonnes[col + i]:
                        pattern.append(plateau.grille[col + i][row + i])
                    else:
                        pattern.append('.')

                pattern_tuple = tuple(pattern)
                if pattern_tuple in self.pattern_values:
                    score += self.pattern_values[pattern_tuple]

        # 2.4 Check diagonal patterns (falling)
        for col in range(plateau.colonnes - 3):
            for row in range(3, plateau.lignes):
                pattern = []
                for i in range(4):
                    if row - i < plateau.hauteurs_colonnes[col + i]:
                        pattern.append(plateau.grille[col + i][row - i])
                    else:
                        pattern.append('.')

                pattern_tuple = tuple(pattern)
                if pattern_tuple in self.pattern_values:
                    score += self.pattern_values[pattern_tuple]
        # 3. Prefer center columns
        centre = plateau.colonnes // 2
        for col in plateau.colonnes_jouables:
            # Higher value for columns closer to center
            distance_from_center = abs(col - centre)
            center_preference = (plateau.colonnes // 2 - distance_from_center) * 5
            score += center_preference

        # 4. Consider position control and threats
        for col in plateau.colonnes_jouables:
            # Check if placing a piece here would create a winning position
            if col in plateau.colonnes_jouables:
                # Check if my piece creates a win
                colonne_est_enlevee = plateau.jouer_coup_reversible(col, self.symbole)
                if plateau.est_victoire(col):
                    score += 500
                plateau.annuler_coup(col, colonne_est_enlevee, self.symbole)

                # Check if opponent piece creates a win
                colonne_est_enlevee = plateau.jouer_coup_reversible(col, self.opponent_symbole)
                if plateau.est_victoire(col):
                    score -= 800
                plateau.annuler_coup(col, colonne_est_enlevee, self.opponent_symbole)

        return score

    def tri_coups(self, plateau, use_history=False):
        """Order moves for better alpha-beta pruning efficiency."""
        centre = plateau.colonnes // 2
        colonnes = list(plateau.colonnes_jouables)

        # Define a sort key function
        def sort_key(col):
            value = 0

            # Proximity to center (higher is better)
            distance_from_center = abs(col - centre)
            value -= distance_from_center * 10

            # History heuristic (if enabled)
            if use_history:
                value += self.history_heuristic.get((self.symbole, col), 0) / 1000

            # Check if this move would create a win
            if col in plateau.colonnes_jouables:
                colonne_est_enlevee = plateau.jouer_coup_reversible(col, self.symbole)
                if plateau.est_victoire(col):
                    value += 10000  # Prioritize winning moves highest
                plateau.annuler_coup(col, colonne_est_enlevee, self.symbole)

                # Check if opponent would win here
                colonne_est_enlevee = plateau.jouer_coup_reversible(col, self.opponent_symbole)
                if plateau.est_victoire(col):
                    value += 9000  # Prioritize blocking opponent wins second-highest
                plateau.annuler_coup(col, colonne_est_enlevee, self.opponent_symbole)

            return value

        # Sort columns using the key function
        return sorted(colonnes, key=sort_key, reverse=True)

    def generate_key(self, plateau):
        """Generate a unique key for the transposition table."""
        key_parts = []
        for col in range(plateau.colonnes):
            col_str = ''.join(plateau.grille[col])
            key_parts.append(col_str)
        return tuple(key_parts)


class MCTSNode:
    """Node class for the Monte Carlo Tree Search algorithm."""

    def __init__(self, plateau, parent=None, move=None, is_my_turn=True, is_victory=False):
        self.plateau = plateau
        self.parent = parent
        self.move = move
        self.is_my_turn = is_my_turn
        self.is_victory = is_victory
        self.children = {}  # Maps moves to child nodes
        self.visits = 0
        self.score = 0

    def is_fully_expanded(self):
        """Check if all possible moves have been tried from this node."""
        return len(self.children) == len(self.plateau.colonnes_jouables)

    def is_terminal(self):
        """Check if this node represents a terminal state."""
        return self.is_victory or not self.plateau.colonnes_jouables

    def get_unexpanded_moves(self):
        """Get the list of moves that haven't been tried yet."""
        expanded_moves = set(self.children.keys())
        return [move for move in self.plateau.colonnes_jouables if move not in expanded_moves]

    def select_best_child(self, c):
        """Select the best child according to the UCB1 formula."""

        # UCB1 formula: score/visits + c * sqrt(ln(parent_visits)/visits)
        def ucb1(node):
            exploitation = node.score / node.visits if node.visits > 0 else 0
            exploration = c * math.sqrt(math.log(self.visits) / node.visits) if node.visits > 0 else float('inf')
            return exploitation + exploration

        return max(self.children.values(), key=ucb1)