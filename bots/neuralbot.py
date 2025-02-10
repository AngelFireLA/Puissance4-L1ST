import pickle

import neat

from bots.bot import Bot

def vectorize_board(board):
    vector = []
    for col in range(board.colonnes):
        # Get the list of tokens in the current column.
        column_tokens = board.grille[col]
        # Fill the column with its tokens; empty slots are represented by "."
        full_column = column_tokens + ["." for _ in range(board.lignes - board.hauteurs_colonnes[col])]
        # Convert each cell as needed: empty=0, "X"=1, "O"=-1
        vector.extend([0 if cell == "." else 1 if cell == "O" else -1 for cell in full_column])
        #for each column, add 1 if the column isn't full, 0 otherwise
        non_full_columns = board.colonnes_jouables
        vector.append(1 if col in non_full_columns else 0)
    return vector

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
        inputs = vectorize_board(plateau)
        outputs = net.activate(inputs)
        colonne = outputs.index(max(outputs))
        return colonne