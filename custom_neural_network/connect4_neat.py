import random
import pickle
import neat
import os
import moteur.plateau as plateau
from moteur import joueur, partie
from bots import negamaxv3, bot, random_bot


# --- Custom Reporter for Saving Intermediate Best Genomes ---
class SaveIntermediateReporter(neat.reporting.BaseReporter):
    def __init__(self, thresholds):
        # thresholds: a collection of generation numbers at which to save
        self.thresholds = set(thresholds)
        self.current_generation = None

    def start_generation(self, generation):
        # Save the current generation number
        self.current_generation = generation

    def post_evaluate(self, config, population, species, best_genome):
        if self.current_generation in self.thresholds:
            filename = f'winner_gen{self.current_generation}.pkl'
            with open(filename, 'wb') as f:
                pickle.dump(best_genome, f)
            print(f"Saved best genome of generation {self.current_generation} to {filename}")


# --- Helper function for converting a board to a neural network input vector ---
def vectorize_board(board: plateau.Plateau):
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


# --- Fitness evaluation function ---
def eval_genomes(genomes, config):
    global gen_counter
    gen_counter += 1
    for genome_id, genome in genomes:
        # Create the network from genome
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        fitness = run_connect4_game(net)  # simulate one game and return a fitness score
        genome.fitness = fitness


# --- Game simulation function ---
def run_connect4_game(net):
    fitness = 0
    for _ in range(20):
        partie_test = partie.Partie()
        partie_en_cours = True

        # Set up players: always player 1 is controlled by the genome,
        # and choose an opponent based on the generation counter.
        joueur1 = joueur.Joueur("Joueur 1", "X")
        if gen_counter <= 50:
            joueur2 = negamaxv3.Negamax3("Bot", "O", profondeur=2)
        elif gen_counter <= 400:
            joueur2 = negamaxv3.Negamax3("Bot", "O", profondeur=4)
        elif gen_counter <= 500:
            joueur2 = negamaxv3.Negamax3("Bot", "O", profondeur=4, temps_max=0.01)
        elif gen_counter <= 600:
            joueur2 = negamaxv3.Negamax3("Bot", "O", profondeur=4, temps_max=0.025)
        elif gen_counter <= 700:
            joueur2 = negamaxv3.Negamax3("Bot", "O", profondeur=6, temps_max=0.025)
        elif gen_counter <= 800:
            joueur2 = negamaxv3.Negamax3("Bot", "O", profondeur=4, temps_max=0.1)
        elif gen_counter <= 900:
            joueur2 = negamaxv3.Negamax3("Bot", "O", profondeur=6, temps_max=0.1)
        else:
            joueur2 = negamaxv3.Negamax3("Bot", "O", profondeur=8, temps_max=0.1)

        partie_test.ajouter_joueur(joueur1)
        partie_test.ajouter_joueur(joueur2)
        partie.tour_joueur = random.randint(1, 2)

        while partie_en_cours:
            if partie_test.tour_joueur == 1:
                inputs = vectorize_board(partie_test.plateau)
                outputs = net.activate(inputs)
                colonne = outputs.index(max(outputs))
                if colonne not in partie_test.plateau.colonnes_jouables:
                    fitness -= 125*5
                    break
            else:
                colonne = joueur2.trouver_coup(partie_test.plateau, joueur1)

            if partie_test.jouer(colonne, partie_test.tour_joueur):

                if partie_test.plateau.est_victoire(colonne):
                    bonus = (100 - partie_test.tour)*5
                    malus = (-100 + partie_test.tour)*5
                    fitness += bonus if partie_test.tour_joueur == 1 else malus
                    break
                elif partie_test.plateau.est_nul():
                    break
                # Switch turn:
                partie_test.tour_joueur = 2 if partie_test.tour_joueur == 1 else 1
            else:
                print("Invalid move encountered")
                break
    return fitness


gen_counter = 0


# --- Main run function ---
def run(config_file):
    global gen_counter
    # Load configuration from file.
    config = neat.Config(
        neat.DefaultGenome, neat.DefaultReproduction,
        neat.DefaultSpeciesSet, neat.DefaultStagnation,
        config_file
    )

    # Create the population.
    p = neat.Population(config)

    # Add reporters: standard output and statistics.
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    # Add our custom reporter to save best genomes at our thresholds.
    thresholds = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 6000, 7000, 8000, 9000, 10000]
    p.add_reporter(SaveIntermediateReporter(thresholds))

    gen_counter = 0
    # Run evolution for 300 generations.
    winner = p.run(eval_genomes, 10000)

    print('\nBest genome:\n{!s}'.format(winner))
    return winner


if __name__ == '__main__':
    # Determine the path to your configuration file.
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config_feedforward')
    run(config_path)
