import pygame

import bots.random_bot
from moteur.partie import Partie
from moteur.joueur import Joueur
from bots import bot, random_bot, negamax, negamaxv2
pygame.init()

partie = Partie()
joueur1 = Joueur("Joueur 1", "X")
joueur2 = bots.negamaxv2.Negamax2("Joueur 2", "O", profondeur=10)
# joueur2 = Joueur("Joueur 2", "O")
partie.ajouter_joueur(joueur1)
partie.ajouter_joueur(joueur2)
plateau_largeur = partie.plateau.colonnes
plateau_hauteur = partie.plateau.lignes
taille_case = 100
decalage = 50
fenetre = pygame.display.set_mode((plateau_largeur * taille_case + decalage*2, plateau_hauteur * taille_case + decalage*2))
pygame.display.set_caption("Puissance 4")
def afficher_grille():
    for x in range(plateau_largeur+1):
        pygame.draw.line(fenetre, (0, 0, 0), (x * taille_case + decalage, decalage), (x * taille_case + decalage, plateau_hauteur * taille_case + decalage), width=3)
        for y in range(plateau_hauteur+1):
            pygame.draw.line(fenetre, (0, 0, 0), (decalage, y * taille_case + decalage), (plateau_largeur * taille_case + decalage, y * taille_case + decalage), width=3)

def p_x(colonne):
    return colonne * taille_case + taille_case//2 + decalage

def p_y(ligne):
    return ((plateau_hauteur-1-ligne) * taille_case + taille_case//2) + decalage

def afficher_pions():
    for ligne in range(partie.plateau.lignes - 1, -1, -1):
        for colonne in range(partie.plateau.colonnes):
            if ligne < partie.plateau.hauteurs_colonnes[colonne]:
                jeton = partie.plateau.grille[colonne][ligne]
                if jeton == "X":
                    joueur = 1
                else:
                    joueur = 2
                pygame.draw.circle(fenetre, (50*joueur, 50*joueur, 50*joueur), (p_x(colonne), p_y(ligne)), taille_case//3)

partie_en_cours = True
while partie_en_cours:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if partie.tour_joueur == 2 and isinstance(partie.joueur2, bot.Bot) :
                colonne = partie.joueur2.trouver_coup(partie.plateau, partie.joueur1)
                print(partie.joueur2.coups)
            else:
                colonne = (event.pos[0] - decalage) // taille_case
            if partie.jouer(colonne, partie.tour_joueur):

                if partie.plateau.est_nul():
                    print("Match nul")
                    partie_en_cours = False
                if partie.plateau.est_victoire(colonne):
                    print(f"Le joueur {partie.tour_joueur} a gagné")
                    partie_en_cours = False

                if partie.tour_joueur == 1:
                    partie.tour_joueur = 2
                else:
                    partie.tour_joueur = 1

    fenetre.fill((255, 255, 255))
    afficher_grille()
    afficher_pions()
    pygame.display.flip()
