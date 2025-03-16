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
from elo_tournament_setup import participants
from moteur.partie import Partie
from bots import bot, random_bot, negamax, negamaxv2, neuralbot, negamaxv4, negamaxv5, negamaxv3, negamaxv5_b


def create_bot_instance(bot_template):
    """Create a new instance of a bot with the same parameters"""
    bot_class = bot_template.__class__
    if hasattr(bot_template, 'profondeur') and hasattr(bot_template, 'temps_max'):
        return bot_class(bot_template.nom, "?", profondeur=bot_template.profondeur, temps_max=bot_template.temps_max)
    elif hasattr(bot_template, 'profondeur'):
        return bot_class(bot_template.nom, "?", profondeur=bot_template.profondeur)
    elif hasattr(bot_template, 'model_path'):
        return bot_class(bot_template.nom, "?", model_path=bot_template.model_path)
    else:
        return bot_class(bot_template.nom, "?")


def une_partie(bot1_template, bot2_template):
    """Play a single game between two bots and return the result"""
    # Create fresh instances for this match
    bot1 = create_bot_instance(bot1_template)
    bot2 = create_bot_instance(bot2_template)

    partie = Partie()
    bot1.symbole = "O"
    bot2.symbole = "X"
    partie.ajouter_joueur(bot1)
    partie.ajouter_joueur(bot2)
    partie.tour_joueur = 1

    moves_count = 0
    start_time = time.time()

    while True:
        moves_count += 1
        if partie.tour_joueur == 1:
            colonne = bot1.trouver_coup(partie.plateau, bot2)
        else:
            colonne = bot2.trouver_coup(partie.plateau, bot1)

        if partie.jouer(colonne, partie.tour_joueur):
            if partie.plateau.est_nul():
                result = "nul"
                break
            if partie.plateau.est_victoire(colonne):
                result = "bot1" if partie.tour_joueur == 1 else "bot2"
                break
            partie.tour_joueur = 2 if partie.tour_joueur == 1 else 1
        else:
            result = "bot2" if partie.tour_joueur == 1 else "bot1"
            break

    game_time = time.time() - start_time

    return {
        "result": result,
        "moves": moves_count,
        "time": game_time,
    }


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


def calculate_elo_change(rating_a, rating_b, result, k_factor=48):
    """Calculate the change in Elo rating for player A"""
    expected_a = 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

    if result == "win":
        actual_a = 1
    elif result == "draw":
        actual_a = 0.5
    else:  # loss
        actual_a = 0

    change = k_factor * (actual_a - expected_a)
    return change


def get_bot_type(bot_name):
    """Extract the bot type from its name"""
    if "Negamax P" in bot_name or bot_name.startswith("Negamax "):
        return "Negamax"
    elif "Negamax2" in bot_name:
        return "Negamax2"
    elif "Negamax3" in bot_name:
        return "Negamax3"
    elif "Negamax4" in bot_name:
        return "Negamax4"
    elif "Negamax5B" in bot_name:
        return "Negamax5B"
    elif "Negamax5" in bot_name and "B" not in bot_name:
        return "Negamax5"
    elif "Neural Bot" in bot_name:
        return "NeuralBot"
    elif "Random Bot" in bot_name:
        return "RandomBot"
    elif "Default Bot" in bot_name:
        return "DefaultBot"
    elif "gpt4o" in bot_name:
        return "gpt4o"
    elif "o3-mini-high-search" in bot_name:
        return "o3-mini-high-search"
    elif "o3-mini-high" in bot_name:
        return "o3-mini-high"
    elif "claude3.7-sonnet-thinking" in bot_name:
        return "claude3.7-sonnet-thinking"
    elif "claude3.7-sonnet" in bot_name:
        return "claude3.7-sonnet"
    elif "r1" in bot_name:
        return "r1"
    elif "gemini-pro-2.0" in bot_name:
        return "gemini-pro-2.0"
    elif "gemini-flash-2.0-thinking" in bot_name:
        return "gemini-flash-2.0-thinking"
    elif "gemini-flash-2.0" in bot_name:
        return "gemini-flash-2.0"
    elif "Gemma3" in bot_name:
        return "Gemma3"
    elif "o1" in bot_name:
        return "o1"
    elif "LeChat" in bot_name:
        return "LeChat"
    elif "QwQ" in bot_name:
        return "QwQ"
    elif "same.dev" in bot_name:
        return "same.dev"
    else:
        return "Other"


def get_bot_depth(bot_name):
    """Extract the depth parameter from the bot name if it exists"""
    if "P" in bot_name and "T" not in bot_name:
        try:
            depth = int(bot_name.split("P")[1].strip().split(" ")[0])
            return depth
        except:
            return None
    elif "P" in bot_name and "T" in bot_name:
        try:
            depth = int(bot_name.split("P")[1].strip().split(" ")[0])
            return depth
        except:
            return None
    return None


def get_bot_time(bot_name):
    """Extract the time parameter from the bot name if it exists"""
    if "T" in bot_name:
        try:
            time_val = float(bot_name.split("T")[1].strip())
            return time_val
        except:
            return None
    return None


def get_neural_generation(bot_name):
    """Extract the generation number from neural bot name if it exists"""
    if "gen" in bot_name.lower():
        try:
            gen = int(''.join(filter(str.isdigit, bot_name.split("gen")[1].split(".")[0])))
            return gen
        except:
            return None
    return None


def run_tournament(participants, num_games_per_match=2, max_workers=None):
    """Run a full tournament between all bots"""
    # Create a results directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = f"tournament_results_{timestamp}"
    os.makedirs(results_dir, exist_ok=True)

    # Initialize ratings and records
    elo_ratings = {bot.nom: 1000 for bot in participants}
    match_results = []
    bot_stats = {bot.nom: {
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
    } for bot in participants}

    # Create all possible pairings
    pairings = list(itertools.combinations(participants, 2))
    random.shuffle(pairings)  # Randomize order for better progress estimation

    print(f"Starting tournament with {len(participants)} bots ({len(pairings)} matches)")

    # Run matches in parallel
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_match = {
            executor.submit(jouer_match, bot1, bot2, num_games=num_games_per_match): (bot1, bot2)
            for bot1, bot2 in pairings
        }

        for i, future in enumerate(tqdm(concurrent.futures.as_completed(future_to_match), total=len(pairings))):
            bot1, bot2 = future_to_match[future]
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
            if i % 50 == 0 or i == len(pairings) - 1:
                save_intermediate_results(results_dir, elo_ratings, match_results, bot_stats)

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


def generate_visualizations(results_dir, elo_df, stats_df, matches_df):
    """Generate all visualizations and save them"""
    plt.figure(figsize=(12, 10))

    # 1. Overall ELO Rankings
    elo_df_sorted = elo_df.sort_values('Elo', ascending=False).copy()
    elo_df_sorted['Rank'] = range(1, len(elo_df_sorted) + 1)

    plt.figure(figsize=(14, 10))
    ax = sns.barplot(x='Elo', y='Bot', data=elo_df_sorted.head(30), hue='Bot_Type', dodge=False)
    plt.title('Top 30 Bots by ELO Rating')
    plt.tight_layout()
    plt.savefig(f"{results_dir}/top30_elo_ratings.png", dpi=300)
    plt.close()

    # 2. ELO by Bot Type (Boxplot)
    plt.figure(figsize=(12, 8))
    sns.boxplot(x='Bot_Type', y='Elo', data=elo_df)
    plt.title('ELO Distribution by Bot Type')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{results_dir}/elo_by_bot_type_boxplot.png", dpi=300)
    plt.close()

    # 3. Win Rate by Bot Type (Heatmap)
    bot_type_winrates = defaultdict(lambda: defaultdict(lambda: {"wins": 0, "total": 0}))

    for _, match in matches_df.iterrows():
        bot1_type = match['bot1_type']
        bot2_type = match['bot2_type']

        bot_type_winrates[bot1_type][bot2_type]["wins"] += match['bot1_wins']
        bot_type_winrates[bot1_type][bot2_type]["total"] += match['bot1_wins'] + match['bot2_wins'] + match['draws']

        bot_type_winrates[bot2_type][bot1_type]["wins"] += match['bot2_wins']
        bot_type_winrates[bot2_type][bot1_type]["total"] += match['bot1_wins'] + match['bot2_wins'] + match['draws']

    # Convert to win rates
    winrate_matrix = {}
    bot_types = sorted(set(elo_df['Bot_Type']))

    for type1 in bot_types:
        winrate_matrix[type1] = {}
        for type2 in bot_types:
            if type1 == type2:
                winrate_matrix[type1][type2] = 0.5  # Draw against same type
            elif bot_type_winrates[type1][type2]["total"] > 0:
                winrate_matrix[type1][type2] = bot_type_winrates[type1][type2]["wins"] / \
                                               bot_type_winrates[type1][type2]["total"]
            else:
                winrate_matrix[type1][type2] = np.nan

    winrate_df = pd.DataFrame(winrate_matrix)

    plt.figure(figsize=(12, 10))
    sns.heatmap(winrate_df, annot=True, cmap="YlGnBu", vmin=0, vmax=1,
                cbar_kws={'label': 'Win Rate (row vs column)'})
    plt.title('Win Rates Between Bot Types')
    plt.tight_layout()
    plt.savefig(f"{results_dir}/bot_type_winrate_heatmap.png", dpi=300)
    plt.close()

    # 4. Depth vs ELO (for bots with depth parameter)
    depth_elo_df = elo_df[elo_df['Depth'].notna()].copy()
    depth_elo_df['Bot_Type'] = depth_elo_df['Bot_Type'].astype('category')

    if not depth_elo_df.empty:
        plt.figure(figsize=(12, 8))
        sns.scatterplot(x='Depth', y='Elo', hue='Bot_Type', size='Time_Limit',
                        sizes=(50, 200), data=depth_elo_df, alpha=0.7)
        plt.title('Depth vs ELO Rating for Different Bot Types')
        plt.tight_layout()
        plt.savefig(f"{results_dir}/depth_vs_elo.png", dpi=300)
        plt.close()

    # 5. Time Limit vs ELO (for bots with time limit parameter)
    time_elo_df = elo_df[elo_df['Time_Limit'].notna()].copy()
    if not time_elo_df.empty:
        plt.figure(figsize=(12, 8))
        sns.scatterplot(x='Time_Limit', y='Elo', hue='Bot_Type', size='Depth',
                        sizes=(50, 200), data=time_elo_df, alpha=0.7)
        plt.xscale('log')
        plt.title('Time Limit vs ELO Rating (Log Scale)')
        plt.tight_layout()
        plt.savefig(f"{results_dir}/time_vs_elo.png", dpi=300)
        plt.close()

    # 6. Neural Bot Generation vs ELO
    neural_gen_df = elo_df[elo_df['Neural_Gen'].notna()].copy()
    if not neural_gen_df.empty:
        plt.figure(figsize=(12, 8))
        sns.scatterplot(x='Neural_Gen', y='Elo', data=neural_gen_df, alpha=0.7)
        plt.title('Neural Bot Generation vs ELO Rating')
        plt.tight_layout()
        plt.savefig(f"{results_dir}/neural_gen_vs_elo.png", dpi=300)
        plt.close()

    # 7. Win/Draw/Loss Distribution
    stats_df['total_games'] = stats_df['wins'] + stats_df['losses'] + stats_df['draws']
    stats_df['win_rate'] = stats_df['wins'] / stats_df['total_games']
    stats_df['draw_rate'] = stats_df['draws'] / stats_df['total_games']
    stats_df['loss_rate'] = stats_df['losses'] / stats_df['total_games']

    top_bots = stats_df.sort_values('win_rate', ascending=False).head(20)

    plt.figure(figsize=(14, 10))
    top_bots_stacked = top_bots[['Bot', 'win_rate', 'draw_rate', 'loss_rate']].set_index('Bot')
    ax = top_bots_stacked.plot(kind='bar', stacked=True, figsize=(14, 10),
                               color=['green', 'gray', 'red'])
    plt.title('Win/Draw/Loss Distribution for Top 20 Bots')
    plt.xlabel('Bot')
    plt.ylabel('Proportion')
    plt.legend(['Wins', 'Draws', 'Losses'])
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(f"{results_dir}/top20_wdl_distribution.png", dpi=300)
    plt.close()

    # 8. Average Moves per Match by Bot Type
    stats_df['avg_moves'] = stats_df['total_moves'] / stats_df[
        'matches_played'] / 2  # Divide by 2 as moves are counted twice

    plt.figure(figsize=(12, 8))
    sns.boxplot(x='type', y='avg_moves', data=stats_df)
    plt.title('Average Moves per Match by Bot Type')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{results_dir}/avg_moves_by_bot_type.png", dpi=300)
    plt.close()

    # 9. Find interesting records
    records = {}

    # Strongest bot
    strongest_bot = elo_df_sorted.iloc[0]['Bot']
    records['strongest_bot'] = strongest_bot
    records['strongest_bot_elo'] = elo_df_sorted.iloc[0]['Elo']

    # Strongest bot by type
    strongest_by_type = {}
    for bot_type in elo_df['Bot_Type'].unique():
        type_df = elo_df[elo_df['Bot_Type'] == bot_type].sort_values('Elo', ascending=False)
        if not type_df.empty:
            strongest = type_df.iloc[0]['Bot']
            elo = type_df.iloc[0]['Elo']
            strongest_by_type[bot_type] = {'bot': strongest, 'elo': elo}
    records['strongest_by_type'] = strongest_by_type

    # Most draws
    most_draws_bot = stats_df.loc[stats_df['draws'].idxmax()]
    records['most_draws_bot'] = most_draws_bot['Bot']
    records['most_draws_count'] = most_draws_bot['draws']

    # Most decisive (fewest draws)
    stats_df['draw_ratio'] = stats_df['draws'] / stats_df['total_games']
    most_decisive = stats_df.loc[stats_df[stats_df['matches_played'] > 10]['draw_ratio'].idxmin()]
    records['most_decisive_bot'] = most_decisive['Bot']
    records['most_decisive_draw_ratio'] = most_decisive['draw_ratio']

    # Save records
    with open(f"{results_dir}/interesting_records.txt", 'w') as f:
        f.write("INTERESTING TOURNAMENT RECORDS\n")
        f.write("============================\n\n")

        f.write(f"Strongest Bot: {records['strongest_bot']} (ELO: {records['strongest_bot_elo']:.1f})\n\n")

        f.write("Strongest Bot by Type:\n")
        for bot_type, data in records['strongest_by_type'].items():
            f.write(f"  {bot_type}: {data['bot']} (ELO: {data['elo']:.1f})\n")
        f.write("\n")

        f.write(f"Most Draws: {records['most_draws_bot']} ({records['most_draws_count']} draws)\n")
        f.write(
            f"Most Decisive Bot: {records['most_decisive_bot']} (Draw ratio: {records['most_decisive_draw_ratio']:.2f})\n")

        # Find biggest upset (match where weaker bot beat stronger bot by largest Elo gap)
        biggest_upset = None
        biggest_upset_gap = 0

        for _, match in matches_df.iterrows():
            bot1_elo = elo_df[elo_df['Bot'] == match['bot1']]['Elo'].values[0]
            bot2_elo = elo_df[elo_df['Bot'] == match['bot2']]['Elo'].values[0]

            # Check if bot2 (weaker) beat bot1 (stronger)
            if bot1_elo > bot2_elo and match['bot2_wins'] > match['bot1_wins']:
                gap = bot1_elo - bot2_elo
                if gap > biggest_upset_gap:
                    biggest_upset_gap = gap
                    biggest_upset = {
                        'stronger_bot': match['bot1'],
                        'stronger_elo': bot1_elo,
                        'weaker_bot': match['bot2'],
                        'weaker_elo': bot2_elo,
                        'stronger_wins': match['bot1_wins'],
                        'weaker_wins': match['bot2_wins'],
                        'draws': match['draws']
                    }

            # Check if bot1 (weaker) beat bot2 (stronger)
            if bot2_elo > bot1_elo and match['bot1_wins'] > match['bot2_wins']:
                gap = bot2_elo - bot1_elo
                if gap > biggest_upset_gap:
                    biggest_upset_gap = gap
                    biggest_upset = {
                        'stronger_bot': match['bot2'],
                        'stronger_elo': bot2_elo,
                        'weaker_bot': match['bot1'],
                        'weaker_elo': bot1_elo,
                        'stronger_wins': match['bot2_wins'],
                        'weaker_wins': match['bot1_wins'],
                        'draws': match['draws']
                    }

        if biggest_upset:
            f.write("\nBiggest Upset:\n")
            f.write(f"  {biggest_upset['weaker_bot']} (ELO: {biggest_upset['weaker_elo']:.1f}) defeated ")
            f.write(f"{biggest_upset['stronger_bot']} (ELO: {biggest_upset['stronger_elo']:.1f})\n")
            f.write(
                f"  Score: {biggest_upset['weaker_wins']}-{biggest_upset['stronger_wins']}-{biggest_upset['draws']} (W-L-D)\n")
            f.write(f"  ELO Gap: {biggest_upset_gap:.1f} points\n")

            # Find closest rivalry (most balanced matches)
        closest_rivalry = None
        smallest_win_diff = float('inf')

        for _, match in matches_df.iterrows():
            if match['bot1_wins'] + match['bot2_wins'] > 0:  # Ensure there were some decisive games
                win_diff = abs(match['bot1_wins'] - match['bot2_wins'])
                if win_diff < smallest_win_diff:
                    smallest_win_diff = win_diff
                    closest_rivalry = {
                        'bot1': match['bot1'],
                        'bot2': match['bot2'],
                        'bot1_wins': match['bot1_wins'],
                        'bot2_wins': match['bot2_wins'],
                        'draws': match['draws']
                    }

        if closest_rivalry:
            f.write("\nClosest Rivalry:\n")
            f.write(f"  {closest_rivalry['bot1']} vs {closest_rivalry['bot2']}\n")
            f.write(
                f"  Score: {closest_rivalry['bot1_wins']}-{closest_rivalry['bot2_wins']}-{closest_rivalry['draws']} (W-L-D)\n")

        # Largest Elo gap between consecutive ranks
        largest_gap = 0
        largest_gap_bots = None

        for i in range(len(elo_df_sorted) - 1):
            gap = elo_df_sorted.iloc[i]['Elo'] - elo_df_sorted.iloc[i + 1]['Elo']
            if gap > largest_gap:
                largest_gap = gap
                largest_gap_bots = {
                    'higher_bot': elo_df_sorted.iloc[i]['Bot'],
                    'higher_elo': elo_df_sorted.iloc[i]['Elo'],
                    'lower_bot': elo_df_sorted.iloc[i + 1]['Bot'],
                    'lower_elo': elo_df_sorted.iloc[i + 1]['Elo'],
                    'ranks': f"{i + 1}-{i + 2}"
                }

        if largest_gap_bots:
            f.write("\nLargest ELO Gap Between Consecutive Ranks:\n")
            f.write(f"  Ranks {largest_gap_bots['ranks']}: {largest_gap:.1f} ELO points\n")
            f.write(f"  {largest_gap_bots['higher_bot']} ({largest_gap_bots['higher_elo']:.1f}) vs ")
            f.write(f"{largest_gap_bots['lower_bot']} ({largest_gap_bots['lower_elo']:.1f})\n")

        # 10. ELO distribution by bot family and parameters
    for bot_type in elo_df['Bot_Type'].unique():
        type_df = elo_df[elo_df['Bot_Type'] == bot_type].sort_values('Elo', ascending=False)
        if len(type_df) > 1:  # Only create graph if multiple bots of this type
            plt.figure(figsize=(14, 10))
            ax = sns.barplot(x='Elo', y='Bot', data=type_df)
            plt.title(f'ELO Ratings for {bot_type} Bots')
            plt.tight_layout()
            plt.savefig(f"{results_dir}/elo_{bot_type}.png", dpi=300)
            plt.close()

        # 11. Depth vs ELO per bot type
    for bot_type in depth_elo_df['Bot_Type'].unique():
        type_df = depth_elo_df[depth_elo_df['Bot_Type'] == bot_type]
        if len(type_df) > 1:  # Only create graph if multiple bots of this type
            plt.figure(figsize=(12, 8))
            # If time limit exists, use it for coloring
            if 'Time_Limit' in type_df.columns and not type_df['Time_Limit'].isna().all():
                sns.scatterplot(x='Depth', y='Elo', hue='Time_Limit', size='Elo',
                                sizes=(50, 200), data=type_df, alpha=0.7)
                plt.title(f'Depth vs ELO for {bot_type} Bots')
            else:
                sns.scatterplot(x='Depth', y='Elo', size='Elo',
                                sizes=(50, 200), data=type_df, alpha=0.7)
                plt.title(f'Depth vs ELO for {bot_type} Bots')
            plt.tight_layout()
            plt.savefig(f"{results_dir}/depth_vs_elo_{bot_type}.png", dpi=300)
            plt.close()

        # 12. Performance tiers
    elo_df_sorted['Tier'] = pd.qcut(elo_df_sorted['Elo'], q=5, labels=['E', 'D', 'C', 'B', 'A'])

    tier_counts = elo_df_sorted.groupby(['Bot_Type', 'Tier']).size().unstack(fill_value=0)

    plt.figure(figsize=(14, 10))
    tier_counts.plot(kind='bar', stacked=True, colormap='viridis')
    plt.title('Bot Types by Performance Tier')
    plt.xlabel('Bot Type')
    plt.ylabel('Count')
    plt.legend(title='Tier')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{results_dir}/bot_types_by_tier.png", dpi=300)
    plt.close()

    # 13. Create an aggregate performance summary
    summary_stats = stats_df.groupby('type').agg({
        'wins': 'sum',
        'losses': 'sum',
        'draws': 'sum',
        'total_moves': 'sum',
        'total_time': 'sum',
        'matches_played': 'sum',
        'Bot': 'count'
    }).reset_index()

    summary_stats['win_rate'] = summary_stats['wins'] / (
                summary_stats['wins'] + summary_stats['losses'] + summary_stats['draws'])
    summary_stats['avg_moves_per_game'] = summary_stats['total_moves'] / (summary_stats['matches_played'] * 2)
    summary_stats['avg_time_per_move'] = summary_stats['total_time'] / summary_stats['total_moves']

    summary_stats = summary_stats.rename(columns={'Bot': 'count', 'type': 'Bot_Type'})

    summary_stats.to_csv(f"{results_dir}/bot_type_summary.csv", index=False)

    # 14. First player advantage analysis
    first_player_stats = {}

    for _, match in matches_df.iterrows():
        # We don't know directly which bot went first in each individual game,
        # but we know they alternated and played an equal number of games as first player
        total_games = match['bot1_wins'] + match['bot2_wins'] + match['draws']
        first_player_wins = (match['bot1_wins'] + match['bot2_wins']) / 2  # Estimate

        # Update stats
        for bot_type in [match['bot1_type'], match['bot2_type']]:
            if bot_type not in first_player_stats:
                first_player_stats[bot_type] = {'games': 0, 'first_player_wins': 0}

            first_player_stats[bot_type]['games'] += total_games / 2  # Each bot went first in half the games
            first_player_stats[bot_type]['first_player_wins'] += first_player_wins / 2  # Half for each bot type

    # Calculate first player advantage rate
    for bot_type in first_player_stats:
        first_player_stats[bot_type]['advantage_rate'] = (
                first_player_stats[bot_type]['first_player_wins'] /
                first_player_stats[bot_type]['games']
        )

    # Create DataFrame and plot
    fpa_df = pd.DataFrame.from_dict(first_player_stats, orient='index').reset_index()
    fpa_df.rename(columns={'index': 'Bot_Type'}, inplace=True)

    plt.figure(figsize=(12, 8))
    sns.barplot(x='Bot_Type', y='advantage_rate', data=fpa_df)
    plt.axhline(y=0.5, color='r', linestyle='--')  # 0.5 line indicating no advantage
    plt.title('First Player Advantage by Bot Type')
    plt.xlabel('Bot Type')
    plt.ylabel('First Player Win Rate')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{results_dir}/first_player_advantage.png", dpi=300)
    plt.close()

    # Return analysis complete message
    return "Analysis complete. Results saved to " + results_dir


def main():
    # Import participants list from the main script
    # participants declared in the main script

    print("Starting connect four bot tournament")
    print(f"Number of bots: {len(participants)}")

    start_time = time.time()
    elo_ratings, match_results, bot_stats = run_tournament(participants, num_games_per_match=2, max_workers=None)
    end_time = time.time()

    print(f"Tournament completed in {end_time - start_time:.2f} seconds")
    print(f"Results saved in tournament_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

    # Print top 10 bots
    top_bots = sorted(elo_ratings.items(), key=lambda x: x[1], reverse=True)[:10]
    print("\nTop 10 Bots:")
    for i, (bot_name, elo) in enumerate(top_bots, 1):
        print(f"{i}. {bot_name}: {elo:.1f}")


if __name__ == "__main__":
    main()