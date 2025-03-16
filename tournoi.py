import time
import concurrent.futures
from moteur.partie import Partie
from bots import negamaxv5, gpt4o, same, o3_mini_high, o3_mini_high_search, negamaxv5_b, claude37_sonnet, \
    claude37_sonnet_thinking, gemini_flash_20, r1, gemini_pro_20, gemini_flash_20_thinking, gemma3, o1, lechat, qwq, \
    negamaxv6


def une_partie(bot1, bot2, i):
    partie = Partie()
    partie.ajouter_joueur(bot1)
    partie.ajouter_joueur(bot2)
    partie.tour_joueur = i%2 + 1

    while True:
        if partie.tour_joueur == 1:
            copie_plateau = partie.plateau.copier_grille()
            colonne = bot1.trouver_coup(copie_plateau, bot2)
        else:
            copie_plateau = partie.plateau.copier_grille()
            colonne = bot2.trouver_coup(copie_plateau, bot1)
        if partie.jouer(colonne, partie.tour_joueur):
            if partie.plateau.est_nul():
                return "nul"
            if partie.plateau.est_victoire(colonne):
                print("bot1" if partie.tour_joueur == 1 else "bot2")
                partie.plateau.afficher()
                print()
                return "bot1" if partie.tour_joueur == 1 else "bot2"

            partie.tour_joueur = 2 if partie.tour_joueur == 1 else 1
        else:
            print("Invalid move encountered", partie.tour_joueur, colonne)
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
    bot1 = negamaxv5_b.Negamax5B("Joueur 1", "X", profondeur=6)
    #bot1 = qwq.AdvancedNegamaxBot("Joueur 1", "O", profondeur=6)

    bot2 = negamaxv6.Negamax6("Joueur 2", "O", profondeur=6)

    start_time = time.time()
    resultats = tournoi(bot1, bot2, 2)
    print(resultats, "in", time.time() - start_time, "seconds")
