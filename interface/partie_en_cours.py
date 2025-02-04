import pygame

import bots.random_bot
from moteur.partie import Partie
from moteur.joueur import Joueur
from bots import bot, random_bot, negamax, negamaxv2

def afficher_grille():
    for x in range(plateau_largeur+1):
        pygame.draw.line(fenetre, (0, 0, 0), (x * taille_case + decalage, decalage), (x * taille_case + decalage, plateau_hauteur * taille_case + decalage), width=3)
        for y in range(plateau_hauteur+1):
            pygame.draw.line(fenetre, (0, 0, 0), (decalage, y * taille_case + decalage), (plateau_largeur * taille_case + decalage, y * taille_case + decalage), width=3)

def p_x(colonne):
    return colonne * taille_case + taille_case//2 + decalage

def p_y(ligne):
    return ((plateau_hauteur-1-ligne) * taille_case + taille_case//2) + decalage

def previsualise_pion(colonne, symbole):
    couleur = (*couleurs_jetons[symbole], 128)
    surface = pygame.Surface((taille_case, taille_case), pygame.SRCALPHA)  # Create a surface with alpha channel
    pygame.draw.circle(surface, couleur, (taille_case // 2, taille_case // 2), taille_case // 3)
    fenetre.blit(surface, (p_x(colonne) - taille_case // 2, decalage // 2 - taille_case // 2))


def afficher_pions():
    for ligne in range(partie.plateau.lignes - 1, -1, -1):
        for colonne in range(partie.plateau.colonnes):
            if ligne < partie.plateau.hauteurs_colonnes[colonne]:
                symbole = partie.plateau.grille[colonne][ligne]
                pygame.draw.circle(fenetre, couleurs_jetons[symbole], (p_x(colonne), p_y(ligne)), taille_case//3)

def est_tour_bot(partie) -> bool:
    return partie.tour_joueur == 2 and isinstance(partie.joueur2, bot.Bot)

def animation_jeton(colonne, final_ligne, symbole):
    x = p_x(colonne)
    start_y = decalage // 2
    target_y = p_y(final_ligne)
    current_y = start_y
    vitesse = 3
    while current_y < target_y:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
        current_y += vitesse
        if current_y > target_y:
            current_y = target_y
        affiche_trucs_de_base()
        pygame.draw.circle(fenetre, couleurs_jetons[symbole], (x, int(current_y)), taille_case//3)
        pygame.display.flip()

def affiche_trucs_de_base():
    fenetre.fill((255, 255, 255))
    afficher_grille()
    afficher_pions()


animation_en_cours = False

def main():
    global partie, plateau_largeur, plateau_hauteur, taille_case, decalage, fenetre, couleurs_jetons, partie_en_cours, animation_en_cours
    partie = Partie()
    joueur1 = Joueur("Joueur 1", "X")
    joueur2 = bots.negamaxv2.Negamax2("Joueur 2", "O", profondeur=8)
    # joueur2 = Joueur("Joueur 2", "O")
    partie.ajouter_joueur(joueur1)
    partie.ajouter_joueur(joueur2)
    plateau_largeur = partie.plateau.colonnes
    plateau_hauteur = partie.plateau.lignes
    taille_case = 100
    decalage = 100
    fenetre = pygame.display.set_mode(
        (plateau_largeur * taille_case + decalage * 2, plateau_hauteur * taille_case + decalage * 2))
    pygame.display.set_caption("Partie de Puissance 4")

    couleurs_jetons = {'X': (255, 0, 255), 'O': (255, 255, 0)}
    partie_en_cours = True
    while partie_en_cours:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                partie_en_cours = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if est_tour_bot(partie):
                    print("bot joue")
                    colonne = partie.joueur2.trouver_coup(partie.plateau, partie.joueur1)
                    print(partie.joueur2.coups)
                else:
                    colonne = (event.pos[0] - decalage) // taille_case
                final_ligne = partie.plateau.hauteurs_colonnes[colonne]
                symbole = partie.joueur1.symbole if partie.tour_joueur == 1 else partie.joueur2.symbole
                animation_jeton(colonne, final_ligne, symbole)
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

        affiche_trucs_de_base()
        mouse = pygame.mouse.get_pos()
        if decalage < mouse[0] < decalage + taille_case * plateau_largeur and not est_tour_bot(partie):
            colonne = (mouse[0] - decalage) // taille_case
            symbole = partie.joueur1.symbole if partie.tour_joueur == 1 else partie.joueur2.symbole
            previsualise_pion(colonne, symbole)
        pygame.display.flip()