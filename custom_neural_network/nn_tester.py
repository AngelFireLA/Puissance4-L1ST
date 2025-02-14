import random
import pickle
import neat
import moteur.plateau as plateau
from moteur.joueur import Joueur
from bots import negamaxv5


def get_move_from_net(net, game_board, my_symbol, opp_symbol):
    """
    Convert the board into 42 inputs:
      - 1.0 for cells with my_symbol,
      - -1.0 for cells with opp_symbol,
      - 0.0 for empty.
    Then, the network is activated and the valid move with the highest output is chosen.
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
    best_move = max(valid_moves, key=lambda col: outputs[col])
    return best_move


def simulate_game(net, first_player, network_symbol, opponent_symbol, opponent_bot):
    """
    Simulate one game of Connect 4 between the network and the Negamax opponent.

    Parameters:
      - net: the trained network.
      - first_player: 1 if the network moves first, 2 if second.
      - network_symbol: the token for the network (e.g., "X").
      - opponent_symbol: the token for the opponent (e.g., "O").
      - opponent_bot: an instance of Negamax5 controlling the opponent.

    Returns:
      - result: 1 for network win, 0 for network loss, 0.5 for draw, -1 for illegal move.
      - move_count: the number of moves made.
    """
    network_symbol = 'O'
    opponent_symbol = 'X'
    opponent_bot = negamaxv5.Negamax5("Negamax", opponent_symbol, profondeur=2)
    game_board = plateau.Plateau()
    current_player = first_player  # 1: network's turn, 2: opponent's turn
    move_count = 0
    dummy = Joueur("Dummy", network_symbol)

    while True:
        if current_player == 1:
            # Network's turn
            move = get_move_from_net(net, game_board, network_symbol, opponent_symbol)
            symbol = network_symbol
            if move is None or move not in game_board.colonnes_jouables:
                return -1, move_count  # Illegal move
        else:
            # Opponent's turn (using Negamax)
            move = opponent_bot.trouver_coup(game_board, dummy)
            if move is None or move not in game_board.colonnes_jouables:
                move = random.choice(list(game_board.colonnes_jouables))
            symbol = opponent_symbol

        game_board.ajouter_jeton(move, symbol)
        move_count += 1

        if game_board.est_victoire(move):
            if current_player == 1:
                return 1, move_count  # Network wins
            else:
                return 0, move_count  # Network loses
        if game_board.est_nul():
            return 0.5, move_count

        current_player = 2 if current_player == 1 else 1


def test_network(net, opponent_depth=2, num_games=10, network_plays_as="O"):
    """
    Test the trained network over num_games using the training scenario.

    The network plays 10 games (alternating first move) against a Negamax opponent.
    The reward for each game is computed as:
      - Win: 1.5 + (42 - move_count) / 42
      - Draw: 0.5
      - Loss: 0
      - Illegal move: -1
    """
    # Set opponent symbol opposite to the network's symbol.
    opponent_symbol = "X"
    # Instantiate Negamax opponent with specified search depth.
    opponent_bot = negamaxv5.Negamax5("Negamax", opponent_symbol, profondeur=opponent_depth)

    total_reward = 0.0
    wins = draws = losses = illegal = 0

    for i in range(num_games):
        # Alternate who goes first.
        first_player = 1 if i % 2 == 0 else 2
        result, moves = simulate_game(net, first_player, network_plays_as, opponent_symbol, opponent_bot)

        # Compute reward as in training.
        if result == 1:
            reward = 1.5 + (42 - moves) / 42.0
            wins += 1
        elif result == 0.5:
            reward = 0.5
            draws += 1
        elif result == 0:
            reward = 0.0
            losses += 1
        else:  # Illegal move
            reward = -1.0
            illegal += 1
        total_reward += reward

    avg_reward = total_reward / num_games
    print(f"Over {num_games} games:")
    print(f"  Wins: {wins}, Draws: {draws}, Losses: {losses}, Illegal moves: {illegal}")
    print(f"  Average reward: {avg_reward:.3f}")


if __name__ == "__main__":
    # Update these paths to point to your trained genome and NEAT configuration.
    model_path = r"genomes/winner8.pkl"
    config_path = r"config_feedforward.txt"

    # Load the trained genome.
    with open(model_path, "rb") as f:
        genome = pickle.load(f)

    config = neat.Config(
        neat.DefaultGenome, neat.DefaultReproduction,
        neat.DefaultSpeciesSet, neat.DefaultStagnation,
        config_path
    )
    net = neat.nn.FeedForwardNetwork.create(genome, config)
    test_network(net, opponent_depth=4, num_games=100, network_plays_as="O")
