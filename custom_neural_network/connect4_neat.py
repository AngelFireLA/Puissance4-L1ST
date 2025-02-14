import pickle
import random

import neat
import moteur.plateau as plateau
from moteur.joueur import Joueur
from bots import negamaxv5


# --- Helper Function: same as in training ---
def get_move_from_net(net, game_board, my_symbol, opp_symbol):
    input_vector = []
    for row in range(game_board.lignes):
        for col in range(game_board.colonnes):
            if row < len(game_board.grille[col]):
                token = game_board.grille[col][row]
                if token == my_symbol:
                    input_vector.append(1.0)
                elif token == opp_symbol:
                    input_vector.append(-1.0)
                else:
                    input_vector.append(0.0)
            else:
                input_vector.append(0.0)
    outputs = net.activate(input_vector)
    valid_moves = list(game_board.colonnes_jouables)
    if not valid_moves:
        return None
    best_move = max(valid_moves, key=lambda col: outputs[col])
    return best_move


def simulate_game(net, first_player):
    game_board = plateau.Plateau()
    if first_player == 1:
        network_symbol = 'X'
        opponent_symbol = 'O'
    else:
        network_symbol = 'O'
        opponent_symbol = 'X'

    # Dummy player for Negamax opponent.
    dummy = Joueur("Dummy", network_symbol)
    # Instantiate the Negamax opponent (adjust depth if needed)
    opponent_bot = negamaxv5.Negamax5("Negamax", opponent_symbol, profondeur=2)

    current_player = first_player
    move_count = 0
    while True:
        if (first_player == 1 and current_player == 1) or (first_player == 2 and current_player == 2):
            move = get_move_from_net(net, game_board, network_symbol, opponent_symbol)
            if move is None or move not in game_board.colonnes_jouables:
                return -1, move_count  # illegal move penalty
        else:
            move = opponent_bot.trouver_coup(game_board, dummy)
            if move is None or move not in game_board.colonnes_jouables:
                move = random.choice(list(game_board.colonnes_jouables))

        game_board.ajouter_jeton(move, network_symbol if ((first_player == 1 and current_player == 1) or (
                    first_player == 2 and current_player == 2)) else opponent_symbol)
        move_count += 1

        if game_board.est_victoire(move):
            if ((first_player == 1 and current_player == 1) or (first_player == 2 and current_player == 2)):
                return 1, move_count  # network wins
            else:
                return 0, move_count  # network loses
        if game_board.est_nul():
            return 0.5, move_count

        current_player = 2 if current_player == 1 else 1


def evaluate_net(net, num_games=10):
    total_score = 0.0
    for i in range(num_games):
        first_player = 1 if i % 2 == 0 else 2
        result, move_count = simulate_game(net, first_player)
        if result == 1:
            total_score += 1.5 + (42 - move_count) / 42.0
        elif result == 0.5:
            total_score += 0.5
        elif result == 0:
            total_score += 0.0
        elif result == -1:
            total_score += -1.0
    average_score = total_score / num_games
    return average_score


# --- Main Testing Code ---
if __name__ == '__main__':
    # Adjust paths to your genome and config files
    genome_path = r'path/to/winner.pkl'
    config_path = r'path/to/config_feedforward'

    with open(genome_path, 'rb') as f:
        genome = pickle.load(f)

    config = neat.Config(
        neat.DefaultGenome, neat.DefaultReproduction,
        neat.DefaultSpeciesSet, neat.DefaultStagnation,
        config_path
    )

    net = neat.nn.FeedForwardNetwork.create(genome, config)
    avg_fitness = evaluate_net(net, num_games=10)
    print("Average fitness (training-like simulation):", avg_fitness)
