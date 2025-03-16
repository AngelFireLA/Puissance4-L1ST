import time
import concurrent.futures
from moteur.partie import Partie
from bots import bot, random_bot, negamax, negamaxv2, neuralbot, negamaxv4, negamaxv5, negamaxv3, negamaxv5_b
from bots import gpt4o, gemini_flash_20, gemini_flash_20_thinking, gemini_pro_20, gemma3, claude37_sonnet_thinking, claude37_sonnet, qwq, o3_mini_high, o3_mini_high_search, lechat, same, r1, o1
def une_partie(bot1, bot2):
    partie = Partie()
    bot1.symbole = "O"
    bot2.symbole = "X"
    partie.ajouter_joueur(bot1)
    partie.ajouter_joueur(bot2)
    partie.tour_joueur = 1

    while True:
        copie_plateau = partie.plateau.copier_grille()
        if partie.tour_joueur == 1:
            colonne = bot1.trouver_coup(copie_plateau, bot2)
        else:
            colonne = bot2.trouver_coup(copie_plateau, bot1)
        if partie.jouer(colonne, partie.tour_joueur):
            if partie.plateau.est_nul():
                return "nul"
            if partie.plateau.est_victoire(colonne):
                return "bot1" if partie.tour_joueur == 1 else "bot2"
            partie.tour_joueur = 2 if partie.tour_joueur == 1 else 1
        else:
            return "bot2" if partie.tour_joueur == 1 else "bot1"

original_negamax_1 = negamax.Negamax("Negamax P1", "?", profondeur=1)
original_negamax_2 = negamax.Negamax("Negamax P2", "?", profondeur=2)
original_negamax_3 = negamax.Negamax("Negamax P4", "?", profondeur=4)
original_negamax_4 = negamax.Negamax("Negamax P6", "?", profondeur=6)
negamaxv2_1 = negamaxv2.Negamax2("Negamax2 P1", "?", profondeur=1)
negamaxv2_2 = negamaxv2.Negamax2("Negamax2 P2", "?", profondeur=2)
negamaxv2_3 = negamaxv2.Negamax2("Negamax2 P4", "?", profondeur=4)
negamaxv2_4 = negamaxv2.Negamax2("Negamax2 P6", "?", profondeur=6)
negamaxv2_5 = negamaxv2.Negamax2("Negamax2 P8", "?", profondeur=8)
negamaxv3_1 = negamaxv3.Negamax3("Negamax3 P1", "?", profondeur=1)
negamaxv3_2 = negamaxv3.Negamax3("Negamax3 P2", "?", profondeur=2)
negamaxv3_3 = negamaxv3.Negamax3("Negamax3 P4", "?", profondeur=4)
negamaxv3_4 = negamaxv3.Negamax3("Negamax3 P6", "?", profondeur=6)
negamaxv3_5 = negamaxv3.Negamax3("Negamax3 P8", "?", profondeur=8)
negamaxv4_1 = negamaxv4.Negamax4("Negamax4 P1", "?", profondeur=1)
negamaxv4_2 = negamaxv4.Negamax4("Negamax4 P2", "?", profondeur=2)
negamaxv4_3 = negamaxv4.Negamax4("Negamax4 P4", "?", profondeur=4)
negamaxv4_4 = negamaxv4.Negamax4("Negamax4 P6", "?", profondeur=6)
negamaxv4_5 = negamaxv4.Negamax4("Negamax4 P8", "?", profondeur=8)
negamaxv4_6 = negamaxv4.Negamax4("Negamax4 P10", "?", profondeur=10)
negamaxv4_7 = negamaxv4.Negamax4("Negamax4 P4 T0.01", "?", profondeur=4, temps_max=0.01)
negamaxv4_8 = negamaxv4.Negamax4("Negamax4 P4 T0.025", "?", profondeur=4, temps_max=0.025)
negamaxv4_9 = negamaxv4.Negamax4("Negamax4 P4 T0.1", "?", profondeur=4, temps_max=0.1)
negamaxv4_10 = negamaxv4.Negamax4("Negamax4 P4 T0.25", "?", profondeur=4, temps_max=0.25)
negamaxv4_11 = negamaxv4.Negamax4("Negamax4 P6 T0.01", "?", profondeur=6, temps_max=0.01)
negamaxv4_12 = negamaxv4.Negamax4("Negamax4 P6 T0.025", "?", profondeur=6, temps_max=0.025)
negamaxv4_13 = negamaxv4.Negamax4("Negamax4 P6 T0.1", "?", profondeur=6, temps_max=0.1)
negamaxv4_14 = negamaxv4.Negamax4("Negamax4 P6 T0.25", "?", profondeur=6, temps_max=0.25)
negamaxv4_15 = negamaxv4.Negamax4("Negamax4 P8 T0.01", "?", profondeur=8, temps_max=0.01)
negamaxv4_16 = negamaxv4.Negamax4("Negamax4 P8 T0.025", "?", profondeur=8, temps_max=0.025)
negamaxv4_17 = negamaxv4.Negamax4("Negamax4 P8 T0.1", "?", profondeur=8, temps_max=0.1)
negamaxv4_18 = negamaxv4.Negamax4("Negamax4 P8 T0.25", "?", profondeur=8, temps_max=0.25)
negamaxv4_19 = negamaxv4.Negamax4("Negamax4 P10 T0.01", "?", profondeur=10, temps_max=0.01)
negamaxv4_20 = negamaxv4.Negamax4("Negamax4 P10 T0.025", "?", profondeur=10, temps_max=0.025)
negamaxv4_21 = negamaxv4.Negamax4("Negamax4 P10 T0.1", "?", profondeur=10, temps_max=0.1)
negamaxv4_22 = negamaxv4.Negamax4("Negamax4 P10 T0.25", "?", profondeur=10, temps_max=0.25)
negamaxv5_1 = negamaxv5.Negamax5("Negamax5 P1", "?", profondeur=1)
negamaxv5_2 = negamaxv5.Negamax5("Negamax5 P2", "?", profondeur=2)
negamaxv5_3 = negamaxv5.Negamax5("Negamax5 P4", "?", profondeur=4)
negamaxv5_4 = negamaxv5.Negamax5("Negamax5 P6", "?", profondeur=6)
negamaxv5_5 = negamaxv5.Negamax5("Negamax5 P8", "?", profondeur=8)
negamaxv5_6 = negamaxv5.Negamax5("Negamax5 P10", "?", profondeur=10)
negamaxv5_7 = negamaxv5.Negamax5("Negamax5 P12", "?", profondeur=12)
negamaxv5_8 = negamaxv5.Negamax5("Negamax5 P4 T0.01", "?", profondeur=4, temps_max=0.01)
negamaxv5_9 = negamaxv5.Negamax5("Negamax5 P4 T0.025", "?", profondeur=4, temps_max=0.025)
negamaxv5_10 = negamaxv5.Negamax5("Negamax5 P4 T0.1", "?", profondeur=4, temps_max=0.1)
negamaxv5_11 = negamaxv5.Negamax5("Negamax5 P4 T0.25", "?", profondeur=4, temps_max=0.25)
negamaxv5_12 = negamaxv5.Negamax5("Negamax5 P6 T0.01", "?", profondeur=6, temps_max=0.01)
negamaxv5_13 = negamaxv5.Negamax5("Negamax5 P6 T0.025", "?", profondeur=6, temps_max=0.025)
negamaxv5_14 = negamaxv5.Negamax5("Negamax5 P6 T0.1", "?", profondeur=6, temps_max=0.1)
negamaxv5_15 = negamaxv5.Negamax5("Negamax5 P6 T0.25", "?", profondeur=6, temps_max=0.25)
negamaxv5_16 = negamaxv5.Negamax5("Negamax5 P8 T0.01", "?", profondeur=8, temps_max=0.01)
negamaxv5_17 = negamaxv5.Negamax5("Negamax5 P8 T0.025", "?", profondeur=8, temps_max=0.025)
negamaxv5_18 = negamaxv5.Negamax5("Negamax5 P8 T0.1", "?", profondeur=8, temps_max=0.1)
negamaxv5_19 = negamaxv5.Negamax5("Negamax5 P8 T0.25", "?", profondeur=8, temps_max=0.25)
negamaxv5_20 = negamaxv5.Negamax5("Negamax5 P10 T0.01", "?", profondeur=10, temps_max=0.01)
negamaxv5_21 = negamaxv5.Negamax5("Negamax5 P10 T0.025", "?", profondeur=10, temps_max=0.025)
negamaxv5_22 = negamaxv5.Negamax5("Negamax5 P10 T0.1", "?", profondeur=10, temps_max=0.1)
negamaxv5_23 = negamaxv5.Negamax5("Negamax5 P10 T0.25", "?", profondeur=10, temps_max=0.25)
negamaxv5_24 = negamaxv5.Negamax5("Negamax5 P12 T0.01", "?", profondeur=12, temps_max=0.01)
negamaxv5_25 = negamaxv5.Negamax5("Negamax5 P12 T0.025", "?", profondeur=12, temps_max=0.025)
negamaxv5_26 = negamaxv5.Negamax5("Negamax5 P12 T0.1", "?", profondeur=12, temps_max=0.1)
negamaxv5_27 = negamaxv5.Negamax5("Negamax5 P12 T0.25", "?", profondeur=12, temps_max=0.25)
negamaxv5b_1 = negamaxv5_b.Negamax5B("Negamax5B P1", "?", profondeur=1)
negamaxv5b_2 = negamaxv5_b.Negamax5B("Negamax5B P2", "?", profondeur=2)
negamaxv5b_3 = negamaxv5_b.Negamax5B("Negamax5B P4", "?", profondeur=4)
negamaxv5b_4 = negamaxv5_b.Negamax5B("Negamax5B P6", "?", profondeur=6)
negamaxv5b_5 = negamaxv5_b.Negamax5B("Negamax5B P8", "?", profondeur=8)
negamaxv5b_6 = negamaxv5_b.Negamax5B("Negamax5B P10", "?", profondeur=10)
negamaxv5b_7 = negamaxv5_b.Negamax5B("Negamax5B P12", "?", profondeur=12)
negamaxv5b_8 = negamaxv5_b.Negamax5B("Negamax5B P4 T0.01", "?", profondeur=4, temps_max=0.01)
negamaxv5b_9 = negamaxv5_b.Negamax5B("Negamax5B P4 T0.025", "?", profondeur=4, temps_max=0.025)
negamaxv5b_10 = negamaxv5_b.Negamax5B("Negamax5B P4 T0.1", "?", profondeur=4, temps_max=0.1)
negamaxv5b_11 = negamaxv5_b.Negamax5B("Negamax5B P4 T0.25", "?", profondeur=4, temps_max=0.25)
negamaxv5b_12 = negamaxv5_b.Negamax5B("Negamax5B P6 T0.01", "?", profondeur=6, temps_max=0.01)
negamaxv5b_13 = negamaxv5_b.Negamax5B("Negamax5B P6 T0.025", "?", profondeur=6, temps_max=0.025)
negamaxv5b_14 = negamaxv5_b.Negamax5B("Negamax5B P6 T0.1", "?", profondeur=6, temps_max=0.1)
negamaxv5b_15 = negamaxv5_b.Negamax5B("Negamax5B P6 T0.25", "?", profondeur=6, temps_max=0.25)
negamaxv5b_16 = negamaxv5_b.Negamax5B("Negamax5B P8 T0.01", "?", profondeur=8, temps_max=0.01)
negamaxv5b_17 = negamaxv5_b.Negamax5B("Negamax5B P8 T0.025", "?", profondeur=8, temps_max=0.025)
negamaxv5b_18 = negamaxv5_b.Negamax5B("Negamax5B P8 T0.1", "?", profondeur=8, temps_max=0.1)
negamaxv5b_19 = negamaxv5_b.Negamax5B("Negamax5B P8 T0.25", "?", profondeur=8, temps_max=0.25)
negamaxv5b_20 = negamaxv5_b.Negamax5B("Negamax5B P10 T0.01", "?", profondeur=10, temps_max=0.01)
negamaxv5b_21 = negamaxv5_b.Negamax5B("Negamax5B P10 T0.025", "?", profondeur=10, temps_max=0.025)
negamaxv5b_22 = negamaxv5_b.Negamax5B("Negamax5B P10 T0.1", "?", profondeur=10, temps_max=0.1)
negamaxv5b_23 = negamaxv5_b.Negamax5B("Negamax5B P10 T0.25", "?", profondeur=10, temps_max=0.25)
negamaxv5b_24 = negamaxv5_b.Negamax5B("Negamax5B P12 T0.01", "?", profondeur=12, temps_max=0.01)
negamaxv5b_25 = negamaxv5_b.Negamax5B("Negamax5B P12 T0.025", "?", profondeur=12, temps_max=0.025)
negamaxv5b_26 = negamaxv5_b.Negamax5B("Negamax5B P12 T0.1", "?", profondeur=12, temps_max=0.1)
negamaxv5b_27 = negamaxv5_b.Negamax5B("Negamax5B P12 T0.25", "?", profondeur=12, temps_max=0.25)
default_bot = bot.Bot("Default Bot", "?")
random_bot = random_bot.RandomBot("Random Bot", "?")
neural_bot1 = neuralbot.NeuralBot("Neural Bot winner.pkl", "?", model_path=r"C:\Dev\Python\Puissance4-L1ST\custom_neural_network\winner.pkl")
neural_bot2 = neuralbot.NeuralBot("Neural Bot winner_gen700.pkl", "?", model_path=r"C:\Dev\Python\Puissance4-L1ST\custom_neural_network\winner_gen700.pkl")
neural_bot3 = neuralbot.NeuralBot("Neural Bot winner_1gen1000.pkl", "?", model_path=r"C:\Dev\Python\Puissance4-L1ST\custom_neural_network\winner_1gen1000.pkl")
neural_bot4 = neuralbot.NeuralBot("Neural Bot winner_gen200.pkl", "?", model_path=r"C:\Dev\Python\Puissance4-L1ST\custom_neural_network\winner_gen200.pkl")
neural_bot5 = neuralbot.NeuralBot("Neural Bot winner_gen1000.pkl", "?", model_path=r"C:\Dev\Python\Puissance4-L1ST\custom_neural_network\winner_gen1000.pkl")
neural_bot6 = neuralbot.NeuralBot("Neural Bot winner_1gen1500.pkl", "?", model_path=r"C:\Dev\Python\Puissance4-L1ST\custom_neural_network\winner_1gen1500.pkl")
neural_bot7 = neuralbot.NeuralBot("Neural Bot winner_gen100.pkl", "?", model_path=r"C:\Dev\Python\Puissance4-L1ST\custom_neural_network\winner_gen100.pkl")
neural_bot8 = neuralbot.NeuralBot("Neural Bot winner_1gen400.pkl", "?", model_path=r"C:\Dev\Python\Puissance4-L1ST\custom_neural_network\winner_1gen400.pkl")
neural_bot9 = neuralbot.NeuralBot("Neural Bot winner_1gen50.pkl", "?", model_path=r"C:\Dev\Python\Puissance4-L1ST\custom_neural_network\winner_1gen50.pkl")
neural_bot10 = neuralbot.NeuralBot("Neural Bot genomes/winner2_gen1200.pkl", "?", model_path=r"C:\Dev\Python\Puissance4-L1ST\custom_neural_network\genomes\winner2_gen1200.pkl")
neural_bot11 = neuralbot.NeuralBot("Neural Bot genomes/winner3_gen1000.pkl", "?", model_path=r"C:\Dev\Python\Puissance4-L1ST\custom_neural_network\genomes\winner3_gen1000.pkl")
neural_bot12 = neuralbot.NeuralBot("Neural Bot genomes/winner4_gen300.pkl", "?", model_path=r"C:\Dev\Python\Puissance4-L1ST\custom_neural_network\genomes\winner4_gen300.pkl")
neural_bot13 = neuralbot.NeuralBot("Neural Bot genomes/winner_gen100.pkl", "?", model_path=r"C:\Dev\Python\Puissance4-L1ST\custom_neural_network\winner_gen100.pkl")
neural_bot14 = neuralbot.NeuralBot("Neural Bot genomes/winner5_gen300.pkl", "?", model_path=r"C:\Dev\Python\Puissance4-L1ST\custom_neural_network\genomes\winner5_gen300.pkl")
neural_bot15 = neuralbot.NeuralBot("Neural Bot genomes/winner.pkl", "?", model_path=r"C:\Dev\Python\Puissance4-L1ST\custom_neural_network\genomes\winner.pkl")
neural_bot16 = neuralbot.NeuralBot("Neural Bot genomes/winner6_gen200.pkl", "?", model_path=r"C:\Dev\Python\Puissance4-L1ST\custom_neural_network\genomes\winner6_gen200.pkl")
neural_bot17 = neuralbot.NeuralBot("Neural Bot genomes/winner7_gen900.pkl", "?", model_path=r"C:\Dev\Python\Puissance4-L1ST\custom_neural_network\genomes\winner7_gen900.pkl")
neural_bot18 = neuralbot.NeuralBot("Neural Bot genomes/winne7.pkl", "?", model_path=r"C:\Dev\Python\Puissance4-L1ST\custom_neural_network\genomes\winne7.pkl")
neural_bot19 = neuralbot.NeuralBot("Neural Bot genomes/winner8_gen300.pkl", "?", model_path=r"C:\Dev\Python\Puissance4-L1ST\custom_neural_network\genomes\winner8_gen300.pkl")
neural_bot20 = neuralbot.NeuralBot("Neural Bot genomes/winner8.pkl", "?", model_path=r"C:\Dev\Python\Puissance4-L1ST\custom_neural_network\genomes\winner8.pkl")
neural_bot21 = neuralbot.NeuralBot("Neural Bot genomes/winner9_gen800.pkl", "?", model_path=r"C:\Dev\Python\Puissance4-L1ST\custom_neural_network\genomes\winner9_gen800.pkl")
neural_bot22 = neuralbot.NeuralBot("Neural Bot genomes/winner3_gen800.pkl", "?", model_path=r"C:\Dev\Python\Puissance4-L1ST\custom_neural_network\genomes\winner3_gen800.pkl")
neural_bot23 = neuralbot.NeuralBot("Neural Bot genomes/checkpoint_gen200.pkl", "?", model_path=r"C:\Dev\Python\Puissance4-L1ST\custom_neural_network\genomes\checkpoint_gen200.pkl")
neural_bot24 = neuralbot.NeuralBot("Neural Bot genomes/checkpoint_gen100.pkl", "?", model_path=r"C:\Dev\Python\Puissance4-L1ST\custom_neural_network\genomes\checkpoint_gen100.pkl")

gpt4o_bot = gpt4o.AlphaConnectX("gpt4o P1", "?", profondeur=1)
gpt4o_bot2 = gpt4o.AlphaConnectX("gpt4o P2", "?", profondeur=2)
gpt4o_bot3 = gpt4o.AlphaConnectX("gpt4o P4", "?", profondeur=4)
gpt4o_bot4 = gpt4o.AlphaConnectX("gpt4o P6", "?", profondeur=6)
gpt4o_bot5 = gpt4o.AlphaConnectX("gpt4o P8", "?", profondeur=8)
gpt4o_bot6 = gpt4o.AlphaConnectX("gpt4o P10", "?", profondeur=10)
gpt4o_bot7 = gpt4o.AlphaConnectX("gpt4o P12", "?", profondeur=12)
gpt4o_bot8 = gpt4o.AlphaConnectX("gpt4o P4 T0.01", "?", profondeur=4, temps_max=0.01)
gpt4o_bot9 = gpt4o.AlphaConnectX("gpt4o P4 T0.025", "?", profondeur=4, temps_max=0.025)
gpt4o_bot10 = gpt4o.AlphaConnectX("gpt4o P4 T0.1", "?", profondeur=4, temps_max=0.1)
gpt4o_bot11 = gpt4o.AlphaConnectX("gpt4o P4 T0.25", "?", profondeur=4, temps_max=0.25)
gpt4o_bot12 = gpt4o.AlphaConnectX("gpt4o P6 T0.01", "?", profondeur=6, temps_max=0.01)
gpt4o_bot13 = gpt4o.AlphaConnectX("gpt4o P6 T0.025", "?", profondeur=6, temps_max=0.025)
gpt4o_bot14 = gpt4o.AlphaConnectX("gpt4o P6 T0.1", "?", profondeur=6, temps_max=0.1)
gpt4o_bot15 = gpt4o.AlphaConnectX("gpt4o P6 T0.25", "?", profondeur=6, temps_max=0.25)
gpt4o_bot16 = gpt4o.AlphaConnectX("gpt4o P8 T0.01", "?", profondeur=8, temps_max=0.01)
gpt4o_bot17 = gpt4o.AlphaConnectX("gpt4o P8 T0.025", "?", profondeur=8, temps_max=0.025)
gpt4o_bot18 = gpt4o.AlphaConnectX("gpt4o P8 T0.1", "?", profondeur=8, temps_max=0.1)
gpt4o_bot19 = gpt4o.AlphaConnectX("gpt4o P8 T0.25", "?", profondeur=8, temps_max=0.25)
gpt4o_bot20 = gpt4o.AlphaConnectX("gpt4o P10 T0.01", "?", profondeur=10, temps_max=0.01)
gpt4o_bot21 = gpt4o.AlphaConnectX("gpt4o P10 T0.025", "?", profondeur=10, temps_max=0.025)
gpt4o_bot22 = gpt4o.AlphaConnectX("gpt4o P10 T0.1", "?", profondeur=10, temps_max=0.1)
gpt4o_bot23 = gpt4o.AlphaConnectX("gpt4o P10 T0.25", "?", profondeur=10, temps_max=0.25)
gpt4o_bot24 = gpt4o.AlphaConnectX("gpt4o P12 T0.01", "?", profondeur=12, temps_max=0.01)
gpt4o_bot25 = gpt4o.AlphaConnectX("gpt4o P12 T0.025", "?", profondeur=12, temps_max=0.025)
gpt4o_bot26 = gpt4o.AlphaConnectX("gpt4o P12 T0.1", "?", profondeur=12, temps_max=0.1)
gpt4o_bot27 = gpt4o.AlphaConnectX("gpt4o P12 T0.25", "?", profondeur=12, temps_max=0.25)
o3_mini_high_bot = o3_mini_high.QuantumConnect4Bot("o3-mini-high P1", "?", profondeur=1)
o3_mini_high_bot2 = o3_mini_high.QuantumConnect4Bot("o3-mini-high P2", "?", profondeur=2)
o3_mini_high_bot3 = o3_mini_high.QuantumConnect4Bot("o3-mini-high P4", "?", profondeur=4)
o3_mini_high_bot4 = o3_mini_high.QuantumConnect4Bot("o3-mini-high P6", "?", profondeur=6)
o3_mini_high_search_bot = o3_mini_high_search.ImprovedMCTSBot("o3-mini-high-search I1000", "?", iterations=1000)
o3_mini_high_search_bot2 = o3_mini_high_search.ImprovedMCTSBot("o3-mini-high-search I2000", "?", iterations=2000)
o3_mini_high_search_bot3 = o3_mini_high_search.ImprovedMCTSBot("o3-mini-high-search I3000", "?", iterations=3000)
o3_mini_high_search_bot4 = o3_mini_high_search.ImprovedMCTSBot("o3-mini-high-search I4000", "?", iterations=4000)
o3_mini_high_search_bot5 = o3_mini_high_search.ImprovedMCTSBot("o3-mini-high-search I5000", "?", iterations=5000)
o3_mini_high_search_bot6 = o3_mini_high_search.ImprovedMCTSBot("o3-mini-high-search I6000", "?", iterations=6000)
o3_mini_high_search_bot7 = o3_mini_high_search.ImprovedMCTSBot("o3-mini-high-search I7000", "?", iterations=7000)
claude37_sonnet_bot = claude37_sonnet.AlphaBetaMCTSHybrid("claude3.7-sonnet P1", "?", profondeur=1)
claude37_sonnet_bot2 = claude37_sonnet.AlphaBetaMCTSHybrid("claude3.7-sonnet P2", "?", profondeur=2)
claude37_sonnet_bot3 = claude37_sonnet.AlphaBetaMCTSHybrid("claude3.7-sonnet P4", "?", profondeur=4)
claude37_sonnet_bot4 = claude37_sonnet.AlphaBetaMCTSHybrid("claude3.7-sonnet P6", "?", profondeur=6)
claude37_sonnet_bot5 = claude37_sonnet.AlphaBetaMCTSHybrid("claude3.7-sonnet P8", "?", profondeur=8)
claude37_sonnet_bot6 = claude37_sonnet.AlphaBetaMCTSHybrid("claude3.7-sonnet P10", "?", profondeur=10)
claude37_sonnet_bot7 = claude37_sonnet.AlphaBetaMCTSHybrid("claude3.7-sonnet P12", "?", profondeur=12)
claude37_sonnet_thinking_bot = claude37_sonnet_thinking.QuantumConnect4("claude3.7-sonnet-thinking P1", "?", profondeur=1, temps_max=1)
claude37_sonnet_thinking_bot2 = claude37_sonnet_thinking.QuantumConnect4("claude3.7-sonnet-thinking P2", "?", profondeur=2, temps_max=1)
claude37_sonnet_thinking_bot3 = claude37_sonnet_thinking.QuantumConnect4("claude3.7-sonnet-thinking P4", "?", profondeur=4, temps_max=1)
claude37_sonnet_thinking_bot4 = claude37_sonnet_thinking.QuantumConnect4("claude3.7-sonnet-thinking P6", "?", profondeur=6, temps_max=1)
claude37_sonnet_thinking_bot5 = claude37_sonnet_thinking.QuantumConnect4("claude3.7-sonnet-thinking P8", "?", profondeur=8, temps_max=1)
same_dev_bot = same.QuantumNegamax("same.dev P1", "?", profondeur=1)
same_dev_bot2 = same.QuantumNegamax("same.dev P2", "?", profondeur=2)
same_dev_bot3 = same.QuantumNegamax("same.dev P4", "?", profondeur=4)
same_dev_bot4 = same.QuantumNegamax("same.dev P6", "?", profondeur=6)
same_dev_bot5 = same.QuantumNegamax("same.dev P8", "?", profondeur=8)
r1_bot = r1.ZobristNegamaxBot("r1 T0.01", "?", temps_max=0.01)
r1_bot2 = r1.ZobristNegamaxBot("r1 T0.025", "?", temps_max=0.025)
r1_bot3 = r1.ZobristNegamaxBot("r1 T0.1", "?", temps_max=0.1)
r1_bot4 = r1.ZobristNegamaxBot("r1 T0.25", "?", temps_max=0.25)
r1_bot5 = r1.ZobristNegamaxBot("r1 T1", "?", temps_max=1)
gemini_flash_20_bot = gemini_flash_20.AlphaConnect("gemini-flash-2.0 P1", "?", profondeur=1)
gemini_flash_20_bot2 = gemini_flash_20.AlphaConnect("gemini-flash-2.0 P2", "?", profondeur=2)
gemini_flash_20_bot3 = gemini_flash_20.AlphaConnect("gemini-flash-2.0 P4", "?", profondeur=4)
gemini_flash_20_bot4 = gemini_flash_20.AlphaConnect("gemini-flash-2.0 P6", "?", profondeur=6)
gemini_flash_20_bot5 = gemini_flash_20.AlphaConnect("gemini-flash-2.0 P8", "?", profondeur=8)
gemini_flash_20_thinking_bot = gemini_flash_20_thinking.OptimizedNegamaxBot("gemini-flash-2.0-thinking P1", "?", profondeur=1)
gemini_flash_20_thinking_bot2 = gemini_flash_20_thinking.OptimizedNegamaxBot("gemini-flash-2.0-thinking P2", "?", profondeur=2)
gemini_flash_20_thinking_bot3 = gemini_flash_20_thinking.OptimizedNegamaxBot("gemini-flash-2.0-thinking P4", "?", profondeur=4)
gemini_flash_20_thinking_bot4 = gemini_flash_20_thinking.OptimizedNegamaxBot("gemini-flash-2.0-thinking P6", "?", profondeur=6)
gemini_flash_20_thinking_bot5 = gemini_flash_20_thinking.OptimizedNegamaxBot("gemini-flash-2.0-thinking P8", "?", profondeur=8)
gemini_pro_20_bot = gemini_pro_20.MTDfbBot("gemini-pro-2.0 P1", "?", profondeur=1)
gemini_pro_20_bot2 = gemini_pro_20.MTDfbBot("gemini-pro-2.0 P2", "?", profondeur=2)
gemini_pro_20_bot3 = gemini_pro_20.MTDfbBot("gemini-pro-2.0 P4", "?", profondeur=4)
gemini_pro_20_bot4 = gemini_pro_20.MTDfbBot("gemini-pro-2.0 P6", "?", profondeur=6)
gemini_pro_20_bot5 = gemini_pro_20.MTDfbBot("gemini-pro-2.0 P8", "?", profondeur=8)
gemma3_bot = gemma3.SigmaBot("Gemma3 P1", "?", profondeur=1)
gemma3_bot2 = gemma3.SigmaBot("Gemma3 P2", "?", profondeur=2)
gemma3_bot3 = gemma3.SigmaBot("Gemma3 P4", "?", profondeur=4)
gemma3_bot4 = gemma3.SigmaBot("Gemma3 P6", "?", profondeur=6)
gemma3_bot5 = gemma3.SigmaBot("Gemma3 P8", "?", profondeur=8)
o1_bot = o1.GrandMasterBot("o1 P1", "?", profondeur=1)
o1_bot2 = o1.GrandMasterBot("o1 P2", "?", profondeur=2)
o1_bot3 = o1.GrandMasterBot("o1 P4", "?", profondeur=4)
o1_bot4 = o1.GrandMasterBot("o1 P6", "?", profondeur=6)
o1_bot5 = o1.GrandMasterBot("o1 P8", "?", profondeur=8)
lechat_bot = lechat.AdvancedConnect4Bot("LeChat P1", "?", profondeur=1)
lechat_bot2 = lechat.AdvancedConnect4Bot("LeChat P2", "?", profondeur=2)
lechat_bot3 = lechat.AdvancedConnect4Bot("LeChat P4", "?", profondeur=4)
lechat_bot4 = lechat.AdvancedConnect4Bot("LeChat P6", "?", profondeur=6)
lechat_bot5 = lechat.AdvancedConnect4Bot("LeChat P8", "?", profondeur=8)
lechat_bot6 = lechat.AdvancedConnect4Bot("LeChat P10", "?", profondeur=10)
qwq_bot = qwq.AdvancedNegamaxBot("QwQ P1", "?", profondeur=1)
qwq_bot2 = qwq.AdvancedNegamaxBot("QwQ P2", "?", profondeur=2)
qwq_bot3 = qwq.AdvancedNegamaxBot("QwQ P4", "?", profondeur=4)
qwq_bot4 = qwq.AdvancedNegamaxBot("QwQ P6", "?", profondeur=6)

participants = [
    # Original Negamax bots
    original_negamax_1, original_negamax_2, original_negamax_3, original_negamax_4,

    # Negamaxv2 bots
    negamaxv2_1, negamaxv2_2, negamaxv2_3, negamaxv2_4, negamaxv2_5,

    # Negamaxv3 bots
    negamaxv3_1, negamaxv3_2, negamaxv3_3, negamaxv3_4, negamaxv3_5,

    # Negamaxv4 bots
    negamaxv4_1, negamaxv4_2, negamaxv4_3, negamaxv4_4, negamaxv4_5, negamaxv4_6,
    negamaxv4_7, negamaxv4_8, negamaxv4_9, negamaxv4_10, negamaxv4_11, negamaxv4_12,
    negamaxv4_13, negamaxv4_14, negamaxv4_15, negamaxv4_16, negamaxv4_17, negamaxv4_18,
    negamaxv4_19, negamaxv4_20, negamaxv4_21, negamaxv4_22,

    # Negamaxv5 bots
    negamaxv5_1, negamaxv5_2, negamaxv5_3, negamaxv5_4, negamaxv5_5, negamaxv5_6, negamaxv5_7,
    negamaxv5_8, negamaxv5_9, negamaxv5_10, negamaxv5_11, negamaxv5_12, negamaxv5_13,
    negamaxv5_14, negamaxv5_15, negamaxv5_16, negamaxv5_17, negamaxv5_18, negamaxv5_19,
    negamaxv5_20, negamaxv5_21, negamaxv5_22, negamaxv5_23, negamaxv5_24, negamaxv5_25,
    negamaxv5_26, negamaxv5_27,

    # Negamaxv5B bots
    negamaxv5b_1, negamaxv5b_2, negamaxv5b_3, negamaxv5b_4, negamaxv5b_5, negamaxv5b_6, negamaxv5b_7,
    negamaxv5b_8, negamaxv5b_9, negamaxv5b_10, negamaxv5b_11, negamaxv5b_12, negamaxv5b_13,
    negamaxv5b_14, negamaxv5b_15, negamaxv5b_16, negamaxv5b_17, negamaxv5b_18, negamaxv5b_19,
    negamaxv5b_20, negamaxv5b_21, negamaxv5b_22, negamaxv5b_23, negamaxv5b_24, negamaxv5b_25,
    negamaxv5b_26, negamaxv5b_27,

    # Default and Random bots
    default_bot, random_bot,

    # Neural bots
    neural_bot1, neural_bot2, neural_bot3, neural_bot4, neural_bot5, neural_bot6, neural_bot7,
    neural_bot8, neural_bot9, neural_bot10, neural_bot11, neural_bot12, neural_bot13, neural_bot14,
    neural_bot15, neural_bot16, neural_bot17, neural_bot18, neural_bot19, neural_bot20,
    neural_bot21, neural_bot22, neural_bot23, neural_bot24,

    # GPT4O bots
    gpt4o_bot, gpt4o_bot2, gpt4o_bot3, gpt4o_bot4, gpt4o_bot5, gpt4o_bot6, gpt4o_bot7,
    gpt4o_bot8, gpt4o_bot9, gpt4o_bot10, gpt4o_bot11, gpt4o_bot12, gpt4o_bot13, gpt4o_bot14,
    gpt4o_bot15, gpt4o_bot16, gpt4o_bot17, gpt4o_bot18, gpt4o_bot19, gpt4o_bot20, gpt4o_bot21,
    gpt4o_bot22, gpt4o_bot23, gpt4o_bot24, gpt4o_bot25, gpt4o_bot26, gpt4o_bot27,

    # o3-mini-high bots
    o3_mini_high_bot, o3_mini_high_bot2, o3_mini_high_bot3, o3_mini_high_bot4,

    # o3-mini-high-search bots
    o3_mini_high_search_bot, o3_mini_high_search_bot2, o3_mini_high_search_bot3,
    o3_mini_high_search_bot4, o3_mini_high_search_bot5, o3_mini_high_search_bot6,
    o3_mini_high_search_bot7,

    # claude3.7-sonnet bots
    claude37_sonnet_bot, claude37_sonnet_bot2, claude37_sonnet_bot3, claude37_sonnet_bot4,
    claude37_sonnet_bot5, claude37_sonnet_bot6, claude37_sonnet_bot7,

    # claude3.7-sonnet-thinking bots
    claude37_sonnet_thinking_bot, claude37_sonnet_thinking_bot2, claude37_sonnet_thinking_bot3,
    claude37_sonnet_thinking_bot4, claude37_sonnet_thinking_bot5,

    # same.dev bots
    same_dev_bot, same_dev_bot2, same_dev_bot3, same_dev_bot4, same_dev_bot5,

    # r1 bots
    r1_bot, r1_bot2, r1_bot3, r1_bot4, r1_bot5,

    # gemini-flash-2.0 bots
    gemini_flash_20_bot, gemini_flash_20_bot2, gemini_flash_20_bot3, gemini_flash_20_bot4,
    gemini_flash_20_bot5,

    # gemini-flash-2.0-thinking bots
    gemini_flash_20_thinking_bot, gemini_flash_20_thinking_bot2, gemini_flash_20_thinking_bot3,
    gemini_flash_20_thinking_bot4, gemini_flash_20_thinking_bot5,

    # gemini-pro-2.0 bots
    gemini_pro_20_bot, gemini_pro_20_bot2, gemini_pro_20_bot3, gemini_pro_20_bot4, gemini_pro_20_bot5,

    # Gemma3 bots
    gemma3_bot, gemma3_bot2, gemma3_bot3, gemma3_bot4, gemma3_bot5,

    # o1 bots
    o1_bot, o1_bot2, o1_bot3, o1_bot4, o1_bot5,

    # LeChat bots
    lechat_bot, lechat_bot2, lechat_bot3, lechat_bot4, lechat_bot5, lechat_bot6,

    # QwQ bots
    qwq_bot, qwq_bot2, qwq_bot3, qwq_bot4,
]

