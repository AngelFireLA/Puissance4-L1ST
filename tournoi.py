import time
import concurrent.futures
from moteur.partie import Partie
from bots import bot, random_bot, negamax, negamaxv2, negamaxv3, neuralbot


def une_partie(bot1, bot2, i):
    partie = Partie()
    partie.ajouter_joueur(bot1)
    partie.ajouter_joueur(bot2)
    partie.tour_joueur = i % 2 + 1

    while True:
        if partie.tour_joueur == 1:
            colonne = bot1.trouver_coup(partie.plateau, bot2)
        else:
            colonne = bot2.trouver_coup(partie.plateau, bot1)
        if partie.jouer(colonne, partie.tour_joueur):
            if partie.plateau.est_nul():
                return "nul"
            if partie.plateau.est_victoire(colonne):
                return "bot1" if partie.tour_joueur == 1 else "bot2"
            partie.tour_joueur = 2 if partie.tour_joueur == 1 else 1
        else:
            return "bot2" if partie.tour_joueur == 1 else "bot1"


def tournoi(bot1, bot2, parties: int, max_workers=None):
    resultats = {"bot1": 0, "bot2": 0, "nul": 0}
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Notice we're NOT directly passing 'bot1' and 'bot2' here, but you can
        # if they're pickleable. If they're not, see notes below.
        futures = [
            executor.submit(une_partie, bot1, bot2, i)
            for i in range(parties)
        ]

        for count, future in enumerate(concurrent.futures.as_completed(futures), start=1):
            outcome = future.result()
            resultats[outcome] += 1

            # Print progress less frequently to reduce overhead
            if count % 50 == 0:
                print(f"Completed game {count}/{parties}")

    return resultats


if __name__ == '__main__':

    # Instantiate bots
    #bot1 = negamaxv2.Negamax2("Joueur 1", "X", profondeur=8)
    bot1 = neuralbot.NeuralBot("Bot", "O",
                                  model_path=r"C:\Dev\Python\Puissance4-L1ST\custom_neural_network\winner_gen100.pkl",
                                  config_path=r"C:\Dev\Python\Puissance4-L1ST\custom_neural_network\config_feedforward")

    bot2 = negamaxv3.Negamax3("Joueur 2", "X", profondeur=4)

    #bot2 = negamaxv3.Negamax3("Joueur 2", "O", profondeur=6, temps_max=0.1)
    #bot2 = random_bot.RandomBot("Joueur 2", "O")
    #bot2 = bot.Bot("Joueur 2", "O")

    start_time = time.time()
    resultats = tournoi(bot1, bot2, 1000)
    print(resultats, "in", time.time() - start_time, "seconds")
