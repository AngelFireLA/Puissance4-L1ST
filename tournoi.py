import time

from moteur.partie import Partie
from bots import bot, random_bot, negamax
def tournoi(bot1, bot2, parties:int):
    resultats = {"bot1": 0, "bot2": 0, "nul": 0}
    for i in range(parties):
        print(i)
        partie = Partie()
        partie.ajouter_joueur(bot1)
        partie.ajouter_joueur(bot2)
        partie.tour_joueur = i%2 + 1

        while True:
            if partie.tour_joueur == 1:
                colonne = bot1.trouver_coup(partie.plateau, bot2)
            else:
                colonne = bot2.trouver_coup(partie.plateau, bot1)
            if partie.jouer(colonne, partie.tour_joueur):
                if partie.plateau.est_nul():
                    resultats["nul"] += 1
                    break
                if partie.plateau.est_victoire(colonne):
                    if partie.tour_joueur == 1:
                        resultats["bot1"] += 1
                    else:
                        resultats["bot2"] += 1
                    break
                if partie.tour_joueur == 1:
                    partie.tour_joueur = 2
                else:
                    partie.tour_joueur = 1
            else:
                # dit que le coup est invalide et ajoute une victoire à l'autre bot
                if partie.tour_joueur == 1:
                    resultats["bot2"] += 1
                else:
                    resultats["bot1"] += 1
                print(f"Coup invalide de {partie.tour_joueur}")
                break
    return resultats

bot1 = negamax.Negamax("Joueur 1", "X", profondeur=4)
bot2 = negamax.Negamax("Joueur 2", "O", profondeur=2)
start_time = time.time()
resultats = tournoi(bot1, bot2, 1000)
print(resultats, "in", time.time() - start_time, "seconds")