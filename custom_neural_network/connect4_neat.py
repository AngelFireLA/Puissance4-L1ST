import random
import pickle
import neat
import os
import moteur.plateau as plateau
from moteur import joueur, partie
from bots import negamaxv5, bot, random_bot


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
            filename = f'genomes/winner12_gen{self.current_generation}.pkl'
            with open(filename, 'wb') as f:
                pickle.dump(best_genome, f)
            print(f"Saved best genome of generation {self.current_generation} to {filename}")


# --- Helper function for converting a board to a neural network input vector ---
def vectorize_board(board: plateau.Plateau):
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



# --- Game simulation function ---
def run_connect4_game(net, gen_counter):
    fitness = 0
    amount_of_games = 10
    for _ in range(amount_of_games):
        partie_test = partie.Partie()
        partie_en_cours = True
        # Set up players: always player 1 is controlled by the genome,
        # and choose an opponent based on the generation counter.
        joueur1 = joueur.Joueur("Joueur 1", "O")
        import random

        # For each generation bracket, define a list of (adversary, weight) pairs.
        if gen_counter <= 50:
            # Early generations: only basic bots available.
            adversaires = [
                (random_bot.RandomBot("Bot", "X"), 1),
                (negamaxv5.Negamax5("Bot", "X", profondeur=1), 1),
                (bot.Bot("Bot", "X"), 1)
            ]
            fitness -= 125
        # else:
        elif gen_counter <= 1500:
            # From 251 to 1000, add the deeper bot with higher weight, but keep the older ones with lower weight.
            adversaires = [
                (random_bot.RandomBot("Bot", "X"), 0.5),
                (negamaxv5.Negamax5("Bot", "X", profondeur=1), 0.3),
                (bot.Bot("Bot", "X"), 1),
                (negamaxv5.Negamax5("Bot", "X", profondeur=2), 5)
            ]
        else:
            adversaires = [
                (random_bot.RandomBot("Bot", "X"), 0.2),
                (negamaxv5.Negamax5("Bot", "X", profondeur=1), 0.1),
                (bot.Bot("Bot", "X"), 0.7),
                (negamaxv5.Negamax5("Bot", "X", profondeur=2), 2),
                (negamaxv5.Negamax5("Bot", "X", profondeur=4), 5)
            ]
        # elif gen_counter <= 6000:
        #     adversaires = [
        #         (random_bot.RandomBot("Bot", "X"), 0.3),
        #         (bot.Bot("Bot", "X"), 0.4),
        #         (negamaxv5.Negamax5("Bot", "X", profondeur=2), 1),
        #         (negamaxv5.Negamax5("Bot", "X", profondeur=4), 2),
        #         (negamaxv5.Negamax5("Bot", "X", profondeur=6), 6)
        #     ]
        # elif gen_counter <= 10000:
        #     adversaires = [
        #         (random_bot.RandomBot("Bot", "X"), 0.2),
        #         (bot.Bot("Bot", "X"), 0.1),
        #         (negamaxv5.Negamax5("Bot", "X", profondeur=4), 1.5),
        #         (negamaxv5.Negamax5("Bot", "X", profondeur=6), 2),
        #         (negamaxv5.Negamax5("Bot", "X", profondeur=8), 7)
        #     ]
        # elif gen_counter <= 15000:
        #     adversaires = [
        #         (random_bot.RandomBot("Bot", "X"), 0.1),
        #         (bot.Bot("Bot", "X"), 0.1),
        #         (negamaxv5.Negamax5("Bot", "X", profondeur=8), 3),
        #         (negamaxv5.Negamax5("Bot", "X", profondeur=10), 9)
        #     ]
        # else:
        #     # After 15000 generations, only the best bots are used.
        #     adversaires = [
        #         (random_bot.RandomBot("Bot", "X"), 0.1),
        #         (bot.Bot("Bot", "X"), 0.1),
        #         (negamaxv5.Negamax5("Bot", "X", profondeur=8), 2),
        #         (negamaxv5.Negamax5("Bot", "X", profondeur=10), 4),
        #         (negamaxv5.Negamax5("Bot", "X", profondeur=12), 10)
        #     ]

        # Unpack the bots and weights.
        bots, weights = zip(*adversaires)
        # Use weighted random selection (random.choices returns a list, so take the first element).
        joueur2 = random.choices(bots, weights=weights, k=1)[0]

        partie_test.ajouter_joueur(joueur1)
        partie_test.ajouter_joueur(joueur2)
        partie_test.tour_joueur = random.randint(1, 2)

        while partie_en_cours:
            if partie_test.tour_joueur == 1:
                inputs = vectorize_board(partie_test.plateau)
                outputs = net.activate(inputs)
                # Get a list of column indices sorted by output (highest first)
                sorted_columns = sorted(range(len(outputs)), key=lambda i: outputs[i], reverse=True)

                # Find the first valid move in the sorted order and compute the penalty
                valid_choice = None
                for rank, col in enumerate(sorted_columns):
                    if col in partie_test.plateau.colonnes_jouables:
                        valid_choice = col
                        break
                    else:
                        fitness -= rank*-5
                colonne = valid_choice
            else:
                colonne = joueur2.trouver_coup(partie_test.plateau, joueur1)

            if partie_test.jouer(colonne, partie_test.tour_joueur):

                if partie_test.plateau.est_victoire(colonne):
                    bonus = (100 - partie_test.tour)
                    malus = (-100 + partie_test.tour)
                    fitness += bonus if partie_test.tour_joueur == 1 else malus
                    break
                elif partie_test.plateau.est_nul():
                    break
                # Switch turn:
                partie_test.tour_joueur = 2 if partie_test.tour_joueur == 1 else 1
            else:
                print("Invalid move encountered")
                break
    return fitness/amount_of_games



def eval_genome(genome, config, gen_counter):
    net = neat.nn.FeedForwardNetwork.create(genome, config)
    fitness = run_connect4_game(net, gen_counter)  # run a game (or several) and get fitness
    return fitness



# --- Main run function ---
def run(config_file):
    config = neat.Config(
        neat.DefaultGenome, neat.DefaultReproduction,
        neat.DefaultSpeciesSet, neat.DefaultStagnation,
        config_file
    )
    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    thresholds = [i*100 for i in range(1, 51)]
    p.add_reporter(SaveIntermediateReporter(thresholds))

    num_workers = os.cpu_count()  # or use max(1, os.cpu_count() - 1)
    pe = neat.ParallelEvaluator(num_workers, eval_genome)
    winner = p.run(pe.evaluate, 50000)

    #save best genome
    with open('genomes/winner12.pkl', 'wb') as f:
        pickle.dump(winner, f)

    print('\nBest genome:\n{!s}'.format(winner))
    return winner


if __name__ == '__main__':
    # Determine the path to your configuration file.
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config_feedforward')
    run(config_path)
