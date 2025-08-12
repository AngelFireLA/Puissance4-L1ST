import json
import os
import time
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict, Counter
from tqdm import tqdm
import re
import argparse
import pickle  # For saving intermediate Elo history if desired

# --- Configuration for Elo Calculation ---
INITIAL_ELO = 1000.0
NUM_ELO_PASSES = 10  # Number of full passes over the game data
K_FACTOR_START = 64  # Initial K-factor for early, larger adjustments
K_FACTOR_END = 16  # Final K-factor for later, finer tuning


# --- Bot Name Parsing Functions ---

def get_bot_type(bot_name):
    """Extract the bot type from its name, updated for new bots."""
    name_lower = bot_name.lower()

    # More specific names first to avoid premature matching
    if "negamax5b" in name_lower: return "Negamax5B"
    if "negamax5" in name_lower and "b" not in name_lower: return "Negamax5"
    if "negamax4" in name_lower: return "Negamax4"
    if "negamax3" in name_lower: return "Negamax3"
    if "negamax2" in name_lower: return "Negamax2"
    if "negamax " in name_lower or bot_name.startswith("Negamax P"): return "Negamax"

    if "o3-mini-high-search" in name_lower: return "o3-mini-high-search"
    if "o3-mini-high" in name_lower: return "o3-mini-high"  # Before plain "o3"

    if "claude3.7-sonnet-thinking" in name_lower: return "claude3.7-sonnet-thinking"
    if "claude3.7-sonnet" in name_lower: return "claude3.7-sonnet"

    if "gemini-flash-2.0-thinking" in name_lower: return "gemini-flash-2.0-thinking"
    if "gemini-flash-2.0" in name_lower: return "gemini-flash-2.0"

    if "gemini2.5 flash thinking" in name_lower: return "Gemini2.5 Flash Thinking"
    if "gemini2.5 pro" in name_lower: return "Gemini2.5 Pro"

    if "gemini-pro-2.0" in name_lower: return "gemini-pro-2.0"

    if "gpt4o" in name_lower: return "gpt4o"
    if "gemma2" in name_lower: return "Gemma2"  # From "Gemma2 P1"
    if "qwen3" in name_lower: return "Qwen3"
    if "o4-mini-high" in name_lower: return "o4-mini-high"
    if "o3 " in name_lower or bot_name.startswith("o3 P"): return "o3"
    if "o1 " in name_lower or bot_name.startswith("o1 P"): return "o1"

    if "lechat" in name_lower: return "LeChat"
    if "qwq" in name_lower: return "QwQ"
    if "same.dev" in name_lower: return "same.dev"
    if "r1 " in name_lower or bot_name.startswith("r1 T"): return "r1"

    if "neural bot" in name_lower: return "NeuralBot"  # Legacy
    if "random bot" in name_lower: return "RandomBot"
    if "default bot" in name_lower: return "DefaultBot"

    print(f"Warning: Bot name '{bot_name}' mapped to 'Other'. Update get_bot_type if needed.")
    return "Other"


def get_bot_depth(bot_name):
    """Extract the depth parameter (e.g., 'P6')."""
    match = re.search(r"P(\d+)", bot_name)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


def get_bot_time(bot_name):
    """Extract the time limit parameter (e.g., 'T0.1')."""
    match = re.search(r"T(\d+\.?\d*)", bot_name)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def get_neural_generation(bot_name):
    """Extract neural net generation (e.g., 'gen1')."""
    if "gen" in bot_name.lower():
        try:
            # More robust extraction for "gen" followed by numbers
            gen_part = bot_name.lower().split("gen")[1]
            return int(re.match(r"(\d+)", gen_part).group(1))
        except (IndexError, AttributeError, ValueError):
            return None
    return None


def get_mcts_iterations(bot_name):
    """Extract MCTS iterations (e.g., 'I1000')."""
    match = re.search(r"I(\d+)", bot_name, re.IGNORECASE)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


# --- Elo Calculation Logic ---
def calculate_elo_change(rating_a, rating_b, result_for_a, k_factor):
    """
    Calculate Elo change for player A.
    result_for_a: "win", "loss", "draw"
    """
    expected_a = 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

    if result_for_a == "win":
        actual_a = 1.0
    elif result_for_a == "draw":
        actual_a = 0.5
    else:  # loss
        actual_a = 0.0

    change = k_factor * (actual_a - expected_a)
    return change


def run_elo_calculation_passes(games_data, all_bot_names):
    """
    Performs multiple passes of Elo calculation.
    Returns final Elo ratings and a history of Elo ratings per pass.
    """
    elo_ratings = {bot_name: INITIAL_ELO for bot_name in all_bot_names}
    elo_history_per_pass = []  # To store Elo ratings after each pass

    # Sort games by global ID for chronological processing
    games_data_sorted = sorted(games_data, key=lambda x: x["game_global_id"])

    print(f"Starting Elo calculation with {NUM_ELO_PASSES} passes...")
    for pass_num in tqdm(range(NUM_ELO_PASSES), desc="Elo Passes"):
        # Determine K-factor for this pass (linear decay)
        if NUM_ELO_PASSES == 1:
            current_k_factor = K_FACTOR_START
        else:
            current_k_factor = K_FACTOR_START - (K_FACTOR_START - K_FACTOR_END) * (pass_num / (NUM_ELO_PASSES - 1))

        # Work on a copy of elo_ratings for this pass
        current_pass_elos = elo_ratings.copy()

        for game in games_data_sorted:
            bot_o_name = game["player_O"]
            bot_x_name = game["player_X"]
            winner = game["winner"]

            # Ensure bots are in the Elo dictionary (should be, due to all_bot_names initialization)
            if bot_o_name not in current_pass_elos: current_pass_elos[bot_o_name] = INITIAL_ELO
            if bot_x_name not in current_pass_elos: current_pass_elos[bot_x_name] = INITIAL_ELO

            elo_o = current_pass_elos[bot_o_name]
            elo_x = current_pass_elos[bot_x_name]

            result_for_o = "draw"
            if winner == bot_o_name:
                result_for_o = "win"
            elif winner == bot_x_name:
                result_for_o = "loss"

            delta_o = calculate_elo_change(elo_o, elo_x, result_for_o, current_k_factor)

            current_pass_elos[bot_o_name] += delta_o
            current_pass_elos[bot_x_name] -= delta_o  # Elo is zero-sum for a game

        # Update main elo_ratings with the results of this pass
        elo_ratings = current_pass_elos
        elo_history_per_pass.append(elo_ratings.copy())  # Store snapshot

    print("Elo calculation finished.")
    return elo_ratings, elo_history_per_pass


# --- Statistics Aggregation ---
def aggregate_bot_statistics(games_data, all_bot_names):
    """
    Aggregates statistics for each bot from all game results.
    """
    bot_stats = {
        bot_name: {
            "wins": 0, "losses": 0, "draws": 0,
            "games_played": 0,
            "total_moves_in_games": 0,  # Sum of moves in games this bot played
            "total_time_in_games": 0.0,  # Sum of time of games this bot played
            "type": get_bot_type(bot_name),
            "depth": get_bot_depth(bot_name),
            "time_limit": get_bot_time(bot_name),
            "neural_gen": get_neural_generation(bot_name),
            "mcts_iter": get_mcts_iterations(bot_name),
        } for bot_name in all_bot_names
    }

    for game in games_data:
        bot_o = game["player_O"]
        bot_x = game["player_X"]
        winner = game["winner"]
        moves = game["moves"]
        game_time = game["time_seconds"]

        # Update stats for Player O
        if bot_o in bot_stats:
            bot_stats[bot_o]["games_played"] += 1
            bot_stats[bot_o]["total_moves_in_games"] += moves
            bot_stats[bot_o]["total_time_in_games"] += game_time
            if winner == bot_o:
                bot_stats[bot_o]["wins"] += 1
            elif winner == bot_x:
                bot_stats[bot_o]["losses"] += 1
            else:  # Draw
                bot_stats[bot_o]["draws"] += 1

        # Update stats for Player X
        if bot_x in bot_stats:
            bot_stats[bot_x]["games_played"] += 1
            bot_stats[bot_x]["total_moves_in_games"] += moves
            bot_stats[bot_x]["total_time_in_games"] += game_time
            if winner == bot_x:
                bot_stats[bot_x]["wins"] += 1
            elif winner == bot_o:
                bot_stats[bot_x]["losses"] += 1
            else:  # Draw
                bot_stats[bot_x]["draws"] += 1

    return bot_stats


def create_match_summary_df(games_data):
    """ Creates a DataFrame summarizing head-to-head match results. """
    match_outcomes = defaultdict(lambda: {"p1_wins": 0, "p2_wins": 0, "draws": 0, "games": 0,
                                          "total_moves": 0, "total_time": 0.0})

    for game in games_data:
        # Use the canonical match participants from the JSON
        p1_name = game["match_participant_1"]
        p2_name = game["match_participant_2"]

        # Key for the match pair (order doesn't matter here as it's canonical from JSON)
        match_key = tuple(sorted((p1_name, p2_name)))

        match_outcomes[match_key]["games"] += 1
        match_outcomes[match_key]["total_moves"] += game["moves"]
        match_outcomes[match_key]["total_time"] += game["time_seconds"]

        winner = game["winner"]
        if winner == p1_name:
            match_outcomes[match_key]["p1_wins"] += 1
        elif winner == p2_name:
            match_outcomes[match_key]["p2_wins"] += 1
        elif winner == "draw":
            match_outcomes[match_key]["draws"] += 1

    match_summary_list = []
    for (bot1, bot2), data in match_outcomes.items():
        match_summary_list.append({
            "bot1": bot1, "bot2": bot2,
            "bot1_wins": data["p1_wins"], "bot2_wins": data["p2_wins"],
            "draws": data["draws"], "total_games_in_match": data["games"],
            "total_moves": data["total_moves"], "total_time": data["total_time"],
            "bot1_type": get_bot_type(bot1), "bot2_type": get_bot_type(bot2)
        })
    return pd.DataFrame(match_summary_list)


# --- Saving Results and Visualizations (Adapted from original) ---
def save_results_and_visualize(output_dir_base, elo_ratings, bot_stats_dict, games_data, elo_history):
    """Saves all results and creates visualizations."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = f"{output_dir_base}_analysis_{timestamp}"
    os.makedirs(results_dir, exist_ok=True)
    print(f"\nSaving analysis results to: {results_dir}")

    # --- Prepare DataFrames ---
    elo_df_list = []
    for bot_name, elo in elo_ratings.items():
        stats = bot_stats_dict.get(bot_name, {})  # Get stats, or empty if somehow missing
        elo_df_list.append({
            'Bot': bot_name,
            'Elo': elo,
            'Bot_Type': stats.get('type', get_bot_type(bot_name)),  # Fallback if type wasn't pre-filled
            'Depth': stats.get('depth'),
            'Time_Limit': stats.get('time_limit'),
            'Neural_Gen': stats.get('neural_gen'),
            'MCTS_Iter': stats.get('mcts_iter')
        })
    elo_df = pd.DataFrame(elo_df_list)
    elo_df = elo_df.sort_values('Elo', ascending=False).reset_index(drop=True)
    elo_df['Rank'] = elo_df.index + 1

    stats_df = pd.DataFrame.from_dict(bot_stats_dict, orient='index').reset_index()
    stats_df.rename(columns={'index': 'Bot'}, inplace=True)
    # Calculate rates for stats_df
    stats_df['win_rate'] = np.where(stats_df['games_played'] > 0, stats_df['wins'] / stats_df['games_played'], 0)
    stats_df['loss_rate'] = np.where(stats_df['games_played'] > 0, stats_df['losses'] / stats_df['games_played'], 0)
    stats_df['draw_rate'] = np.where(stats_df['games_played'] > 0, stats_df['draws'] / stats_df['games_played'], 0)
    stats_df['avg_moves_per_game'] = np.where(stats_df['games_played'] > 0,
                                              stats_df['total_moves_in_games'] / stats_df['games_played'], 0)
    stats_df['avg_time_per_game'] = np.where(stats_df['games_played'] > 0,
                                             stats_df['total_time_in_games'] / stats_df['games_played'], 0)

    # Raw games data can be saved as CSV too, though it's already in JSON
    games_df = pd.DataFrame(games_data)

    # Match summary DataFrame
    matches_df = create_match_summary_df(games_data)

    # --- Save DataFrames as CSV ---
    elo_df.to_csv(os.path.join(results_dir, "elo_ratings.csv"), index=False)
    stats_df.to_csv(os.path.join(results_dir, "bot_statistics.csv"), index=False)
    games_df.to_csv(os.path.join(results_dir, "all_games_detailed.csv"), index=False)
    matches_df.to_csv(os.path.join(results_dir, "match_summary.csv"), index=False)

    # Save Elo history (list of dicts)
    with open(os.path.join(results_dir, "elo_history_per_pass.pkl"), 'wb') as f:
        pickle.dump(elo_history, f)
    print("CSVs and Elo history saved.")

    # --- Generate Visualizations ---
    print("Generating visualizations...")
    plt.style.use('seaborn-v0_8-whitegrid')  # Using a seaborn style

    # 1. Overall ELO Rankings (Top 30)
    plt.figure(figsize=(16, 12))
    sns.barplot(x='Elo', y='Bot', data=elo_df.head(30), hue='Bot_Type', dodge=False, palette="viridis")
    plt.title('Top 30 Bots by ELO Rating', fontsize=16)
    plt.xlabel('ELO Rating', fontsize=12)
    plt.ylabel('Bot', fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, "top30_elo_ratings.png"), dpi=300)
    plt.close()

    # 2. ELO by Bot Type (Boxplot)
    plt.figure(figsize=(14, 9))
    sns.boxplot(x='Elo', y='Bot_Type', data=elo_df, palette="coolwarm",
                order=elo_df.groupby('Bot_Type')['Elo'].median().sort_values(ascending=False).index)
    plt.title('ELO Distribution by Bot Type', fontsize=16)
    plt.xlabel('ELO Rating', fontsize=12)
    plt.ylabel('Bot Type', fontsize=12)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, "elo_by_bot_type_boxplot.png"), dpi=300)
    plt.close()

    # 3. Win Rate by Bot Type (Heatmap - using match_summary_df)
    # This requires careful aggregation of win rates between types
    bot_types = sorted(matches_df['bot1_type'].dropna().unique())
    winrate_matrix_data = defaultdict(lambda: defaultdict(lambda: {"wins_row": 0, "games_total": 0}))

    for _, match_row in matches_df.iterrows():
        type1, type2 = match_row['bot1_type'], match_row['bot2_type']
        if pd.isna(type1) or pd.isna(type2): continue

        # Games where type1 is bot1
        winrate_matrix_data[type1][type2]["wins_row"] += match_row['bot1_wins']
        winrate_matrix_data[type1][type2]["games_total"] += match_row['total_games_in_match']
        # Games where type1 is bot2 (so type2 is bot1)
        winrate_matrix_data[type2][type1]["wins_row"] += match_row['bot2_wins']
        winrate_matrix_data[type2][type1]["games_total"] += match_row['total_games_in_match']

    winrate_df_data = []
    for r_type in bot_types:
        row = []
        for c_type in bot_types:
            if r_type == c_type:
                # For diagonal, could show average win rate or 0.5 if many self-plays
                # Or calculate from actual self-type matches if they exist and make sense
                # For now, let's use overall win rate of this type if available, or NaN
                # This part is tricky for a heatmap of A vs B.
                # Let's make it win rate of RowType vs ColType.
                # If RowType == ColType, it's ambiguous. Let's put NaN or 0.5.
                num = winrate_matrix_data[r_type][c_type]["wins_row"]
                den = winrate_matrix_data[r_type][c_type]["games_total"]
                # This counts games where r_type played c_type, and r_type was listed as bot1 or bot2.
                # The logic above for winrate_matrix_data needs to be symmetric for total games.
                # Let's simplify: iterate through matches_df, for each (typeA, typeB) pair, sum wins of A vs B and total games.
                row.append(0.5 if r_type == c_type else np.nan)  # Placeholder for diagonal
            else:
                wins = winrate_matrix_data[r_type][c_type]["wins_row"]
                total = winrate_matrix_data[r_type][c_type]["games_total"]
                row.append(wins / total if total > 0 else np.nan)
        winrate_df_data.append(row)

    # Rebuilding heatmap logic more directly from matches_df
    # This heatmap shows win rate of ROW player against COLUMN player
    type_pairs = defaultdict(lambda: {'wins_A': 0, 'games': 0})
    for _, row in matches_df.iterrows():
        t1, t2 = row['bot1_type'], row['bot2_type']
        if pd.isna(t1) or pd.isna(t2): continue

        # t1 vs t2
        key1 = tuple(sorted((t1, t2)))  # Canonical key
        type_pairs[key1]['games'] += row['total_games_in_match']
        if t1 == key1[0]:  # t1 is the first in sorted tuple
            type_pairs[key1]['wins_A'] += row['bot1_wins']
        else:  # t1 is the second in sorted tuple
            type_pairs[key1]['wins_A'] += row['bot2_wins']  # this is wins for key1[0]

    # Create the matrix for heatmap
    unique_bot_types = sorted(
        list(set(matches_df['bot1_type'].dropna().tolist() + matches_df['bot2_type'].dropna().tolist())))
    heatmap_matrix = pd.DataFrame(index=unique_bot_types, columns=unique_bot_types, dtype=float)

    for r_type in unique_bot_types:
        for c_type in unique_bot_types:
            if r_type == c_type:
                heatmap_matrix.loc[r_type, c_type] = 0.5  # Or NaN
                continue

            key = tuple(sorted((r_type, c_type)))
            data = type_pairs[key]
            if data['games'] > 0:
                if r_type == key[0]:  # r_type is the 'A' bot in (A,B)
                    heatmap_matrix.loc[r_type, c_type] = data['wins_A'] / data['games']
                else:  # r_type is the 'B' bot, so we want 1 - win_rate_of_A
                    heatmap_matrix.loc[r_type, c_type] = (data['games'] - data['wins_A'] - matches_df[
                        (matches_df['bot1_type'] == c_type) & (matches_df['bot2_type'] == r_type) | (
                                    matches_df['bot1_type'] == r_type) & (matches_df['bot2_type'] == c_type)][
                        'draws'].sum()) / data['games']
            else:
                heatmap_matrix.loc[r_type, c_type] = np.nan

    # The above heatmap logic is getting complex. A simpler approach:
    # For each cell (TypeA, TypeB), find all games where TypeA played TypeB.
    # Calculate win rate of TypeA in those games.
    # This requires iterating `games_df`.

    # Simpler heatmap: Aggregate wins of row_type vs col_type
    pivot_data = []
    for game in games_data:
        p_o, p_x = game['player_O'], game['player_X']
        t_o, t_x = get_bot_type(p_o), get_bot_type(p_x)
        winner = game['winner']

        # O vs X
        outcome_o = 0.5 if winner == "draw" else (1.0 if winner == p_o else 0.0)
        pivot_data.append({'row_type': t_o, 'col_type': t_x, 'outcome': outcome_o})
        # X vs O (for symmetry in data, though pivot_table handles it)
        outcome_x = 0.5 if winner == "draw" else (1.0 if winner == p_x else 0.0)
        pivot_data.append({'row_type': t_x, 'col_type': t_o, 'outcome': outcome_x})

    if pivot_data:
        heatmap_df_raw = pd.DataFrame(pivot_data)
        heatmap_pivot = heatmap_df_raw.pivot_table(index='row_type', columns='col_type', values='outcome',
                                                   aggfunc='mean')

        plt.figure(figsize=(15, 12))
        sns.heatmap(heatmap_pivot, annot=True, cmap="YlGnBu", fmt=".2f", vmin=0, vmax=1,
                    cbar_kws={'label': 'Win Rate (Row Type vs Column Type)'})
        plt.title('Win Rates Between Bot Types', fontsize=16)
        plt.xlabel('Opponent Bot Type (Column)', fontsize=12)
        plt.ylabel('Bot Type (Row)', fontsize=12)
        plt.xticks(rotation=45, ha="right")
        plt.yticks(rotation=0)
        plt.tight_layout()
        plt.savefig(os.path.join(results_dir, "bot_type_winrate_heatmap.png"), dpi=300)
        plt.close()
    else:
        print("Skipping bot_type_winrate_heatmap due to no pivot data.")

    # 4. Depth vs ELO
    depth_elo_df = elo_df[elo_df['Depth'].notna()].copy()
    if not depth_elo_df.empty:
        plt.figure(figsize=(12, 8))
        sns.scatterplot(x='Depth', y='Elo', hue='Bot_Type', size='Time_Limit', data=depth_elo_df, sizes=(50, 250),
                        alpha=0.7, palette="tab10")
        plt.title('Depth vs ELO Rating', fontsize=16)
        plt.xlabel('Depth', fontsize=12)
        plt.ylabel('ELO Rating', fontsize=12)
        plt.legend(title='Bot Type / Time Limit', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(os.path.join(results_dir, "depth_vs_elo.png"), dpi=300)
        plt.close()

    # 5. Time Limit vs ELO
    time_elo_df = elo_df[elo_df['Time_Limit'].notna()].copy()
    if not time_elo_df.empty:
        plt.figure(figsize=(12, 8))
        sns.scatterplot(x='Time_Limit', y='Elo', hue='Bot_Type', size='Depth', data=time_elo_df, sizes=(50, 250),
                        alpha=0.7, palette="tab10")
        plt.xscale('log')
        plt.title('Time Limit (log scale) vs ELO Rating', fontsize=16)
        plt.xlabel('Time Limit (seconds, log scale)', fontsize=12)
        plt.ylabel('ELO Rating', fontsize=12)
        plt.legend(title='Bot Type / Depth', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(os.path.join(results_dir, "time_vs_elo.png"), dpi=300)
        plt.close()

    # 6. MCTS Iterations vs ELO
    mcts_elo_df = elo_df[elo_df['MCTS_Iter'].notna()].copy()
    if not mcts_elo_df.empty:
        plt.figure(figsize=(12, 8))
        sns.scatterplot(x='MCTS_Iter', y='Elo', hue='Bot_Type', data=mcts_elo_df, alpha=0.7, s=100, palette="tab10")
        plt.xscale('log')
        plt.title('MCTS Iterations (log scale) vs ELO Rating', fontsize=16)
        plt.xlabel('MCTS Iterations (log scale)', fontsize=12)
        plt.ylabel('ELO Rating', fontsize=12)
        plt.legend(title='Bot Type', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(os.path.join(results_dir, "mcts_iter_vs_elo.png"), dpi=300)
        plt.close()

    # 7. Win/Draw/Loss Distribution (Top 20 by Win Rate)
    # Ensure 'win_rate' is in stats_df from earlier calculation
    top_bots_stats = stats_df.sort_values('win_rate', ascending=False).head(20)
    if not top_bots_stats.empty:
        plt.figure(figsize=(16, 10))
        top_bots_stats.set_index('Bot')[['win_rate', 'draw_rate', 'loss_rate']].plot(
            kind='bar', stacked=True, figsize=(16, 10), colormap="Spectral"
        )
        plt.title('Win/Draw/Loss Distribution for Top 20 Bots (by Win Rate)', fontsize=16)
        plt.xlabel('Bot', fontsize=12)
        plt.ylabel('Proportion of Games', fontsize=12)
        plt.xticks(rotation=75, ha="right")
        plt.legend(['Wins', 'Draws', 'Losses'], title='Outcome')
        plt.tight_layout()
        plt.savefig(os.path.join(results_dir, "top20_wdl_distribution.png"), dpi=300)
        plt.close()

    # 8. Elo History Plot (Top N bots)
    if elo_history:
        num_bots_to_plot = 10
        top_n_bots_final_elo = elo_df.head(num_bots_to_plot)['Bot'].tolist()

        history_df_data = []
        for pass_idx, pass_elos in enumerate(elo_history):
            for bot_name in top_n_bots_final_elo:
                if bot_name in pass_elos:
                    history_df_data.append({'Pass': pass_idx + 1, 'Bot': bot_name, 'Elo': pass_elos[bot_name]})

        if history_df_data:
            elo_history_df_plot = pd.DataFrame(history_df_data)
            plt.figure(figsize=(14, 8))
            sns.lineplot(data=elo_history_df_plot, x='Pass', y='Elo', hue='Bot', marker='o', palette="tab10")
            plt.title(f'Elo Evolution for Top {num_bots_to_plot} Bots Over Passes', fontsize=16)
            plt.xlabel('Elo Calculation Pass Number', fontsize=12)
            plt.ylabel('Elo Rating', fontsize=12)
            plt.legend(title='Bot', bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.grid(True, which="both", ls="-", alpha=0.5)
            plt.tight_layout()
            plt.savefig(os.path.join(results_dir, "elo_history_top_bots.png"), dpi=300)
            plt.close()

    # 9. First Player Advantage by Bot Type (using games_df)
    first_player_advantage_data = []
    for _, game_row in games_df.iterrows():
        player_o_type = get_bot_type(game_row['player_O'])
        if game_row['winner'] == game_row['player_O']:
            first_player_advantage_data.append({'Bot_Type': player_o_type, 'Outcome': 1})  # Win
        elif game_row['winner'] == 'draw':
            first_player_advantage_data.append({'Bot_Type': player_o_type, 'Outcome': 0.5})  # Draw
        else:
            first_player_advantage_data.append({'Bot_Type': player_o_type, 'Outcome': 0})  # Loss

    if first_player_advantage_data:
        fpa_df = pd.DataFrame(first_player_advantage_data)
        fpa_summary = fpa_df.groupby('Bot_Type')['Outcome'].mean().reset_index(name='First_Player_Win_Rate_Equivalent')
        fpa_summary = fpa_summary.sort_values('First_Player_Win_Rate_Equivalent', ascending=False)

        plt.figure(figsize=(14, 8))
        sns.barplot(x='First_Player_Win_Rate_Equivalent', y='Bot_Type', data=fpa_summary, palette="coolwarm_r")
        plt.axvline(x=0.5, color='black', linestyle='--', label='No Advantage (0.5)')
        plt.title('First Player Advantage (Win+0.5*Draw Rate) by Bot Type', fontsize=16)
        plt.xlabel('First Player Score Rate (Win=1, Draw=0.5, Loss=0)', fontsize=12)
        plt.ylabel('Bot Type (of First Player)', fontsize=12)
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(results_dir, "first_player_advantage.png"), dpi=300)
        plt.close()

    # --- Generate Interesting Records Text File ---
    print("Generating interesting records...")
    with open(os.path.join(results_dir, "interesting_records.txt"), 'w') as f:
        f.write("INTERESTING TOURNAMENT RECORDS\n")
        f.write("============================\n\n")
        f.write(f"Elo Calculation Parameters:\n")
        f.write(f"  Initial Elo: {INITIAL_ELO}\n")
        f.write(f"  Number of Passes: {NUM_ELO_PASSES}\n")
        f.write(f"  K-Factor Range: {K_FACTOR_START} (start) to {K_FACTOR_END} (end)\n\n")

        strongest_bot = elo_df.iloc[0]
        f.write(
            f"Strongest Bot: {strongest_bot['Bot']} (ELO: {strongest_bot['Elo']:.1f}, Type: {strongest_bot['Bot_Type']})\n\n")

        f.write("Strongest Bot by Type:\n")
        for bot_type in elo_df['Bot_Type'].unique():
            type_df = elo_df[elo_df['Bot_Type'] == bot_type].sort_values('Elo', ascending=False)
            if not type_df.empty:
                s_bot = type_df.iloc[0]
                f.write(f"  {bot_type}: {s_bot['Bot']} (ELO: {s_bot['Elo']:.1f}, Overall Rank: {s_bot['Rank']})\n")
        f.write("\n")

        # Most draws (bot)
        most_draws_bot_series = stats_df.loc[stats_df['draws'].idxmax()]
        f.write(
            f"Bot with Most Draws: {most_draws_bot_series['Bot']} ({most_draws_bot_series['draws']} draws, Draw Rate: {most_draws_bot_series['draw_rate']:.2%})\n")

        # Most decisive (fewest draws relative to games played, min 20 games)
        decisive_candidates = stats_df[stats_df['games_played'] >= 20].copy()
        if not decisive_candidates.empty:
            most_decisive_bot_series = decisive_candidates.loc[decisive_candidates['draw_rate'].idxmin()]
            f.write(
                f"Most Decisive Bot (min 20 games): {most_decisive_bot_series['Bot']} (Draw Rate: {most_decisive_bot_series['draw_rate']:.2%})\n\n")

        # Biggest Upset (single game)
        biggest_upset_game = None
        max_elo_diff_upset = -1

        for _, game_row in games_df.iterrows():
            p_o, p_x = game_row['player_O'], game_row['player_X']
            winner = game_row['winner']

            elo_p_o = elo_df.loc[elo_df['Bot'] == p_o, 'Elo'].iloc[0]
            elo_p_x = elo_df.loc[elo_df['Bot'] == p_x, 'Elo'].iloc[0]

            if winner == p_o and elo_p_o < elo_p_x:  # Player O won despite lower Elo
                elo_diff = elo_p_x - elo_p_o
                if elo_diff > max_elo_diff_upset:
                    max_elo_diff_upset = elo_diff
                    biggest_upset_game = {
                        'winner': p_o, 'winner_elo': elo_p_o,
                        'loser': p_x, 'loser_elo': elo_p_x,
                        'diff': elo_diff, 'game_id': game_row['game_global_id']
                    }
            elif winner == p_x and elo_p_x < elo_p_o:  # Player X won despite lower Elo
                elo_diff = elo_p_o - elo_p_x
                if elo_diff > max_elo_diff_upset:
                    max_elo_diff_upset = elo_diff
                    biggest_upset_game = {
                        'winner': p_x, 'winner_elo': elo_p_x,
                        'loser': p_o, 'loser_elo': elo_p_o,
                        'diff': elo_diff, 'game_id': game_row['game_global_id']
                    }

        if biggest_upset_game:
            f.write("Biggest Upset (Single Game):\n")
            f.write(f"  Game ID: {biggest_upset_game['game_id']}\n")
            f.write(f"  Winner: {biggest_upset_game['winner']} (Elo: {biggest_upset_game['winner_elo']:.1f})\n")
            f.write(f"  Loser: {biggest_upset_game['loser']} (Elo: {biggest_upset_game['loser_elo']:.1f})\n")
            f.write(f"  Elo Difference Overcome: {biggest_upset_game['diff']:.1f} points\n\n")

        # Closest Rivalry (Pair of bots with most balanced win/loss over many games)
        # Using matches_df for this
        if not matches_df.empty:
            matches_df_min_games = matches_df[
                matches_df['total_games_in_match'] >= 10].copy()  # Min 10 games for a rivalry
            if not matches_df_min_games.empty:
                matches_df_min_games['score_diff_abs'] = abs(
                    matches_df_min_games['bot1_wins'] - matches_df_min_games['bot2_wins'])
                matches_df_min_games['balance_metric'] = matches_df_min_games['score_diff_abs'] / matches_df_min_games[
                    'total_games_in_match']

                closest_rivalry_series = matches_df_min_games.sort_values(by=['balance_metric', 'total_games_in_match'],
                                                                          ascending=[True, False]).iloc[0]
                f.write("Closest Rivalry (min 10 games, most balanced W/L ratio):\n")
                f.write(f"  Bots: {closest_rivalry_series['bot1']} vs {closest_rivalry_series['bot2']}\n")
                f.write(
                    f"  Score: {closest_rivalry_series['bot1_wins']} (Bot1) - {closest_rivalry_series['bot2_wins']} (Bot2) - {closest_rivalry_series['draws']} (Draws)\n")
                f.write(f"  Total Games: {closest_rivalry_series['total_games_in_match']}\n")
                f.write(
                    f"  Balance Metric (abs_score_diff/total_games): {closest_rivalry_series['balance_metric']:.3f}\n\n")

    print("Analysis complete. Results saved to " + results_dir)
    return results_dir


# --- Main Execution ---
def main():
    parser = argparse.ArgumentParser(
        description="Analyze tournament game results, calculate Elo, and generate stats/visualizations.")
    parser.add_argument("--output_base", type=str, default="tournament_analysis",
                        help="Base name for the output directory.")
    json_file_path = r'C:\Dev\Python\Puissance4-L1ST\tournament_raw_games_20250509_215643\all_games_results_20250509_215643.json'
    args = parser.parse_args()

    if not os.path.exists(json_file_path):
        print(f"Error: JSON file not found at {json_file_path}")
        return

    print(f"Loading game data from: {json_file_path}")
    with open(json_file_path, 'r') as f:
        all_games_data = json.load(f)

    if not all_games_data:
        print("Error: No game data loaded from the JSON file.")
        return
    print(f"Loaded {len(all_games_data)} game records.")

    # Extract all unique bot names from the game data
    all_bot_names = set()
    for game in all_games_data:
        all_bot_names.add(game["player_O"])
        all_bot_names.add(game["player_X"])
    all_bot_names = sorted(list(all_bot_names))
    print(f"Found {len(all_bot_names)} unique bot participants in the games.")

    # 1. Calculate Elo Ratings
    final_elo_ratings, elo_history = run_elo_calculation_passes(all_games_data, all_bot_names)

    # 2. Aggregate Bot Statistics
    print("Aggregating bot statistics...")
    bot_stats_aggregated = aggregate_bot_statistics(all_games_data, all_bot_names)
    print("Statistics aggregation finished.")

    # 3. Save results and generate visualizations
    save_results_and_visualize(args.output_base, final_elo_ratings, bot_stats_aggregated, all_games_data, elo_history)


if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    print(f"Total analysis script execution time: {end_time - start_time:.2f} seconds.")