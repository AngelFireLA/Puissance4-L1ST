from moteur.partie import Partie
from bots import bot, random_bot, negamax, negamaxv2, negamaxv4, negamaxv5, negamaxv3, negamaxv5_b
from bots import gpt4o, gemini_flash_20, gemini_flash_20_thinking, gemini_pro_20, gemma3, claude37_sonnet_thinking, claude37_sonnet, qwq, o3_mini_high, lechat, same, r1, o1, gemini25_pro, gemini25_flash_thinking, qwen3, o4_mini_high, o3, gpt5


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
            if partie.plateau.est_victoire(colonne):
                return "bot1" if partie.tour_joueur == 1 else "bot2"
            if partie.plateau.est_nul():
                return "nul"
            partie.tour_joueur = 2 if partie.tour_joueur == 1 else 1
        else:
            return "bot2" if partie.tour_joueur == 1 else "bot1"


original_negamax_4 = negamax.Negamax("Negamax P6", "?", profondeur=6)
negamaxv2_5 = negamaxv2.Negamax2("Negamax2 P8", "?", profondeur=8)
negamaxv3_5 = negamaxv3.Negamax3("Negamax3 P8", "?", profondeur=8)
negamaxv4_22 = negamaxv4.Negamax4("Negamax4 P10 T0.25", "?", profondeur=10, temps_max=0.25)
negamaxv5_23 = negamaxv5.Negamax5("Negamax5 P10 T0.25", "?", profondeur=10, temps_max=0.25)
negamaxv5b_23 = negamaxv5_b.Negamax5B("Negamax5B P10 T0.25", "?", profondeur=10, temps_max=0.25)
default_bot = bot.Bot("Default Bot", "?")
random_bot = random_bot.RandomBot("Random Bot", "?")
gpt4o_bot23 = gpt4o.AlphaConnectX("gpt4o P10 T0.25", "?", profondeur=10, temps_max=0.25)
o3_mini_high_bot4 = o3_mini_high.QuantumConnect4Bot("o3-mini-high P6", "?", profondeur=6)
claude37_sonnet_bot6 = claude37_sonnet.AlphaBetaMCTSHybrid("claude3.7-sonnet P10", "?", profondeur=10)
claude37_sonnet_thinking_bot5 = claude37_sonnet_thinking.QuantumConnect4("claude3.7-sonnet-thinking P8", "?", profondeur=8, temps_max=0.75)
same_dev_bot4 = same.QuantumNegamax("same.dev P6", "?", profondeur=6)
r1_bot5 = r1.ZobristNegamaxBot("r1 T0.5", "?", temps_max=0.5)
gemini_flash_20_bot5 = gemini_flash_20.AlphaConnect("gemini-flash-2.0 P8", "?", profondeur=8)
gemini_flash_20_thinking_bot5 = gemini_flash_20_thinking.OptimizedNegamaxBot("gemini-flash-2.0-thinking P8", "?", profondeur=8)
gemini_pro_20_bot5 = gemini_pro_20.MTDfbBot("gemini-pro-2.0 P8", "?", profondeur=8)
gemma3_bot5 = gemma3.SigmaBot("Gemma2 P8", "?", profondeur=8)
o1_bot5 = o1.GrandMasterBot("o1 P8", "?", profondeur=8)
lechat_bot6 = lechat.AdvancedConnect4Bot("LeChat P10", "?", profondeur=10)
qwq_bot4 = qwq.AdvancedNegamaxBot("QwQ P6", "?", profondeur=6)
gemini25_pro_bot4 = gemini25_pro.StrategosPrime("Gemini2.5 Pro P6", "?", profondeur=6)
gemini25_flash_thinking_bot5 = gemini25_flash_thinking.BetaBot("Gemini2.5 Flash Thinking P8", "?", profondeur=8)
qwen3_bot4 = qwen3.ThreatHunterBot("Qwen3 P6", "?", profondeur=6)
o4_mini_high_bot7 = o4_mini_high.QuantumNexus("o4-mini-high P12", "?", profondeur=12)
o3_bot6 = o3.StellarStorm("o3 P10", "?", profondeur=10)
gpt5_thinking_bot1 = gpt5.Aetherion("gpt5 P8", "?", profondeur=8, temps_max=0.5)
participants = [
    original_negamax_4,
    negamaxv2_5,
    negamaxv3_5,
    negamaxv4_22,
    negamaxv5_23,
    negamaxv5b_23,
    default_bot,
    random_bot,
    gpt4o_bot23,
    o3_mini_high_bot4,
    claude37_sonnet_bot6,
    claude37_sonnet_thinking_bot5,
    same_dev_bot4,
    r1_bot5,
    gemini_flash_20_bot5,
    gemini_flash_20_thinking_bot5,
    gemini_pro_20_bot5,
    gemma3_bot5,
    o1_bot5,
    lechat_bot6,
    qwq_bot4,
    gemini25_pro_bot4,
    gemini25_flash_thinking_bot5,
    qwen3_bot4,
    o4_mini_high_bot7,
    o3_bot6,
]
