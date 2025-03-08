import pygame

from interface import boutton, partie_en_cours
from utils import afficher_texte, dict_couleurs, largeur_fenetre, hauteur_fenetre, est_local, charger_config, récupérer_port, mettre_à_jour_port, mettre_à_jour_ip
import threading
import multijoueur.serveur as serveur
import interface.entrer_port_menu as entrer_port_menu
import interface.rejoindre_partie_menu as rejoindre_partie_menu
arriere_plan = pygame.image.load("assets/images/menu_arrière_plan.jpg")
arriere_plan = pygame.transform.scale(arriere_plan, (largeur_fenetre, hauteur_fenetre))
boutton_créer_partie = boutton.Boutton(largeur_fenetre // 2, hauteur_fenetre // 2 - 75, 450, 100, "Créer une partie",
                                       dict_couleurs["bleu boutton"])
boutton_rejoindre_partie = boutton.Boutton(largeur_fenetre // 2, hauteur_fenetre // 2 + 75, 450, 100,
                                           "Rejoindre une partie", dict_couleurs["bleu boutton"])
def main():
    clock = pygame.time.Clock()
    fenetre = pygame.display.set_mode((largeur_fenetre, hauteur_fenetre))
    pygame.display.set_caption("Menu Puissance 4")

    en_cours = True
    while en_cours:
        fenetre.blit(arriere_plan, (0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if boutton_créer_partie.boutton_clické(event):
                    port_pour_serveur = récupérer_port()
                    while not type(port_pour_serveur) == int or port_pour_serveur < 0:
                        entrer_port_menu.main()
                        port_pour_serveur = récupérer_port()
                    mettre_à_jour_ip("127.0.0.1")
                    if est_local():
                        threading.Thread(target=serveur.main, args=(port_pour_serveur,), daemon=True).start()
                    else:
                        threading.Thread(target=serveur.main, args=(port_pour_serveur,), daemon=True).start()
                    partie_en_cours.main_multi()
                    #close the server
                    serveur.éteint_serveur()
                    fenetre = pygame.display.set_mode((largeur_fenetre, hauteur_fenetre))

                if boutton_rejoindre_partie.boutton_clické(event):
                    rejoindre_partie_menu.main()
                    fenetre = pygame.display.set_mode((largeur_fenetre, hauteur_fenetre))
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return

        afficher_texte(fenetre, largeur_fenetre//2, 90, "Multijoueur :", 75, couleur=dict_couleurs["bleu marin"])
        boutton_créer_partie.afficher(fenetre)
        boutton_rejoindre_partie.afficher(fenetre)
        pygame.display.flip()
        clock.tick(60)
