import random
import socket
import pygame

import bots.random_bot
from moteur.partie import Partie
from moteur.joueur import Joueur
from interface import menu_pause
from bots import negamaxv5
from utils import afficher_texte, dict_couleurs, couleurs_jetons, couleur_plateau, est_local, récupérer_port, récupérer_ip_cible
import uuid


def afficher_grille(plateau_largeur, plateau_hauteur, fenetre):
    largeur_grille = plateau_largeur * taille_case
    hauteur_grille = plateau_hauteur * taille_case
    surface_grille = pygame.Surface((largeur_grille, hauteur_grille), pygame.SRCALPHA)

    surface_grille.fill(couleur_plateau)
    marge = 10
    rayon = taille_case // 2 - marge

    for ligne in range(plateau_hauteur):
        for colonne in range(plateau_largeur):
            centre_x = colonne * taille_case + taille_case // 2
            centre_y = (plateau_hauteur - 1 - ligne) * taille_case + taille_case // 2
            pygame.draw.circle(surface_grille, (0, 0, 0, 0), (centre_x, centre_y), rayon)

    fenetre.blit(surface_grille, (decalage, decalage))


def p_x(colonne):
    return colonne * taille_case + taille_case//2 + decalage


def p_y(ligne, plateau_hauteur):
    return ((plateau_hauteur-1-ligne) * taille_case + taille_case//2) + decalage


def previsualise_pion(colonne, symbole, fenetre):
    couleur = (*couleurs_jetons[symbole], 255)
    surface = pygame.Surface((taille_case, taille_case), pygame.SRCALPHA)  # Create a surface with alpha channel
    pygame.draw.circle(surface, couleur, (taille_case // 2, taille_case // 2), taille_jeton)
    fenetre.blit(surface, (p_x(colonne) - taille_case // 2, decalage // 2 - taille_case // 2))


def afficher_pions(plateau_hauteur, partie, fenetre):
    for ligne in range(partie.plateau.lignes - 1, -1, -1):
        for colonne in range(partie.plateau.colonnes):
            if ligne < partie.plateau.hauteurs_colonnes[colonne]:
                symbole = partie.plateau.grille[colonne][ligne]
                pygame.draw.circle(fenetre, couleurs_jetons[symbole], (p_x(colonne), p_y(ligne, plateau_hauteur)), taille_jeton)


def est_tour_bot(partie) -> bool:
    return partie.tour_joueur == 2 and isinstance(partie.joueur2, negamaxv5.Negamax5)


def affiche_trucs_de_base(plateau_largeur, plateau_hauteur, arriere_plan, partie, fenetre):
    fenetre.blit(arriere_plan, (0, 0))
    afficher_grille(plateau_largeur, plateau_hauteur, fenetre)
    afficher_pions(plateau_hauteur, partie, fenetre)


def tour_opposé(tour):
    return 1 if tour == 2 else 2


def vérifie_fin_de_partie(fenêtre, hauteur_fenêtre, largeur_fenêtre, partie, colonne_choisie):
    joueur_actuel = partie.joueur1 if partie.tour_joueur == 1 else partie.joueur2
    if partie.plateau.est_nul():
        print("Match nul")
        afficher_texte(fenêtre, largeur_fenêtre // 2, hauteur_fenêtre // 2, f"Match nul !", 60, dict_couleurs["bleu marin"])
        pygame.display.flip()
        pygame.time.wait(3000)
        return False
    if partie.plateau.est_victoire(colonne_choisie):
        afficher_texte(fenêtre, largeur_fenêtre // 2, hauteur_fenêtre // 2, f"Victoire de {joueur_actuel.nom} !", 60, dict_couleurs["bleu marin"])
        pygame.display.flip()
        pygame.time.wait(3000)
        return False
    return True


noms_robots = ["Terminator", "Dalek", "R2D2", "C3PO", "Wall-E", "Bender"]
taille_case = 100
decalage = 90
taille_jeton = taille_case//2 - 10


def main(profondeur=6):
    def animation_jeton(colonne, ligne_finale, symbole):
        pos_x = p_x(colonne)
        depart_y = decalage // 2
        cible_y = p_y(ligne_finale, plateau_hauteur)
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
            affiche_trucs_de_base(plateau_largeur, plateau_hauteur, arriere_plan, partie, fenetre)
            pygame.draw.circle(fenetre, couleurs_jetons[symbole], (pos_x, int(pos_y)), taille_jeton)
            horloge.tick(60)
            pygame.display.flip()

    partie = Partie()
    partie.tour_joueur = 1
    clock = pygame.time.Clock()
    joueur1 = Joueur("Joueur 1", "X")
    if profondeur > 0:
        temp_de_pensée_max = 3 if profondeur >= 8 else 0
        joueur2 = bots.negamaxv5.Negamax5(random.choice(noms_robots), "O", profondeur=profondeur, temps_max=temp_de_pensée_max)

    else:
        joueur2 = Joueur("Joueur 2", "O")
    # joueur2 = Joueur("Joueur 2", "O")
    partie.ajouter_joueur(joueur1)
    partie.ajouter_joueur(joueur2)
    plateau_largeur = partie.plateau.colonnes
    plateau_hauteur = partie.plateau.lignes
    arriere_plan = pygame.image.load("assets/images/menu_arrière_plan.jpg")
    largeur_fenetre, hauteur_fenetre = plateau_largeur * taille_case + decalage * 2, plateau_hauteur * taille_case + decalage * 2
    arriere_plan = pygame.transform.scale(arriere_plan, (largeur_fenetre, hauteur_fenetre))
    fenetre = pygame.display.set_mode((largeur_fenetre, hauteur_fenetre))
    pygame.display.set_caption("Partie de Puissance 4")
    partie_en_cours = True
    while partie_en_cours:
        for event in pygame.event.get():
            affiche_trucs_de_base(plateau_largeur, plateau_hauteur, arriere_plan, partie, fenetre)
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                colonne = (event.pos[0] - decalage) // taille_case
                ligne_finale = partie.plateau.hauteurs_colonnes[colonne]
                symbole = partie.joueur1.symbole if partie.tour_joueur == 1 else partie.joueur2.symbole
                animation_jeton(colonne, ligne_finale, symbole)
                if partie.jouer(colonne, partie.tour_joueur):

                    partie_en_cours = vérifie_fin_de_partie(fenetre, hauteur_fenetre, largeur_fenetre, partie, colonne)

                    if partie.tour_joueur == 1:
                        partie.tour_joueur = 2
                    else:
                        partie.tour_joueur = 1


            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if menu_pause.main():
                        return
                    else:
                        fenetre = pygame.display.set_mode((largeur_fenetre, hauteur_fenetre))

        if est_tour_bot(partie):
            pygame.time.wait(500)
            afficher_texte(fenetre, largeur_fenetre//2, decalage//2, f"{joueur2.nom} réfléchit...", 45, dict_couleurs["bleu marin"])
            pygame.display.flip()
            colonne = partie.joueur2.trouver_coup(partie.plateau, partie.joueur1)
            #print("Coups évalués :", partie.joueur2.coups)
            ligne_finale = partie.plateau.hauteurs_colonnes[colonne]
            symbole = partie.joueur1.symbole if partie.tour_joueur == 1 else partie.joueur2.symbole
            animation_jeton(colonne, ligne_finale, symbole)
            if partie.jouer(colonne, partie.tour_joueur):

                partie_en_cours = vérifie_fin_de_partie(fenetre, hauteur_fenetre, largeur_fenetre, partie, colonne)

                if partie.tour_joueur == 1:
                    partie.tour_joueur = 2
                else:
                    partie.tour_joueur = 1

        mouse = pygame.mouse.get_pos()
        if decalage < mouse[0] < decalage + taille_case * plateau_largeur and not est_tour_bot(partie):
            colonne = (mouse[0] - decalage) // taille_case
            symbole = partie.joueur1.symbole if partie.tour_joueur == 1 else partie.joueur2.symbole
            previsualise_pion(colonne, symbole, fenetre)
        if partie_en_cours: pygame.display.flip()
        clock.tick(60)


def main_multi():
    def animation_jeton(colonne, ligne_finale, symbole):
        pos_x = p_x(colonne)
        depart_y = decalage // 2
        cible_y = p_y(ligne_finale, plateau_hauteur)
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
            affiche_trucs_de_base(plateau_largeur, plateau_hauteur, arriere_plan, partie, fenetre)
            pygame.draw.circle(fenetre, couleurs_jetons[symbole], (pos_x, int(pos_y)), taille_jeton)
            horloge.tick(60)
            pygame.display.flip()

    partie = Partie()
    clock = pygame.time.Clock()
    plateau_largeur = partie.plateau.colonnes
    plateau_hauteur = partie.plateau.lignes
    arriere_plan = pygame.image.load("assets/images/menu_arrière_plan.jpg")
    largeur_fenetre, hauteur_fenetre = plateau_largeur * taille_case + decalage * 2, plateau_hauteur * taille_case + decalage * 2
    arriere_plan = pygame.transform.scale(arriere_plan, (largeur_fenetre, hauteur_fenetre))

    fenetre = pygame.display.set_mode((largeur_fenetre, hauteur_fenetre))
    pygame.display.set_caption("Partie de Puissance 4")

    port = récupérer_port()
    local = est_local()
    socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ip_serveur = récupérer_ip_cible() if not local else "127.0.0.1"
    socket_client.connect((ip_serveur, port))
    #make socket not blocking
    socket_client.setblocking(False)
    nom_utilisateur = str(uuid.uuid4())
    socket_client.sendall(f"@connexion:{nom_utilisateur}".encode('utf-8'))
    print("Connexion établie")
    fenetre.blit(arriere_plan, (0, 0))
    afficher_texte(fenetre, largeur_fenetre//2, hauteur_fenetre//2, "En attente d'un adversaire...", 60, dict_couleurs["bleu marin"])
    pygame.display.flip()
    réponse = ""
    while not réponse.startswith("@commencer:"):
        try:
            réponse = socket_client.recv(2048).decode('utf-8')
        except BlockingIOError:
            pass
        clock.tick(60)
    print("Partie va commencer")
    indexe_joueur, nom_adversaire = réponse.split(":")[1].split("|")
    indexe_joueur = int(indexe_joueur)
    joueur1 = Joueur(nom_utilisateur, "X")
    joueur2 = Joueur(nom_adversaire, "O")

    partie.ajouter_joueur(joueur1)
    partie.ajouter_joueur(joueur2)

    partie_en_cours = True
    colonne_choisie = None
    while partie_en_cours:
        affiche_trucs_de_base(plateau_largeur, plateau_hauteur, arriere_plan, partie, fenetre)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if partie.tour_joueur == indexe_joueur:
                    colonne_choisie = (event.pos[0] - decalage) // taille_case
                    socket_client.sendall(f"@jouer:{colonne_choisie}".encode('utf-8'))

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if menu_pause.main():
                        return
                    else:
                        fenetre = pygame.display.set_mode((largeur_fenetre, hauteur_fenetre))

        if partie.tour_joueur == tour_opposé(indexe_joueur):
            try:
                réponse = socket_client.recv(2048).decode('utf-8')
                if réponse.startswith("@jouer:"):
                    colonne_choisie = int(réponse.split(":")[1])
            except BlockingIOError:
                pass

        if colonne_choisie is not None:
            ligne_finale = partie.plateau.hauteurs_colonnes[colonne_choisie]
            symbole = partie.joueur1.symbole if partie.tour_joueur == 1 else partie.joueur2.symbole
            animation_jeton(colonne_choisie, ligne_finale, symbole)
            if partie.jouer(colonne_choisie, partie.tour_joueur):

                if partie.plateau.est_nul():
                    print("Match nul")
                    afficher_texte(fenetre, largeur_fenetre // 2, hauteur_fenetre // 2, f"Match nul !", 60,
                                   dict_couleurs["bleu marin"])
                    pygame.display.flip()
                    pygame.time.wait(3000)
                    partie_en_cours = False
                    socket_client.close()
                if partie.plateau.est_victoire(colonne_choisie):
                    texte_résultat = "Victoire !" if partie.tour_joueur == indexe_joueur else f"Défaite !"
                    afficher_texte(fenetre, largeur_fenetre // 2, hauteur_fenetre // 2,
                                   texte_résultat, 60, dict_couleurs["bleu marin"])
                    pygame.display.flip()
                    pygame.time.wait(3000)
                    partie_en_cours = False
                    socket_client.close()

                if partie.tour_joueur == 1:
                    partie.tour_joueur = 2
                else:
                    partie.tour_joueur = 1
            colonne_choisie = None

        mouse = pygame.mouse.get_pos()
        if decalage < mouse[0] < decalage + taille_case * plateau_largeur and partie.tour_joueur == indexe_joueur:
            colonne = (mouse[0] - decalage) // taille_case
            symbole = partie.joueur1.symbole if partie.tour_joueur == 1 else partie.joueur2.symbole
            previsualise_pion(colonne, symbole, fenetre)
        if partie_en_cours: pygame.display.flip()
        clock.tick(60)
