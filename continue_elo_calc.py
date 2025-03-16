import time
import copy
import concurrent.futures
import itertools
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
from tqdm import tqdm
from datetime import datetime
import os
import pickle
import glob
from elo_tournament_setup import participants
from elo_calc import (une_partie, create_bot_instance, calculate_elo_change, get_bot_type,
                      get_bot_depth, get_bot_time, get_neural_generation, generate_visualizations)


def load_previous_results(previous_results_dir):
    """Load previous tournament results from the specified directory"""
    # Find the most recent results file (either final or intermediate)
    final_results_path = os.path.join(previous_results_dir, "final_results.pkl")
    intermediate_results_path = os.path.join(previous_results_dir, "intermediate_results.pkl")

    if os.path.exists(final_results_path):
        with open(final_results_path, 'rb') as f:
            return pickle.load(f)
    elif os.path.exists(intermediate_results_path):
        with open(intermediate_results_path, 'rb') as f:
            return pickle.load(f)
    else:
        raise FileNotFoundError(f"No results files found in {previous_results_dir}")


def identify_new_bots(previous_results, current_participants):
    """Identify which bots in the current participants list are new"""
    previous_bot_names = set(previous_results['elo_ratings'].keys())
    current_bot_names = {bot.nom for bot in current_participants}

    new_bot_names = current_bot_names - previous_bot_names
    previous_bot_names_still_present = previous_bot_names.intersection(current_bot_names)

    # Create mapping from bot names to bot objects
    bot_name_to_object = {bot.nom: bot for bot in current_participants}

    new_bots = [bot_name_to_object[name] for name in new_bot_names]
    existing_bots = [bot_name_to_object[name] for name in previous_bot_names_still_present]

    return new_bots, existing_bots


def create_match_key(bot1_name, bot2_name):
    """Create a consistent match key regardless of the order of bots"""
    return tuple(sorted([bot1_name, bot2_name]))


def identify_completed_matches(previous_results):
    """Create a set of completed match keys from previous results"""
    completed_matches = set()

    for match in previous_results['match_results']:
        match_key = create_match_key(match['bot1'], match['bot2'])
        completed_matches.add(match_key)

    return completed_matches


def jouer_match(bot1_template, bot2_template, num_games=2):
    """Play a match of multiple games between two bots"""
    results = {"bot1_wins": 0, "bot2_wins": 0, "draws": 0, "total_moves": 0, "total_time": 0}

    for i in range(num_games):
        # Alternate who goes first
        if i % 2 == 0:
            game_result = une_partie(bot1_template, bot2_template)
        else:
            game_result = une_partie(bot2_template, bot1_template)
            # Invert the result since we swapped the bots
            if game_result["result"] == "bot1":
                game_result["result"] = "bot2"
            elif game_result["result"] == "bot2":
                game_result["result"] = "bot1"

        results["total_moves"] += game_result["moves"]
        results["total_time"] += game_result["time"]

        if game_result["result"] == "bot1":
            results["bot1_wins"] += 1
        elif game_result["result"] == "bot2":
            results["bot2_wins"] += 1
        else:
            results["draws"] += 1

    return results


def continue_tournament(previous_results_dir, participants, num_games_per_match=2, max_workers=None):
    """Continue the tournament with new bots, reusing results for existing bots"""
    # Create a results directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = f"tournament_results_{timestamp}"
    os.makedirs(results_dir, exist_ok=True)

    # Load previous results
    print(f"Loading previous results from {previous_results_dir}...")
    previous_results = load_previous_results(previous_results_dir)

    # Identify new bots and existing bots
    new_bots, existing_bots = identify_new_bots(previous_results, participants)
    print(f"Found {len(new_bots)} new bots and {len(existing_bots)} existing bots")

    if len(new_bots) == -1:
        print("No new bots found. Nothing to do.")
        return previous_results['elo_ratings'], previous_results['match_results'], previous_results['bot_stats']

    # Get completed matches
    completed_matches = identify_completed_matches(previous_results)
    print(f"Loaded {len(completed_matches)} completed matches from previous results")

    # Initialize with previous data
    elo_ratings = copy.deepcopy(previous_results['elo_ratings'])
    match_results = copy.deepcopy(previous_results['match_results'])
    bot_stats = copy.deepcopy(previous_results['bot_stats'])

    # Initialize data for new bots
    for bot in new_bots:
        elo_ratings[bot.nom] = 1000
        bot_stats[bot.nom] = {
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "type": get_bot_type(bot.nom),
            "depth": get_bot_depth(bot.nom),
            "time_limit": get_bot_time(bot.nom),
            "neural_gen": get_neural_generation(bot.nom),
            "total_moves": 0,
            "total_time": 0,
            "matches_played": 0
        }
    # recalculate bot type for existing bots
    for bot in existing_bots:
        bot_stats[bot.nom]["type"] = get_bot_type(bot.nom)
    # Create pairings for new bots
    new_vs_existing_pairings = [(new_bot, existing_bot)
                                for new_bot in new_bots
                                for existing_bot in existing_bots]

    new_vs_new_pairings = list(itertools.combinations(new_bots, 2))

    all_pairings = new_vs_existing_pairings + new_vs_new_pairings
    random.shuffle(all_pairings)

    print(f"Created {len(all_pairings)} new pairings to run")
    print(f"- {len(new_vs_existing_pairings)} new vs existing bot matches")
    print(f"- {len(new_vs_new_pairings)} new vs new bot matches")

    # Run new matches in parallel
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_match = {
            executor.submit(jouer_match, bot1, bot2, num_games=num_games_per_match): (bot1, bot2)
            for bot1, bot2 in all_pairings
        }

        for i, future in enumerate(tqdm(concurrent.futures.as_completed(future_to_match), total=len(all_pairings))):
            bot1, bot2 = future_to_match[future]
            try:
                result = future.result()

                # Extract match data
                bot1_name = bot1.nom
                bot2_name = bot2.nom
                bot1_wins = result["bot1_wins"]
                bot2_wins = result["bot2_wins"]
                draws = result["draws"]
                total_moves = result["total_moves"]
                total_time = result["total_time"]

                # Update stats
                bot_stats[bot1_name]["matches_played"] += 1
                bot_stats[bot2_name]["matches_played"] += 1
                bot_stats[bot1_name]["wins"] += bot1_wins
                bot_stats[bot2_name]["wins"] += bot2_wins
                bot_stats[bot1_name]["losses"] += bot2_wins
                bot_stats[bot2_name]["losses"] += bot1_wins
                bot_stats[bot1_name]["draws"] += draws
                bot_stats[bot2_name]["draws"] += draws
                bot_stats[bot1_name]["total_moves"] += total_moves
                bot_stats[bot2_name]["total_moves"] += total_moves
                bot_stats[bot1_name]["total_time"] += total_time
                bot_stats[bot2_name]["total_time"] += total_time

                # Store match result
                match_result = {
                    "bot1": bot1_name,
                    "bot2": bot2_name,
                    "bot1_wins": bot1_wins,
                    "bot2_wins": bot2_wins,
                    "draws": draws,
                    "total_moves": total_moves,
                    "total_time": total_time,
                    "bot1_type": bot_stats[bot1_name]["type"],
                    "bot2_type": bot_stats[bot2_name]["type"],
                }
                match_results.append(match_result)

                # Calculate Elo changes
                old_elo_1 = elo_ratings[bot1_name]
                old_elo_2 = elo_ratings[bot2_name]

                # Each game contributes to Elo
                for j in range(bot1_wins):
                    elo_change = calculate_elo_change(old_elo_1, old_elo_2, "win")
                    elo_ratings[bot1_name] += elo_change
                    elo_ratings[bot2_name] -= elo_change

                for j in range(bot2_wins):
                    elo_change = calculate_elo_change(old_elo_1, old_elo_2, "loss")
                    elo_ratings[bot1_name] += elo_change
                    elo_ratings[bot2_name] -= elo_change

                for j in range(draws):
                    elo_change = calculate_elo_change(old_elo_1, old_elo_2, "draw")
                    elo_ratings[bot1_name] += elo_change
                    elo_ratings[bot2_name] -= elo_change

                # Save intermediate results periodically
                if i % 50 == 0 or i == len(all_pairings) - 1:
                    save_intermediate_results(results_dir, elo_ratings, match_results, bot_stats)

            except Exception as e:
                print(f"Error in match {bot1.nom} vs {bot2.nom}: {str(e)}")

    # Save final results
    save_final_results(results_dir, elo_ratings, match_results, bot_stats)

    return elo_ratings, match_results, bot_stats


def save_intermediate_results(results_dir, elo_ratings, match_results, bot_stats):
    """Save intermediate results during tournament"""
    data = {
        'elo_ratings': elo_ratings,
        'match_results': match_results,
        'bot_stats': bot_stats
    }
    with open(f"{results_dir}/intermediate_results.pkl", 'wb') as f:
        pickle.dump(data, f)


def save_final_results(results_dir, elo_ratings, match_results, bot_stats):
    """Save all final results and create visualizations"""
    # Save raw data
    data = {
        'elo_ratings': elo_ratings,
        'match_results': match_results,
        'bot_stats': bot_stats
    }
    with open(f"{results_dir}/final_results.pkl", 'wb') as f:
        pickle.dump(data, f)

    # Create DataFrames for easier analysis
    elo_df = pd.DataFrame(list(elo_ratings.items()), columns=['Bot', 'Elo'])
    elo_df['Bot_Type'] = elo_df['Bot'].map(lambda x: get_bot_type(x))
    elo_df['Depth'] = elo_df['Bot'].map(lambda x: get_bot_depth(x))
    elo_df['Time_Limit'] = elo_df['Bot'].map(lambda x: get_bot_time(x))
    elo_df['Neural_Gen'] = elo_df['Bot'].map(lambda x: get_neural_generation(x))

    stats_df = pd.DataFrame.from_dict(bot_stats, orient='index').reset_index()
    stats_df.rename(columns={'index': 'Bot'}, inplace=True)

    matches_df = pd.DataFrame(match_results)

    # Save DataFrames as CSV
    elo_df.to_csv(f"{results_dir}/elo_ratings.csv", index=False)
    stats_df.to_csv(f"{results_dir}/bot_stats.csv", index=False)
    matches_df.to_csv(f"{results_dir}/match_results.csv", index=False)

    # Generate all visualizations
    generate_visualizations(results_dir, elo_df, stats_df, matches_df)


def main():
    # Get the most recent results directory
    prev_result_dirs = glob.glob("tournament_results_*")
    if not prev_result_dirs:
        print("No previous tournament results found. Running a full tournament instead.")
        from elo_calc import run_tournament
        run_tournament(participants, num_games_per_match=2, max_workers=None)
        return

    prev_result_dirs.sort(reverse=True)  # Sort by name (which includes timestamp)
    previous_results_dir = prev_result_dirs[0]

    print(f"Found previous results directory: {previous_results_dir}")
    print(f"Number of bots in current setup: {len(participants)}")

    start_time = time.time()
    elo_ratings, match_results, bot_stats = continue_tournament(
        previous_results_dir, participants, num_games_per_match=2, max_workers=None
    )
    end_time = time.time()

    print(f"Tournament continuation completed in {end_time - start_time:.2f} seconds")

    # Print top 10 bots
    top_bots = sorted(elo_ratings.items(), key=lambda x: x[1], reverse=True)[:10]
    print("\nTop 10 Bots:")
    for i, (bot_name, elo) in enumerate(top_bots, 1):
        print(f"{i}. {bot_name}: {elo:.1f}")


if __name__ == "__main__":
    main()