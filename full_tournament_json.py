import time
import concurrent.futures
import itertools
import random
from datetime import datetime
import os
import json  # Changed from pickle
from tqdm import tqdm

# Assuming these are correctly set up by the user
# You need to ensure 'elo_tournament_setup.py' exists and defines 'participants'
# 'participants' should be a list of bot template instances.
# Example: participants = [negamax.Negamax("Nega_P3", "?", profondeur=3), random_bot.RandomBot("Rando", "?")]
from elo_tournament_setup import participants

# Game engine
from moteur.partie import Partie

# Import all bot classes that might be in `participants`
# Ensure all bot classes used in 'participants' are imported here.


# Add any other custom bot classes if they are part of `participants`


def create_bot_instance(bot_template):
    """
    Create a new instance of a bot from a template.
    This is crucial for ensuring each game uses a fresh, independent bot.
    """
    bot_class = bot_template.__class__
    # The 'nom' is copied from the template. 'symbole' is temporarily '?'
    # and will be set correctly ('O' or 'X') before each game.
    if hasattr(bot_template, 'profondeur') and hasattr(bot_template, 'temps_max'):
        return bot_class(bot_template.nom, "?", profondeur=bot_template.profondeur, temps_max=bot_template.temps_max)
    elif hasattr(bot_template, 'profondeur'):
        return bot_class(bot_template.nom, "?", profondeur=bot_template.profondeur)
    elif hasattr(bot_template, 'model_path'):  # For NeuralBot or similar
        return bot_class(bot_template.nom, "?", model_path=bot_template.model_path)
    else:  # For basic bots like RandomBot or a default Bot
        return bot_class(bot_template.nom, "?")


def une_partie(bot_instance_1, bot_instance_2, first_player_is_bot1):
    """
    Play a single game between two provided bot INSTANCES.
    - bot_instance_1, bot_instance_2: Freshly created bot objects for this game.
    - first_player_is_bot1: Boolean, True if bot_instance_1 should play first (as 'O').
    Returns a dictionary with detailed game results.
    """
    partie = Partie()

    if first_player_is_bot1:
        player1_instance, player2_instance = bot_instance_1, bot_instance_2
    else:
        # bot_instance_2 plays first
        player1_instance, player2_instance = bot_instance_2, bot_instance_1

    # Player1 (the one who starts) is always 'O'
    player1_instance.symbole = "O"
    player2_instance.symbole = "X"

    partie.ajouter_joueur(player1_instance)  # partie.joueurs[0] will be player1_instance
    partie.ajouter_joueur(player2_instance)  # partie.joueurs[1] will be player2_instance
    partie.tour_joueur = 1  # Player1 (joueurs[0]) starts

    moves_count = 0
    start_time = time.time()
    winner_name = "draw"  # Default outcome

    while True:
        moves_count += 1

        current_player_logic_instance = partie.joueurs[partie.tour_joueur - 1]
        opponent_logic_instance = partie.joueurs[1 if partie.tour_joueur == 1 else 0]

        try:
            colonne = current_player_logic_instance.trouver_coup(partie.plateau, opponent_logic_instance)
        except Exception as e:
            print(f"\nERROR during 'trouver_coup' for {current_player_logic_instance.nom}: {e}. "
                  f"Opponent {opponent_logic_instance.nom} wins by default.")
            winner_name = opponent_logic_instance.nom
            break  # End game

        if partie.jouer(colonne, partie.tour_joueur):  # True if move is valid and played
            if partie.plateau.est_victoire(colonne):
                winner_name = current_player_logic_instance.nom
                break  # End game
            if partie.plateau.est_nul():
                winner_name = "draw"
                break  # End game
            # Switch turn
            partie.tour_joueur = 2 if partie.tour_joueur == 1 else 1
        else:  # Invalid move made by current_player_logic_instance
            print(f"\nINVALID MOVE by {current_player_logic_instance.nom}. "
                  f"Opponent {opponent_logic_instance.nom} wins by default.")
            winner_name = opponent_logic_instance.nom
            break  # End game

    game_time_seconds = time.time() - start_time

    return {
        "player_O_name": player1_instance.nom,  # Actual name of the bot that played 'O' (started)
        "player_X_name": player2_instance.nom,  # Actual name of the bot that played 'X'
        "winner_name": winner_name,  # Name of the winner, or "draw"
        "moves": moves_count,
        "time_seconds": game_time_seconds,
    }


def jouer_match(bot1_template, bot2_template, num_games_per_match=2):
    """
    Play a match (a series of games) between two bot TEMPLATES.
    In a match, bots typically alternate starting positions.
    Returns a list of individual game result dictionaries from this match.
    """
    match_game_results = []

    for i in range(num_games_per_match):
        # Create fresh bot instances for EACH game to prevent state leakage
        bot1_game_instance = create_bot_instance(bot1_template)
        bot2_game_instance = create_bot_instance(bot2_template)

        # Alternate who starts:
        # If i is even, bot1_template's instance starts.
        # If i is odd, bot2_template's instance starts.
        current_game_starts_with_bot1_template = (i % 2 == 0)

        single_game_result_data = une_partie(
            bot1_game_instance,
            bot2_game_instance,
            first_player_is_bot1=current_game_starts_with_bot1_template
        )

        # Create a canonical representation of the pair for this match
        # This helps in grouping games belonging to the same bot-vs-bot contest.
        # Names are sorted alphabetically.
        match_pair_sorted_names = tuple(sorted((bot1_template.nom, bot2_template.nom)))

        game_record = {
            "match_participant_1": match_pair_sorted_names[0],
            "match_participant_2": match_pair_sorted_names[1],
            "game_in_match_id": i,  # e.g., 0 for 1st game in match, 1 for 2nd
            "player_O": single_game_result_data["player_O_name"],
            "player_X": single_game_result_data["player_X_name"],
            "winner": single_game_result_data["winner_name"],
            "moves": single_game_result_data["moves"],
            "time_seconds": single_game_result_data["time_seconds"]
        }
        match_game_results.append(game_record)

    return match_game_results


def run_tournament_and_save_results(participants_templates_list, num_games_per_match=2, max_workers=20):
    """
    Runs a round-robin tournament: each unique pair of bots plays a match.
    All individual game results are collected and saved to a single JSON file.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = f"tournament_raw_games_{timestamp}"
    os.makedirs(results_dir, exist_ok=True)
    results_filename = os.path.join(results_dir, f"all_games_results_{timestamp}.json")

    all_individual_game_results = []
    game_global_id_counter = 0

    # Create all unique pairings from the list of bot templates
    unique_pairings = list(itertools.combinations(participants_templates_list, 2))
    random.shuffle(unique_pairings)  # Shuffle for better progress distribution with tqdm

    num_total_matches = len(unique_pairings)
    num_total_games_expected = num_total_matches * num_games_per_match

    print(f"Starting Tournament Data Collection:")
    print(f"  Number of bot templates: {len(participants_templates_list)}")
    print(f"  Number of unique matches (pairs): {num_total_matches}")
    print(f"  Number of games per match: {num_games_per_match}")
    print(f"  Total games to be played: {num_total_games_expected}")
    print("-" * 30)

    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all matches to the executor pool
        future_to_match_templates_pair = {
            executor.submit(jouer_match, bot1_template, bot2_template, num_games_per_match): (
            bot1_template, bot2_template)
            for bot1_template, bot2_template in unique_pairings
        }

        # Process results as they are completed
        for future in tqdm(concurrent.futures.as_completed(future_to_match_templates_pair), total=num_total_matches,
                           desc="Processing Matches"):
            original_bot1_template, original_bot2_template = future_to_match_templates_pair[future]
            try:
                games_played_in_match = future.result()  # This is a list of game_record dicts
                for game_record in games_played_in_match:
                    game_record["game_global_id"] = game_global_id_counter
                    all_individual_game_results.append(game_record)
                    game_global_id_counter += 1
            except Exception as e:
                # This catches errors if a whole 'jouer_match' call fails
                print(
                    f"\nCRITICAL ERROR: Match between {original_bot1_template.nom} and {original_bot2_template.nom} failed entirely: {e}")
                # Optionally, log this error or add placeholder error records for these games.
                # For now, games from a failed match are simply not added to the results.

    # Sort results by global game ID for consistent output, though not strictly necessary
    all_individual_game_results.sort(key=lambda x: x["game_global_id"])

    # Save all collected game results to the JSON file
    with open(results_filename, 'w') as f:
        json.dump(all_individual_game_results, f, indent=2)

    print("\n" + "-" * 30)
    print(f"Tournament data collection finished.")
    print(f"  {len(all_individual_game_results)} games recorded.")
    if len(all_individual_game_results) != num_total_games_expected:
        print(
            f"  WARNING: Expected {num_total_games_expected} games, but recorded {len(all_individual_game_results)}. Some games/matches might have failed.")
    print(f"Raw game results saved to: {results_filename}")

    return results_filename, all_individual_game_results


def main():
    # `participants` is imported from `elo_tournament_setup.py`
    # It should be a list of bot *template* instances.

    print("=== Connect Four Bot Tournament: Data Collection Phase ===")
    if not participants:
        print("\nERROR: The `participants` list is empty or not loaded.")
        print("Please ensure `elo_tournament_setup.py` exists and defines the `participants` list correctly.")
        return

    print(f"\nLoaded {len(participants)} bot templates for the tournament:")
    for i, p_bot_template in enumerate(participants):
        print(f"  {i + 1}. Name: '{p_bot_template.nom}', Class: {p_bot_template.__class__.__name__}")
    print("-" * 30)

    tournament_start_time = time.time()

    # Configure and run the tournament
    # `num_games_per_match=2` means each bot in a pair gets to start one game.
    # `max_workers=None` uses os.cpu_count(). Set to 1 for sequential execution (easier debugging).
    results_file, collected_games = run_tournament_and_save_results(
        participants_templates_list=participants,
        num_games_per_match=2,
        max_workers=20
    )

    tournament_end_time = time.time()
    total_duration_seconds = tournament_end_time - tournament_start_time
    print(
        f"\nTotal tournament duration: {total_duration_seconds:.2f} seconds ({total_duration_seconds / 60:.2f} minutes).")

    if collected_games:
        print(f"\nNext steps: Analyze the JSON file '{results_file}' to:")
        print("  - Calculate Elo ratings based on individual game outcomes.")
        print("  - Generate win/loss/draw statistics for each bot and pair.")
        print("  - Create visualizations and leaderboards.")
    else:
        print("\nNo games were recorded. Please check for errors during the tournament.")
    print("==========================================================")


if __name__ == "__main__":
    # Important: Ensure that your Python environment can find the necessary modules:
    # - `elo_tournament_setup.py` (for the `participants` list)
    # - `moteur.partie` (for the `Partie` class)
    # - `bots` (package containing your bot implementations like `negamax.py`, `random_bot.py`, etc.)
    #
    # If this script is in a subdirectory (e.g., `project_root/scripts/`), and your modules
    # are in `project_root/` or `project_root/moteur/`, `project_root/bots/`,
    # you might need to:
    #  1. Run this script from `project_root` using `python -m scripts.your_script_name`
    #  2. Or, adjust `sys.path` if necessary (though direct modification is often discouraged).
    #  3. Or, structure your project as a package.
    # For simplicity, this script assumes it's run from a location where imports resolve correctly.
    main()