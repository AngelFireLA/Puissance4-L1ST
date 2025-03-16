import math
import pickle

import neat

from bots.bot import Bot

def vectorize_board(board):
    vector = []
    column_states = []
    for col in range(board.colonnes):
        # Get the list of tokens in the current column.
        column_tokens = board.grille[col]
        # Fill the column with its tokens; empty slots are represented by "."
        full_column = column_tokens + ["." for _ in range(board.lignes - board.hauteurs_colonnes[col])]
        # Convert each cell as needed: empty=0, "X"=1, "O"=-1
        vector.extend([0 if cell == "." else 1 if cell == "O" else -1 for cell in full_column])
        #for each column, add 1 if the column isn't full, 0 otherwise
        non_full_columns = board.colonnes_jouables
        column_states.append(1 if col in non_full_columns else 0)
    return vector + column_states



def load_genome(genome_file):
    with open(genome_file, 'rb') as f:
        genome = pickle.load(f)
    return genome

def elu_activation(x):
    alpha = 1.0  # You can adjust this constant as needed
    return x if x > 0 else alpha * (math.exp(x) - 1)

def leaky_relu_activation(x):
    alpha = 0.01  # You can adjust this constant as needed
    return x if x > 0 else alpha * x

def selu_activation(x):
    alpha = 1.6732632423543773
    scale = 1.0507009873554805
    return scale * x if x > 0 else scale * alpha * (math.exp(x) - 1)

def gelu_activation(x):
    return x * 0.5 * (1 + math.erf(x / math.sqrt(2)))

class NeuralBot(Bot):
    def __init__(self, name, symbole, model_path, config_path=r"C:\Dev\Python\Puissance4-L1ST\custom_neural_network\config_feedforward"):
        super().__init__(name, symbole)
        self.model_path = model_path
        self.genome = load_genome(model_path)
        self.config = neat.Config(
            neat.DefaultGenome, neat.DefaultReproduction,
            neat.DefaultSpeciesSet, neat.DefaultStagnation,
            config_path
        )
        self.config.genome_config.add_activation('elu', elu_activation)
        self.config.genome_config.add_activation('leaky_relu', leaky_relu_activation)
        self.config.genome_config.add_activation('selu', selu_activation)
        self.config.genome_config.add_activation('gelu', gelu_activation)


    def trouver_coup(self, plateau, joueur2):
        net = neat.nn.FeedForwardNetwork.create(self.genome, self.config)
        inputs = vectorize_board(plateau)
        outputs = net.activate(inputs)

        # Get a list of column indices sorted by output (highest first)
        sorted_columns = sorted(range(len(outputs)), key=lambda i: outputs[i], reverse=True)

        # Return the highest-ranked column that is playable.
        for col in sorted_columns:
            if col in plateau.colonnes_jouables:
                return col

        # Fallback: if somehow no column is playable, return the best column (should not occur in a valid game state)
        return sorted_columns[0]

