import pickle
import random

import neat

from bots.bot import Bot

def get_move_from_net(net, game_board, my_symbol, opp_symbol):
    """
    Convert the board into 42 inputs:
      - 1.0 for cells with my_symbol,
      - -1.0 for cells with opp_symbol,
      - 0.0 for empty.
    Then, activate the network and choose the valid move (column)
    with the highest output.
    """
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
    # Choose the valid move with the highest output value.
    best_move = max(valid_moves, key=lambda col: outputs[col])
    # (This check is just in case—best_move should always be valid here.)
    if best_move not in valid_moves:
        return None
    return best_move



def load_genome(genome_file):
    with open(genome_file, 'rb') as f:
        genome = pickle.load(f)
    return genome

class NeuralBot(Bot):
    def __init__(self, name, symbole, model_path, config_path):
        super().__init__(name, symbole)
        self.model_path = model_path
        self.genome = load_genome(model_path)
        self.config = neat.Config(
        neat.DefaultGenome, neat.DefaultReproduction,
        neat.DefaultSpeciesSet, neat.DefaultStagnation,
        config_path
    )

    def trouver_coup(self, plateau, joueur2):
        net = neat.nn.FeedForwardNetwork.create(self.genome, self.config)
        return get_move_from_net(net, plateau, self.symbole, joueur2.symbole)

