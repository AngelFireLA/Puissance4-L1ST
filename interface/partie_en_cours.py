import random

import pygame

import bots.random_bot
from moteur.partie import Partie
from moteur.joueur import Joueur
from bots import bot, random_bot, negamax, negamaxv2, menu_pause
from utils import afficher_texte, dict_couleurs, couleurs_jetons, couleur_plateau


def afficher_grille():
    grid_width = plateau_largeur * taille_case
    grid_height = plateau_hauteur * taille_case
    grid_surface = pygame.Surface((grid_width, grid_height), pygame.SRCALPHA)

    # Fill the grid surface with the blue color
    grid_surface.fill(couleur_plateau)

    # Set margin to adjust the hole size (change this value to fine-tune the look)
    margin = 10
    # Calculate the radius so that the circle fits nicely within a cell
    radius = taille_case // 2 - margin

    # Loop over each cell in the grid.
    # We use (plateau_hauteur - 1 - row) so that row 0 appears at the bottom.
    for row in range(plateau_hauteur):
        for col in range(plateau_largeur):
            center_x = col * taille_case + taille_case // 2
            center_y = (plateau_hauteur - 1 - row) * taille_case + taille_case // 2
            pygame.draw.circle(grid_surface, (0, 0, 0, 0), (center_x, center_y), radius)

    fenetre.blit(grid_surface, (decalage, decalage))


def p_x(colonne):
    return colonne * taille_case + taille_case//2 + decalage

def p_y(ligne):
    return ((plateau_hauteur-1-ligne) * taille_case + taille_case//2) + decalage

def previsualise_pion(colonne, symbole):
    couleur = (*couleurs_jetons[symbole], 255)
    surface = pygame.Surface((taille_case, taille_case), pygame.SRCALPHA)  # Create a surface with alpha channel
    pygame.draw.circle(surface, couleur, (taille_case // 2, taille_case // 2), taille_jeton)
    fenetre.blit(surface, (p_x(colonne) - taille_case // 2, decalage // 2 - taille_case // 2))


def afficher_pions():
    for ligne in range(partie.plateau.lignes - 1, -1, -1):
        for colonne in range(partie.plateau.colonnes):
            if ligne < partie.plateau.hauteurs_colonnes[colonne]:
                symbole = partie.plateau.grille[colonne][ligne]
                pygame.draw.circle(fenetre, couleurs_jetons[symbole], (p_x(colonne), p_y(ligne)), taille_jeton)

def est_tour_bot(partie) -> bool:
    return partie.tour_joueur == 2 and isinstance(partie.joueur2, bot.Bot)

def animation_jeton(colonne, ligne_finale, symbole):
    pos_x = p_x(colonne)
    depart_y = decalage // 2
    cible_y = p_y(ligne_finale)
    pos_y = depart_y
    vitesse_y = 0
    acceleration = 1
    horloge = pygame.time.Clock()
    while pos_y < cible_y:
        for evenement in pygame.event.get():
            if evenement.type == pygame.QUIT:
                pygame.quit()
                exit()
        vitesse_y += acceleration
        pos_y += vitesse_y
        if pos_y > cible_y:
            pos_y = cible_y
        affiche_trucs_de_base()
        pygame.draw.circle(fenetre, couleurs_jetons[symbole], (pos_x, int(pos_y)), taille_jeton)
        horloge.tick(60)
        pygame.display.flip()


def affiche_trucs_de_base():
    fenetre.blit(arriere_plan, (0, 0))
    afficher_grille()
    afficher_pions()


noms_robots = ["Terminator", "Dalek", "R2D2", "C3PO", "Wall-E", "Bender"]
taille_case = 100
decalage = 80
taille_jeton = taille_case//2 - 10

partie = Partie()

def main(profondeur=6):
    global partie, plateau_largeur, plateau_hauteur, taille_case, decalage, fenetre, partie_en_cours, arriere_plan
    partie = Partie()
    clock = pygame.time.Clock()
    joueur1 = Joueur("Joueur 1", "X")
    if profondeur > 0:
        joueur2 = bots.negamaxv2.Negamax2(random.choice(noms_robots), "O", profondeur=profondeur)
    else:
        joueur2 = Joueur("Joueur 2", "O")
    # joueur2 = Joueur("Joueur 2", "O")
    partie.ajouter_joueur(joueur1)
    partie.ajouter_joueur(joueur2)
    plateau_largeur = partie.plateau.colonnes
    plateau_hauteur = partie.plateau.lignes
    arriere_plan = pygame.image.load("../assets/images/menu_arrière_plan.jpg")
    largeur_fenetre, hauteur_fenetre = plateau_largeur * taille_case + decalage * 2, plateau_hauteur * taille_case + decalage * 2
    arriere_plan = pygame.transform.scale(arriere_plan, (largeur_fenetre, hauteur_fenetre))

    fenetre = pygame.display.set_mode((largeur_fenetre, hauteur_fenetre))
    pygame.display.set_caption("Partie de Puissance 4")
    partie_en_cours = True
    while partie_en_cours:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
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
                        afficher_texte(fenetre, largeur_fenetre // 2, hauteur_fenetre // 2, f"Match nul !", 60, dict_couleurs["bleu marin"])
                        pygame.display.flip()
                        pygame.time.wait(3000)
                        partie_en_cours = False
                    if partie.plateau.est_victoire(colonne):
                        joueur_actuel = partie.joueur1 if partie.tour_joueur == 1 else partie.joueur2
                        afficher_texte(fenetre, largeur_fenetre // 2, hauteur_fenetre // 2, f"Victoire de {joueur_actuel.nom} !", 60, dict_couleurs["bleu marin"])
                        pygame.display.flip()
                        pygame.time.wait(3000)
                        partie_en_cours = False

                    if partie.tour_joueur == 1:
                        partie.tour_joueur = 2
                    else:
                        partie.tour_joueur = 1

            #if escape is pressed, show pause menu :
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if menu_pause.main():
                        partie_en_cours = False
                        return
                    else:
                        fenetre = pygame.display.set_mode((largeur_fenetre, hauteur_fenetre))
        affiche_trucs_de_base()
        mouse = pygame.mouse.get_pos()
        if decalage < mouse[0] < decalage + taille_case * plateau_largeur and not est_tour_bot(partie):
            colonne = (mouse[0] - decalage) // taille_case
            symbole = partie.joueur1.symbole if partie.tour_joueur == 1 else partie.joueur2.symbole
            previsualise_pion(colonne, symbole)
        if partie_en_cours: pygame.display.flip()
        clock.tick(60)
