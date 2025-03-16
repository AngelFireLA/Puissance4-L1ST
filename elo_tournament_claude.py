import os
import time
import random
import math
import csv
import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime
from collections import defaultdict, Counter
import seaborn as sns
from tqdm import tqdm
import elo_tournament_setup as setup

# Constants
ELO_K_FACTOR = 32
ELO_DEFAULT = 1200
MAX_WORKERS = None  # Set to number of cores or leave as None for auto

# Directory structure
BASE_DIR = "tournament_results"
DIRECTORIES = {
    "single_knockout": f"{BASE_DIR}/single_knockout",
    "double_knockout": f"{BASE_DIR}/double_knockout",
    "round_robin": f"{BASE_DIR}/round_robin",
    "swiss": f"{BASE_DIR}/swiss",
    "stats": f"{BASE_DIR}/stats",
    "charts": f"{BASE_DIR}/charts"
}


# Create directories
def create_directories():
    for directory in DIRECTORIES.values():
        os.makedirs(directory, exist_ok=True)


class MatchResult:
    def __init__(self, player1, player2, result, player1_first=True):
        """
        Store result of a match between two players
        result: "player1", "player2", or "draw"
        """
        self.player1 = player1
        self.player2 = player2
        self.result = result
        self.player1_first = player1_first
        self.timestamp = datetime.now()

    def winner(self):
        if self.result == "player1":
            return self.player1
        elif self.result == "player2":
            return self.player2
        return None

    def loser(self):
        if self.result == "player1":
            return self.player2
        elif self.result == "player2":
            return self.player1
        return None


class TournamentStats:
    def __init__(self):
        self.elo_ratings = {}
        self.wins = defaultdict(int)
        self.losses = defaultdict(int)
        self.draws = defaultdict(int)
        self.first_player_wins = defaultdict(int)
        self.second_player_wins = defaultdict(int)
        self.match_history = []
        self.game_length = defaultdict(list)
        self.bot_types = {}
        self.execution_times = defaultdict(list)

    def initialize_elo(self, participants):
        """Initialize ELO ratings for all participants"""
        for bot in participants:
            self.elo_ratings[bot.nom] = ELO_DEFAULT

            # Categorize bots by type
            if "Negamax" in bot.nom:
                if "Negamax P" in bot.nom and "Negamax2" not in bot.nom and "Negamax3" not in bot.nom and "Negamax4" not in bot.nom and "Negamax5" not in bot.nom:
                    self.bot_types[bot.nom] = "Negamax"
                elif "Negamax2" in bot.nom:
                    self.bot_types[bot.nom] = "Negamax2"
                elif "Negamax3" in bot.nom:
                    self.bot_types[bot.nom] = "Negamax3"
                elif "Negamax4" in bot.nom:
                    self.bot_types[bot.nom] = "Negamax4"
                elif "Negamax5" in bot.nom and "Negamax5B" not in bot.nom:
                    self.bot_types[bot.nom] = "Negamax5"
                elif "Negamax5B" in bot.nom:
                    self.bot_types[bot.nom] = "Negamax5B"
            elif "Neural Bot" in bot.nom:
                self.bot_types[bot.nom] = "Neural"
            elif "Random" in bot.nom:
                self.bot_types[bot.nom] = "Random"
            elif "Default" in bot.nom:
                self.bot_types[bot.nom] = "Default"
            else:
                self.bot_types[bot.nom] = "Other"

    def update_elo(self, player1, player2, result):
        """Update ELO ratings based on match result"""
        # Get current ratings
        r1 = self.elo_ratings[player1.nom]
        r2 = self.elo_ratings[player2.nom]

        # Calculate expected scores
        e1 = 1 / (1 + 10 ** ((r2 - r1) / 400))
        e2 = 1 / (1 + 10 ** ((r1 - r2) / 400))

        # Calculate actual scores
        if result == "player1":
            s1, s2 = 1, 0
        elif result == "player2":
            s1, s2 = 0, 1
        else:  # draw
            s1, s2 = 0.5, 0.5

        # Update ratings
        self.elo_ratings[player1.nom] = r1 + ELO_K_FACTOR * (s1 - e1)
        self.elo_ratings[player2.nom] = r2 + ELO_K_FACTOR * (s2 - e2)

    def record_match(self, match_result):
        """Record match result and update stats"""
        player1 = match_result.player1
        player2 = match_result.player2
        result = match_result.result
        player1_first = match_result.player1_first

        self.match_history.append(match_result)
        self.update_elo(player1, player2, result)

        if result == "player1":
            self.wins[player1.nom] += 1
            self.losses[player2.nom] += 1
            if player1_first:
                self.first_player_wins[player1.nom] += 1
            else:
                self.second_player_wins[player1.nom] += 1
        elif result == "player2":
            self.wins[player2.nom] += 1
            self.losses[player1.nom] += 1
            if not player1_first:
                self.first_player_wins[player2.nom] += 1
            else:
                self.second_player_wins[player2.nom] += 1
        else:  # draw
            self.draws[player1.nom] += 1
            self.draws[player2.nom] += 1

    def get_win_percentage(self, bot_name):
        """Calculate win percentage for a bot"""
        total_games = self.wins[bot_name] + self.losses[bot_name] + self.draws[bot_name]
        if total_games == 0:
            return 0
        return (self.wins[bot_name] + 0.5 * self.draws[bot_name]) / total_games * 100

    def get_win_ratio(self, bot_name):
        """Calculate W/L ratio for a bot"""
        if self.losses[bot_name] == 0:
            return float('inf') if self.wins[bot_name] > 0 else 0
        return self.wins[bot_name] / self.losses[bot_name]

    def get_rankings(self):
        """Get sorted rankings based on ELO"""
        return sorted(self.elo_ratings.items(), key=lambda x: x[1], reverse=True)

    def get_first_move_advantage_stats(self):
        """Calculate first-move advantage statistics"""
        total_first_wins = sum(self.first_player_wins.values())
        total_second_wins = sum(self.second_player_wins.values())
        total_games = total_first_wins + total_second_wins + sum(self.draws.values())

        if total_games == 0:
            return {
                "first_win_percentage": 0,
                "second_win_percentage": 0,
                "draw_percentage": 0
            }

        return {
            "first_win_percentage": (total_first_wins / total_games) * 100,
            "second_win_percentage": (total_second_wins / total_games) * 100,
            "draw_percentage": (sum(self.draws.values()) / 2 / total_games) * 100
        }

    def get_bot_type_performance(self):
        """Get performance statistics by bot type"""
        type_wins = defaultdict(int)
        type_losses = defaultdict(int)
        type_draws = defaultdict(int)
        type_elo = defaultdict(list)

        for bot_name, bot_type in self.bot_types.items():
            type_wins[bot_type] += self.wins[bot_name]
            type_losses[bot_type] += self.losses[bot_name]
            type_draws[bot_type] += self.draws[bot_name]
            type_elo[bot_type].append(self.elo_ratings[bot_name])

        type_avg_elo = {bot_type: sum(elos) / len(elos) for bot_type, elos in type_elo.items()}
        type_win_rate = {}

        for bot_type in type_wins.keys():
            games = type_wins[bot_type] + type_losses[bot_type] + type_draws[bot_type]
            if games == 0:
                type_win_rate[bot_type] = 0
            else:
                type_win_rate[bot_type] = (type_wins[bot_type] + 0.5 * type_draws[bot_type]) / games * 100

        return {
            "type_wins": dict(type_wins),
            "type_losses": dict(type_losses),
            "type_draws": dict(type_draws),
            "type_win_rate": dict(type_win_rate),
            "type_avg_elo": dict(type_avg_elo)
        }


class Tournament:
    def __init__(self, participants, stats=None):
        self.participants = participants
        self.stats = stats if stats else TournamentStats()
        if not self.stats.elo_ratings:
            self.stats.initialize_elo(participants)

    def play_match(self, player1, player2, return_match=True):
        """
        Play a match between two players, then reverse and play again if return_match is True
        Returns tuple (match1_result, match2_result) where match2_result may be None
        """
        start_time = time.time()
        result1 = setup.une_partie(player1, player2)

        # Map the result to player1/player2/draw format
        if result1 == "bot1":
            match_result1 = MatchResult(player1, player2, "player1", player1_first=True)
        elif result1 == "bot2":
            match_result1 = MatchResult(player1, player2, "player2", player1_first=True)
        else:  # nul
            match_result1 = MatchResult(player1, player2, "draw", player1_first=True)

        self.stats.record_match(match_result1)

        # Play return match with players swapped
        match_result2 = None
        if return_match:
            result2 = setup.une_partie(player2, player1)

            if result2 == "bot1":
                match_result2 = MatchResult(player2, player1, "player1", player1_first=True)
            elif result2 == "bot2":
                match_result2 = MatchResult(player2, player1, "player2", player1_first=True)
            else:  # nul
                match_result2 = MatchResult(player2, player1, "draw", player1_first=True)

            self.stats.record_match(match_result2)

        end_time = time.time()
        execution_time = end_time - start_time
        self.stats.execution_times[player1.nom].append(execution_time / (2 if return_match else 1))
        self.stats.execution_times[player2.nom].append(execution_time / (2 if return_match else 1))

        return match_result1, match_result2

    def play_match_parallel(self, matches):
        """
        Play multiple matches in parallel.
        matches: list of tuples (player1, player2, return_match)
        Returns a list of tuples (first_match_result, second_match_result) where
        second_match_result is None if no return match was scheduled.
        """
        # We'll store data for each match in a dictionary keyed by a unique match identifier.
        # For simplicity, we use (player1.nom, player2.nom) as the match key.
        # results_info = []  # List to hold (match_key, is_first_match, match_result)
        #
        # with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        #     future_to_match = {}
        #     # Submit all matches with metadata
        #     for player1, player2, return_match in matches:
        #         match_key = (player1.nom, player2.nom)
        #         # Submit the first match (as given)
        #         future = executor.submit(setup.une_partie, player1, player2)
        #         future_to_match[future] = (match_key, True, player1, player2)
        #         # Submit the return match if needed (players are swapped)
        #         if return_match:
        #             future = executor.submit(setup.une_partie, player2, player1)
        #             future_to_match[future] = (match_key, False, player1, player2)
        #
        #     # Process futures as they complete
        #     for future in concurrent.futures.as_completed(future_to_match):
        #         match_key, is_first_match, player1, player2 = future_to_match[future]
        #         result = future.result()
        #
        #         if is_first_match:
        #             # For the first match, players remain in the same order.
        #             if result == "bot1":
        #                 match_result = MatchResult(player1, player2, "player1", player1_first=True)
        #             elif result == "bot2":
        #                 match_result = MatchResult(player1, player2, "player2", player1_first=True)
        #             else:
        #                 match_result = MatchResult(player1, player2, "draw", player1_first=True)
        #         else:
        #             # For the return match, players are swapped.
        #             if result == "bot1":
        #                 match_result = MatchResult(player2, player1, "player1", player1_first=True)
        #             elif result == "bot2":
        #                 match_result = MatchResult(player2, player1, "player2", player1_first=True)
        #             else:
        #                 match_result = MatchResult(player2, player1, "draw", player1_first=True)
        #
        #         self.stats.record_match(match_result)
        #         results_info.append((match_key, is_first_match, match_result))
        #
        # # Reassemble the results by grouping them with their match_key.
        # match_results_by_key = {}
        # for key, is_first, match_result in results_info:
        #     if key not in match_results_by_key:
        #         match_results_by_key[key] = {}
        #     if is_first:
        #         match_results_by_key[key]['first'] = match_result
        #     else:
        #         match_results_by_key[key]['second'] = match_result
        #
        # # Reconstruct the list of match result tuples in the same order as the original matches list.
        # restructured_results = []
        # for player1, player2, return_match in matches:
        #     key = (player1.nom, player2.nom)
        #     first_match = match_results_by_key.get(key, {}).get('first', None)
        #     second_match = match_results_by_key.get(key, {}).get('second', None) if return_match else None
        #     restructured_results.append((first_match, second_match))
        #
        # return restructured_results
        results = []
        for player1, player2, return_match in matches:
            match_result1, match_result2 = self.play_match(player1, player2, return_match)
            print(player1.nom, player2.nom, match_result1.result, match_result2.result if match_result2 else None)
            results.append((match_result1, match_result2))
        return results

    def get_bot_by_name(self, name):
        """Helper to find bot by name"""
        for bot in self.participants:
            if bot.nom == name:
                return bot
        return None


class SingleKnockoutTournament(Tournament):
    def __init__(self, participants, stats=None):
        super().__init__(participants, stats)
        self.matches = []
        self.rounds = []
        self.bracket = []

    def run_tournament(self):
        """Run a single-elimination knockout tournament"""
        print("Starting Single Knockout Tournament")

        # Make sure we have a power of 2 number of participants
        num_participants = len(self.participants)
        next_power_of_2 = 2 ** math.ceil(math.log2(num_participants))

        # If not power of 2, some players get a bye in the first round
        players = self.participants.copy()
        random.shuffle(players)  # Randomize seeding

        # Add byes to make it a power of 2
        byes_needed = next_power_of_2 - num_participants
        self.bracket = []

        # Create first round with byes
        first_round = []
        players_with_byes = []

        for i in range(0, num_participants - byes_needed, 2):
            first_round.append((players[i], players[i + 1]))

        for i in range(num_participants - byes_needed, num_participants):
            players_with_byes.append(players[i])

        self.rounds = [first_round]
        self.bracket = self.rounds.copy()

        # Play the tournament rounds
        active_players = []

        # Play first round
        results = []
        match_pairs = []
        for player1, player2 in tqdm(first_round, desc="First round"):
            match_pairs.append((player1, player2, True))

        match_results = self.play_match_parallel(match_pairs)

        for ((p1, p2), (match1, match2)) in zip(first_round, match_results):
            # Determine winner based on both matches
            winner = self.determine_winner(match1, match2)
            if winner:
                print(p1.nom, p2.nom, winner.nom)
                active_players.append(winner)
            self.matches.append((match1, match2))
            results.append((p1, p2, winner))

        # Add players with byes
        active_players.extend(players_with_byes)

        # Continue with subsequent rounds
        round_number = 1
        while len(active_players) > 1:
            print(f"Round {round_number + 1}: {len(active_players)} players remaining")
            next_round = []
            results = []
            match_pairs = []

            for i in range(0, len(active_players), 2):
                if i + 1 < len(active_players):
                    next_round.append((active_players[i], active_players[i + 1]))
                    match_pairs.append((active_players[i], active_players[i + 1], True))
                else:
                    # Odd number of players, last one gets a bye
                    active_players.append(active_players[i])
                    break

            self.rounds.append(next_round)
            self.bracket.append(next_round)

            if match_pairs:  # Only play matches if we have pairs
                match_results = self.play_match_parallel(match_pairs)

                active_players = []
                for ((p1, p2), (match1, match2)) in zip(next_round, match_results):
                    winner = self.determine_winner(match1, match2)
                    if winner:
                        active_players.append(winner)
                    self.matches.append((match1, match2))
                    results.append((p1, p2, winner))

            round_number += 1

        print(f"Tournament complete. Winner: {active_players[0].nom}")
        return active_players[0]  # Return winner

    def determine_winner(self, match1, match2):
        """
        Determine overall winner based on two matches
        Returns the winning player or None for a draw
        """
        # Count wins for each player
        p1_wins = 0
        p2_wins = 0

        if match1.result == "player1":
            p1_wins += 1
        elif match1.result == "player2":
            p2_wins += 1

        if match2:
            if match2.result == "player1":
                p2_wins += 1  # Players are swapped in match2
            elif match2.result == "player2":
                p1_wins += 1  # Players are swapped in match2

        if p1_wins > p2_wins:
            print(match1.player1.nom, "has won because it has won", p1_wins, "matches compared to", match1.player2.nom, "which has won", p2_wins, "matches")
            return match1.player1
        elif p2_wins > p1_wins:
            print(match1.player2.nom, "has won because it has won", p2_wins, "matches compared to", match1.player1.nom, "which has won", p1_wins, "matches")
            return match1.player2
        else:
            # If tied, choose based on ELO
            if self.stats.elo_ratings[match1.player1.nom] >= self.stats.elo_ratings[match1.player2.nom]:
                print(match1.player1.nom, "has won because it has a higher elo of", self.stats.elo_ratings[match1.player1.nom], "compared to the elo of", match1.player2.nom, "which is", self.stats.elo_ratings[match1.player2.nom])
                return match1.player1
            else:
                print(match1.player2.nom, "has won because it has a higher elo of", self.stats.elo_ratings[match1.player2.nom], "compared to the elo of", match1.player1.nom, "which is", self.stats.elo_ratings[match1.player1.nom])
                return match1.player2


class DoubleKnockoutTournament(Tournament):
    def __init__(self, participants, stats=None):
        super().__init__(participants, stats)
        self.matches = []
        self.winners_bracket = []
        self.losers_bracket = []

    def run_tournament(self):
        """Run a double-elimination knockout tournament"""
        print("Starting Double Knockout Tournament")

        # Shuffle participants for random seeding
        players = self.participants.copy()
        random.shuffle(players)

        # Initialize winners and losers brackets
        winners = players.copy()
        losers = []

        round_number = 1
        while len(winners) > 1 or len(losers) > 1:
            print(f"Round {round_number}")

            # Process winners bracket
            if len(winners) > 1:
                winners_matches = []
                new_winners = []
                new_losers = []

                # Create winner bracket matches
                for i in range(0, len(winners), 2):
                    if i + 1 < len(winners):
                        winners_matches.append((winners[i], winners[i + 1], True))
                    else:
                        # Bye for odd number of players
                        new_winners.append(winners[i])

                winners_results = self.play_match_parallel(winners_matches)
                self.winners_bracket.append(winners_matches)

                for ((p1, p2, _), (match1, match2)) in zip(winners_matches, winners_results):
                    winner = self.determine_winner(match1, match2)
                    loser = p1 if winner == p2 else p2
                    new_winners.append(winner)
                    new_losers.append(loser)
                    self.matches.append((match1, match2))

                winners = new_winners
                losers.extend(new_losers)

            # Process losers bracket
            if len(losers) > 1:
                losers_matches = []
                new_losers = []

                # Create loser bracket matches
                for i in range(0, len(losers), 2):
                    if i + 1 < len(losers):
                        losers_matches.append((losers[i], losers[i + 1], True))
                    else:
                        # Bye for odd number of players
                        new_losers.append(losers[i])

                self.losers_bracket.append(losers_matches)

                if losers_matches:  # Only play matches if we have pairs
                    losers_results = self.play_match_parallel(losers_matches)

                    for ((p1, p2, _), (match1, match2)) in zip(losers_matches, losers_results):
                        winner = self.determine_winner(match1, match2)
                        new_losers.append(winner)
                        self.matches.append((match1, match2))

                losers = new_losers

            round_number += 1

            # Break if we have our finalists
            if len(winners) == 1 and len(losers) <= 1:
                break

        # Final match between winners bracket champion and losers bracket champion
        if losers:  # If there's a losers bracket finalist
            print("Championship Final")
            winner_champ = winners[0]
            loser_champ = losers[0]

            # Losers bracket finalist must win twice (since winners bracket finalist hasn't lost yet)
            # First championship match
            match1, match2 = self.play_match(winner_champ, loser_champ, True)
            winner = self.determine_winner(match1, match2)
            self.matches.append((match1, match2))

            if winner == loser_champ:
                # If losers bracket champ wins, play a final deciding match
                print("Championship Final - Deciding Match")
                match1, match2 = self.play_match(winner_champ, loser_champ, True)
                winner = self.determine_winner(match1, match2)
                self.matches.append((match1, match2))

            print(f"Tournament complete. Winner: {winner.nom}")
            return winner
        else:
            # If no losers bracket finalist, winners bracket champion wins by default
            print(f"Tournament complete. Winner: {winners[0].nom}")
            return winners[0]

    def determine_winner(self, match1, match2):
        """
        Determine overall winner based on two matches
        Returns the winning player or None for a draw
        """
        # Count wins for each player
        p1_wins = 0
        p2_wins = 0

        if match1.result == "player1":
            p1_wins += 1
        elif match1.result == "player2":
            p2_wins += 1

        if match2:
            if match2.result == "player1":
                p2_wins += 1  # Players are swapped in match2
            elif match2.result == "player2":
                p1_wins += 1  # Players are swapped in match2

        if p1_wins > p2_wins:
            return match1.player1
        elif p2_wins > p1_wins:
            return match1.player2
        else:
            # If tied, choose based on ELO
            if self.stats.elo_ratings[match1.player1.nom] >= self.stats.elo_ratings[match1.player2.nom]:
                return match1.player1
            else:
                return match1.player2


class RoundRobinTournament(Tournament):
    def __init__(self, participants, stats=None):
        super().__init__(participants, stats)
        self.matches = []
        self.results_table = {}

    def run_tournament(self):
        """Run a round-robin (league) tournament where each bot plays against every other bot"""
        print("Starting Round Robin Tournament")

        players = self.participants.copy()
        n = len(players)

        # Initialize results table
        for p1 in players:
            self.results_table[p1.nom] = {}
            for p2 in players:
                if p1 != p2:
                    self.results_table[p1.nom][p2.nom] = {"wins": 0, "losses": 0, "draws": 0, "points": 0}

        # Create all match pairings
        all_matches = []
        for i in range(n):
            for j in range(i + 1, n):
                all_matches.append((players[i], players[j], True))

        # Play all matches
        total_matches = len(all_matches)
        print(f"Playing {total_matches} matches ({total_matches * 2} games including return matches)...")

        # Play in batches to avoid memory issues
        batch_size = 50  # Adjust based on your system's capabilities
        for i in range(0, total_matches, batch_size):
            batch = all_matches[i:i + batch_size]
            match_results = self.play_match_parallel(batch)

            for ((p1, p2, _), (match1, match2)) in zip(batch, match_results):
                # Process results
                self.matches.append((match1, match2))

                # Update results table
                if match1.result == "player1":
                    self.results_table[p1.nom][p2.nom]["wins"] += 1
                    self.results_table[p2.nom][p1.nom]["losses"] += 1
                    self.results_table[p1.nom][p2.nom]["points"] += 3
                elif match1.result == "player2":
                    self.results_table[p1.nom][p2.nom]["losses"] += 1
                    self.results_table[p2.nom][p1.nom]["wins"] += 1
                    self.results_table[p2.nom][p1.nom]["points"] += 3
                else:  # draw
                    self.results_table[p1.nom][p2.nom]["draws"] += 1
                    self.results_table[p2.nom][p1.nom]["draws"] += 1
                    self.results_table[p1.nom][p2.nom]["points"] += 1
                    self.results_table[p2.nom][p1.nom]["points"] += 1

                if match2:  # Process the return match
                    if match2.result == "player1":
                        self.results_table[p2.nom][p1.nom]["wins"] += 1
                        self.results_table[p1.nom][p2.nom]["losses"] += 1
                        self.results_table[p2.nom][p1.nom]["points"] += 3
                    elif match2.result == "player2":
                        self.results_table[p2.nom][p1.nom]["losses"] += 1
                        self.results_table[p1.nom][p2.nom]["wins"] += 1
                        self.results_table[p1.nom][p2.nom]["points"] += 3
                    else:  # draw
                        self.results_table[p2.nom][p1.nom]["draws"] += 1
                        self.results_table[p1.nom][p2.nom]["draws"] += 1
                        self.results_table[p2.nom][p1.nom]["points"] += 1
                        self.results_table[p1.nom][p2.nom]["points"] += 1
            print(f"Completed {min(i + batch_size, total_matches)}/{total_matches} matches")
        # Calculate total points and determine winner
        points = {}
        for player in players:
            total_points = 0
            for opponent in players:
                if player != opponent:
                    total_points += self.results_table[player.nom][opponent.nom]["points"]
            points[player.nom] = total_points

        # Sort by points
        sorted_results = sorted(points.items(), key=lambda x: x[1], reverse=True)
        winner_name = sorted_results[0][0]
        winner = self.get_bot_by_name(winner_name)

        print(f"Tournament complete. Winner: {winner.nom} with {points[winner.nom]} points")
        return winner, sorted_results


class SwissTournament(Tournament):
    def __init__(self, participants, stats=None, num_rounds=None):
        super().__init__(participants, stats)
        self.matches = []
        self.standings = {}
        # If no round count specified, use log2(n) rounded up
        self.num_rounds = num_rounds or math.ceil(math.log2(len(participants)))

    def run_tournament(self):
        """Run a Swiss-style tournament"""
        print(f"Starting Swiss Tournament with {self.num_rounds} rounds")

        players = self.participants.copy()

        # Initialize standings
        for player in players:
            self.standings[player.nom] = {
                "player": player,
                "score": 0,
                "opponents": [],
                "results": []
            }

        # Run each round
        for round_num in range(1, self.num_rounds + 1):
            print(f"Round {round_num}/{self.num_rounds}")

            # Pair players based on current standings
            pairings = self.pair_players_for_round(round_num)

            # Play matches
            match_pairs = [(p1, p2, True) for p1, p2 in pairings]
            match_results = self.play_match_parallel(match_pairs)

            # Process results
            for ((p1, p2), (match1, match2)) in zip(pairings, match_results):
                print(p1.nom, p2.nom, match1.result, match2.result if match2 else None)
                self.matches.append((match1, match2))

                # Determine points (2 for win, 1 for draw, 0 for loss)
                # Score from match 1
                if match1.result == "player1":
                    self.standings[p1.nom]["score"] += 1
                elif match1.result == "player2":
                    self.standings[p2.nom]["score"] += 1
                else:  # draw
                    self.standings[p1.nom]["score"] += 0.5
                    self.standings[p2.nom]["score"] += 0.5

                # Score from match 2
                if match2.result == "player1":
                    self.standings[p2.nom]["score"] += 1  # Players are swapped
                elif match2.result == "player2":
                    self.standings[p1.nom]["score"] += 1  # Players are swapped
                else:  # draw
                    self.standings[p1.nom]["score"] += 0.5
                    self.standings[p2.nom]["score"] += 0.5

                # Record opponents
                self.standings[p1.nom]["opponents"].append(p2.nom)
                self.standings[p2.nom]["opponents"].append(p1.nom)

                # Record results
                self.standings[p1.nom]["results"].append(
                    2 if match1.result == "player1" else (1 if match1.result == "draw" else 0))
                self.standings[p1.nom]["results"].append(
                    2 if match2.result == "player2" else (1 if match2.result == "draw" else 0))
                self.standings[p2.nom]["results"].append(
                    2 if match1.result == "player2" else (1 if match1.result == "draw" else 0))
                self.standings[p2.nom]["results"].append(
                    2 if match2.result == "player1" else (1 if match2.result == "draw" else 0))

        # Determine final standings
        final_standings = sorted(
            self.standings.items(),
            key=lambda x: (x[1]["score"], self.calculate_buchholz(x[0])),
            reverse=True
        )

        winner_name = final_standings[0][0]
        winner = self.get_bot_by_name(winner_name)

        print(f"Tournament complete. Winner: {winner.nom} with {self.standings[winner.nom]['score']} points")
        return winner, final_standings

    def pair_players_for_round(self, round_num):
        """Pair players for a Swiss tournament round"""
        # Sort by current score, then by rating
        sorted_players = sorted(
            self.standings.items(),
            key=lambda x: (x[1]["score"], self.stats.elo_ratings[x[0]]),
            reverse=True
        )

        if round_num == 1:
            # For first round, just pair by initial rating
            pairs = []
            players = [p[1]["player"] for p in sorted_players]
            for i in range(0, len(players), 2):
                if i + 1 < len(players):
                    pairs.append((players[i], players[i + 1]))
            return pairs

        # For subsequent rounds, use Swiss pairing algorithm
        remaining_players = [p[1]["player"] for p in sorted_players]
        pairs = []

        while remaining_players:
            current = remaining_players.pop(0)

            # Find best opponent from remaining players
            best_opponent = None
            best_opponent_idx = -1

            for i, candidate in enumerate(remaining_players):
                # Skip if already played against this opponent
                if candidate.nom in self.standings[current.nom]["opponents"]:
                    continue

                # Found valid opponent
                best_opponent = candidate
                best_opponent_idx = i
                break

            if best_opponent is None:
                # If no valid opponent found, just take the next player
                # (this is suboptimal but prevents infinite loops)
                if remaining_players:
                    best_opponent = remaining_players.pop(0)
                    pairs.append((current, best_opponent))
            else:
                # Remove selected opponent and add pair
                remaining_players.pop(best_opponent_idx)
                pairs.append((current, best_opponent))

        return pairs

    def calculate_buchholz(self, player_name):
        """Calculate Buchholz score (sum of opponents' scores) for tiebreaker"""
        buchholz = 0
        for opponent_name in self.standings[player_name]["opponents"]:
            buchholz += self.standings[opponent_name]["score"]
        return buchholz


class TournamentAnalyzer:
    def __init__(self, stats, tournament_type):
        self.stats = stats
        self.tournament_type = tournament_type
        self.output_dir = DIRECTORIES[tournament_type]

    def generate_reports(self):
        """Generate comprehensive reports"""
        self.save_overall_rankings()
        self.save_detailed_stats()
        self.save_match_history()
        self.save_type_performance()
        self.plot_elo_distribution()
        self.plot_win_rates()
        self.plot_first_move_advantage()
        self.plot_bot_type_comparison()
        self.plot_execution_times()

        # Copy main summary to stats directory
        self.copy_rankings_to_stats_dir()

    def save_overall_rankings(self):
        """Save overall rankings to CSV"""
        rankings = self.stats.get_rankings()

        with open(f"{self.output_dir}/rankings.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Rank", "Bot", "ELO", "Wins", "Losses", "Draws", "Win %", "W/L Ratio"])

            for rank, (bot_name, elo) in enumerate(rankings, 1):
                wins = self.stats.wins[bot_name]
                losses = self.stats.losses[bot_name]
                draws = self.stats.draws[bot_name]
                win_pct = self.stats.get_win_percentage(bot_name)
                wl_ratio = self.stats.get_win_ratio(bot_name)

                writer.writerow([
                    rank, bot_name, round(elo, 1), wins, losses, draws,
                    f"{win_pct:.2f}%", f"{wl_ratio:.3f}"
                ])

    def save_detailed_stats(self):
        """Save detailed statistics about each bot"""
        with open(f"{self.output_dir}/detailed_stats.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Bot", "ELO", "Wins", "Losses", "Draws", "Win %", "W/L Ratio",
                "First Player Wins", "Second Player Wins", "Bot Type", "Avg Execution Time (s)"
            ])

            for bot_name in sorted(self.stats.elo_ratings.keys()):
                wins = self.stats.wins[bot_name]
                losses = self.stats.losses[bot_name]
                draws = self.stats.draws[bot_name]
                win_pct = self.stats.get_win_percentage(bot_name)
                wl_ratio = self.stats.get_win_ratio(bot_name)
                first_wins = self.stats.first_player_wins[bot_name]
                second_wins = self.stats.second_player_wins[bot_name]
                bot_type = self.stats.bot_types.get(bot_name, "Unknown")

                exec_times = self.stats.execution_times.get(bot_name, [0])
                avg_time = sum(exec_times) / len(exec_times) if exec_times else 0

                writer.writerow([
                    bot_name, round(self.stats.elo_ratings[bot_name], 1),
                    wins, losses, draws, f"{win_pct:.2f}%", f"{wl_ratio:.3f}",
                    first_wins, second_wins, bot_type, f"{avg_time:.4f}"
                ])

    def save_match_history(self):
        """Save match history to CSV"""
        with open(f"{self.output_dir}/match_history.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Player 1", "Player 2", "Result", "Player 1 First", "Timestamp"])

            for match in self.stats.match_history:
                writer.writerow([
                    match.player1.nom, match.player2.nom,
                    "Player 1 Win" if match.result == "player1" else
                    "Player 2 Win" if match.result == "player2" else "Draw",
                    match.player1_first, match.timestamp
                ])

    def save_type_performance(self):
        """Save bot type performance statistics"""
        type_stats = self.stats.get_bot_type_performance()

        with open(f"{self.output_dir}/type_performance.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Bot Type", "Total Bots", "Wins", "Losses", "Draws", "Win Rate", "Avg ELO"
            ])

            bot_type_counts = {}
            for _, bot_type in self.stats.bot_types.items():
                bot_type_counts[bot_type] = bot_type_counts.get(bot_type, 0) + 1

            for bot_type in sorted(type_stats["type_wins"].keys()):
                wins = type_stats["type_wins"][bot_type]
                losses = type_stats["type_losses"][bot_type]
                draws = type_stats["type_draws"][bot_type]
                win_rate = type_stats["type_win_rate"][bot_type]
                avg_elo = type_stats["type_avg_elo"][bot_type]
                bot_count = bot_type_counts.get(bot_type, 0)

                writer.writerow([
                    bot_type, bot_count, wins, losses, draws,
                    f"{win_rate:.2f}%", f"{avg_elo:.1f}"
                ])

    def plot_elo_distribution(self):
        """Create ELO distribution histogram"""
        plt.figure(figsize=(12, 8))

        # Group by bot type
        bot_types = set(self.stats.bot_types.values())
        type_elos = {bot_type: [] for bot_type in bot_types}

        for bot_name, elo in self.stats.elo_ratings.items():
            bot_type = self.stats.bot_types.get(bot_name, "Unknown")
            type_elos[bot_type].append(elo)

        # Plot histogram for each type
        for bot_type, elos in type_elos.items():
            if elos:  # Only plot if we have data
                plt.hist(elos, alpha=0.7, label=bot_type, bins=15)

        plt.title('ELO Rating Distribution by Bot Type', fontsize=16)
        plt.xlabel('ELO Rating', fontsize=14)
        plt.ylabel('Number of Bots', fontsize=14)
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()

        plt.savefig(f"{self.output_dir}/elo_distribution.png", dpi=300)
        plt.close()

    def plot_win_rates(self):
        """Create win rate visualization"""
        # Get top 20 bots by ELO
        top_bots = [bot for bot, _ in self.stats.get_rankings()[:20]]
        win_rates = [self.stats.get_win_percentage(bot) for bot in top_bots]

        plt.figure(figsize=(14, 10))

        # Color-code by bot type
        bot_types = [self.stats.bot_types.get(bot, "Unknown") for bot in top_bots]
        unique_types = sorted(set(bot_types))
        colors = plt.cm.tab10(np.linspace(0, 1, len(unique_types)))
        type_to_color = dict(zip(unique_types, colors))
        bar_colors = [type_to_color[bot_type] for bot_type in bot_types]

        # Create horizontal bar chart
        bars = plt.barh(top_bots, win_rates, color=bar_colors)

        # Add ELO to labels
        for i, bot in enumerate(top_bots):
            plt.text(
                win_rates[i] + 1, i,
                f"ELO: {self.stats.elo_ratings[bot]:.1f}",
                va='center', fontsize=10
            )

        # Create legend for bot types
        from matplotlib.patches import Patch
        legend_elements = [Patch(facecolor=type_to_color[t], label=t) for t in unique_types]
        plt.legend(handles=legend_elements, loc='lower right')

        plt.title('Win Rates for Top 20 Bots', fontsize=16)
        plt.xlabel('Win Percentage (%)', fontsize=14)
        plt.grid(True, alpha=0.3)
        plt.xlim(0, 100)
        plt.tight_layout()

        plt.savefig(f"{self.output_dir}/win_rates.png", dpi=300)
        plt.close()

    def plot_first_move_advantage(self):
        """Visualize first-move advantage statistics"""
        stats = self.stats.get_first_move_advantage_stats()

        plt.figure(figsize=(10, 8))

        labels = ['First Player', 'Second Player', 'Draw']
        values = [
            stats["first_win_percentage"],
            stats["second_win_percentage"],
            stats["draw_percentage"]
        ]
        colors = ['#FF9999', '#66B2FF', '#C2C2C2']

        plt.pie(
            values, labels=labels, colors=colors, autopct='%1.1f%%',
            startangle=90, shadow=True, explode=(0.05, 0.05, 0)
        )
        plt.axis('equal')
        plt.title('First vs. Second Player Advantage', fontsize=16)

        plt.savefig(f"{self.output_dir}/first_move_advantage.png", dpi=300)
        plt.close()

        # Also save as CSV
        with open(f"{self.output_dir}/first_move_advantage.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Position", "Win Percentage"])
            writer.writerow(["First Player", f"{stats['first_win_percentage']:.2f}%"])
            writer.writerow(["Second Player", f"{stats['second_win_percentage']:.2f}%"])
            writer.writerow(["Draw", f"{stats['draw_percentage']:.2f}%"])

    def plot_bot_type_comparison(self):
        """Compare performance between bot types"""
        type_stats = self.stats.get_bot_type_performance()

        plt.figure(figsize=(12, 10))

        bot_types = list(type_stats["type_avg_elo"].keys())
        avg_elos = [type_stats["type_avg_elo"][bt] for bt in bot_types]
        win_rates = [type_stats["type_win_rate"][bt] for bt in bot_types]

        # Sort by average ELO
        sorted_indices = np.argsort(avg_elos)[::-1]
        bot_types = [bot_types[i] for i in sorted_indices]
        avg_elos = [avg_elos[i] for i in sorted_indices]
        win_rates = [win_rates[i] for i in sorted_indices]

        # Create figure with two axes
        fig, ax1 = plt.subplots(figsize=(14, 10))
        ax2 = ax1.twinx()

        # Plot average ELO as bars
        ax1.bar(bot_types, avg_elos, color='skyblue', alpha=0.7, label='Avg ELO')
        ax1.set_ylabel('Average ELO Rating', fontsize=14)
        ax1.set_ylim(min(avg_elos) * 0.95, max(avg_elos) * 1.05)

        # Plot win rate as line
        ax2.plot(bot_types, win_rates, 'ro-', linewidth=2, label='Win Rate')
        ax2.set_ylabel('Win Rate (%)', fontsize=14)
        ax2.set_ylim(0, 100)

        # Add win rates as text above points
        for i, rate in enumerate(win_rates):
            ax2.annotate(
                f"{rate:.1f}%",
                (i, rate),
                textcoords="offset points",
                xytext=(0, 10),
                ha='center'
            )

        plt.title('Bot Type Comparison: Average ELO and Win Rate', fontsize=16)
        plt.xticks(rotation=45, ha='right')

        # Add both legends
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')

        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/bot_type_comparison.png", dpi=300)
        plt.close()

    def plot_execution_times(self):
        """Plot average execution times for each bot"""
        # Get average execution time for each bot
        bot_names = []
        avg_times = []

        for bot_name, times in self.stats.execution_times.items():
            if times:
                bot_names.append(bot_name)
                avg_times.append(sum(times) / len(times))

        # Sort by execution time
        sorted_indices = np.argsort(avg_times)
        bot_names = [bot_names[i] for i in sorted_indices]
        avg_times = [avg_times[i] for i in sorted_indices]

        # Take top 20 longest running bots
        if len(bot_names) > 20:
            bot_names = bot_names[-20:]
            avg_times = avg_times[-20:]

        plt.figure(figsize=(14, 10))

        # Color by bot type
        bot_types = [self.stats.bot_types.get(bot, "Unknown") for bot in bot_names]
        unique_types = sorted(set(bot_types))
        colors = plt.cm.tab10(np.linspace(0, 1, len(unique_types)))
        type_to_color = dict(zip(unique_types, colors))
        bar_colors = [type_to_color[bot_type] for bot_type in bot_types]

        plt.barh(bot_names, avg_times, color=bar_colors)

        # Add legend for bot types
        from matplotlib.patches import Patch
        legend_elements = [Patch(facecolor=type_to_color[t], label=t) for t in unique_types]
        plt.legend(handles=legend_elements, loc='lower right')

        plt.title('Average Execution Time per Game (seconds)', fontsize=16)
        plt.xlabel('Time (seconds)', fontsize=14)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        plt.savefig(f"{self.output_dir}/execution_times.png", dpi=300)
        plt.close()

    def copy_rankings_to_stats_dir(self):
        """Copy the rankings file to stats directory for aggregation"""
        rankings = self.stats.get_rankings()

        with open(f"{DIRECTORIES['stats']}/{self.tournament_type}_rankings.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Rank", "Bot", "ELO", "Wins", "Losses", "Draws", "Win %", "Tournament"])

            for rank, (bot_name, elo) in enumerate(rankings, 1):
                wins = self.stats.wins[bot_name]
                losses = self.stats.losses[bot_name]
                draws = self.stats.draws[bot_name]
                win_pct = self.stats.get_win_percentage(bot_name)

                writer.writerow([
                    rank, bot_name, round(elo, 1), wins, losses, draws,
                    f"{win_pct:.2f}%", self.tournament_type.capitalize()
                ])


def create_combined_ranking_report():
    """Create a combined ranking across all tournament types"""
    files = [
        f"{DIRECTORIES['stats']}/single_knockout_rankings.csv",
        f"{DIRECTORIES['stats']}/double_knockout_rankings.csv",
        f"{DIRECTORIES['stats']}/round_robin_rankings.csv",
        f"{DIRECTORIES['stats']}/swiss_rankings.csv"
    ]

    # Collect all available data
    all_data = []

    for file_path in files:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    all_data.append(row)

    if not all_data:
        print("No data available to create combined rankings")
        return

    # Create a combined ELO score for each bot
    bot_data = {}

    for row in all_data:
        bot_name = row['Bot']
        if bot_name not in bot_data:
            bot_data[bot_name] = {
                'elo_sum': 0,
                'wins': 0,
                'losses': 0,
                'draws': 0,
                'tournaments': 0
            }

        bot_data[bot_name]['elo_sum'] += float(row['ELO'])
        bot_data[bot_name]['wins'] += int(row['Wins'])
        bot_data[bot_name]['losses'] += int(row['Losses'])
        bot_data[bot_name]['draws'] += int(row['Draws'])
        bot_data[bot_name]['tournaments'] += 1

    # Calculate average ELO
    for bot_name in bot_data:
        bot_data[bot_name]['avg_elo'] = bot_data[bot_name]['elo_sum'] / bot_data[bot_name]['tournaments']

    # Sort by average ELO
    sorted_bots = sorted(bot_data.items(), key=lambda x: x[1]['avg_elo'], reverse=True)

    # Write combined rankings
    with open(f"{DIRECTORIES['stats']}/combined_rankings.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Rank", "Bot", "Avg ELO", "Total Wins", "Total Losses",
            "Total Draws", "Win %", "Tournaments Played"
        ])

        for rank, (bot_name, data) in enumerate(sorted_bots, 1):
            total_games = data['wins'] + data['losses'] + data['draws']
            win_pct = (data['wins'] + 0.5 * data['draws']) / total_games * 100 if total_games > 0 else 0

            writer.writerow([
                rank, bot_name, round(data['avg_elo'], 1),
                data['wins'], data['losses'], data['draws'],
                f"{win_pct:.2f}%", data['tournaments']
            ])

    # Plot top 20 bots
    top_bots = [bot for bot, _ in sorted_bots[:20]]
    avg_elos = [bot_data[bot]['avg_elo'] for bot in top_bots]

    plt.figure(figsize=(14, 10))
    plt.barh(top_bots, avg_elos)
    plt.title('Top 20 Bots by Average ELO Across All Tournaments', fontsize=16)
    plt.xlabel('Average ELO Rating', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"{DIRECTORIES['charts']}/combined_top_bots.png", dpi=300)
    plt.close()


def run_tournaments(participants):
    """Run all tournament types and generate reports"""
    create_directories()

    # # 1. Single Knockout Tournament
    # print("\n=== RUNNING SINGLE KNOCKOUT TOURNAMENT ===\n")
    # single_ko = SingleKnockoutTournament(participants)
    # single_ko_winner = single_ko.run_tournament()
    # analyzer = TournamentAnalyzer(single_ko.stats, "single_knockout")
    # analyzer.generate_reports()
    #
    # # 2. Double Knockout Tournament
    # print("\n=== RUNNING DOUBLE KNOCKOUT TOURNAMENT ===\n")
    # double_ko = DoubleKnockoutTournament(participants)
    # double_ko_winner = double_ko.run_tournament()
    # analyzer = TournamentAnalyzer(double_ko.stats, "double_knockout")
    # analyzer.generate_reports()
    #
    # # 3. Round Robin Tournament
    # print("\n=== RUNNING ROUND ROBIN TOURNAMENT ===\n")
    # round_robin = RoundRobinTournament(participants)
    # round_robin_winner, round_robin_rankings = round_robin.run_tournament()
    # analyzer = TournamentAnalyzer(round_robin.stats, "round_robin")
    # analyzer.generate_reports()

    # 4. Swiss Tournament
    print("\n=== RUNNING SWISS TOURNAMENT ===\n")
    # Use log2(n) rounds for Swiss
    num_rounds = min(7, math.ceil(math.log2(len(participants))))
    swiss = SwissTournament(participants, num_rounds=num_rounds)
    swiss_winner, swiss_rankings = swiss.run_tournament()
    analyzer = TournamentAnalyzer(swiss.stats, "swiss")
    analyzer.generate_reports()

    # Create combined rankings
    create_combined_ranking_report()

    # Print final results
    print("\n=== TOURNAMENT RESULTS SUMMARY ===\n")
    # print(f"Single Knockout Winner: {single_ko_winner.nom}")
    # print(f"Double Knockout Winner: {double_ko_winner.nom}")
    # print(f"Round Robin Winner: {round_robin_winner.nom}")
    print(f"Swiss Tournament Winner: {swiss_winner.nom}")
    print("\nAll tournament data and analysis has been saved to the 'tournament_results' directory.")


if __name__ == "__main__":
    print("Connect4 Bot Tournament System")
    print(f"Discovered {len(setup.participants)} bots to compete")

    # Run all tournament types
    run_tournaments(setup.participants)