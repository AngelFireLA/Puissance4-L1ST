import random
import pygame
pygame.init()

import interface.boutton as boutton
import partie_en_cours
import menu_solo
import menu_options
import menu_multijoueur
from utils import afficher_texte, dict_couleurs, largeur_fenetre, hauteur_fenetre


arriere_plan = pygame.image.load("../assets/images/menu_arrière_plan.jpg")
arriere_plan = pygame.transform.scale(arriere_plan, (largeur_fenetre, hauteur_fenetre))
boutton_troll = boutton.Boutton(75, hauteur_fenetre // 2 + 250, 100, 50, "Quitter", (255, 0, 0), amplitude_arrondi=1.2, couleur_surlignée=(255, 50, 50))
boutton_solo = boutton.Boutton(largeur_fenetre // 2, hauteur_fenetre // 2 - 100, 350, 75, "Solo", dict_couleurs["bleu boutton"])
boutton_local = boutton.Boutton(largeur_fenetre // 2, hauteur_fenetre // 2, 350, 75, "1v1 Local", dict_couleurs["bleu boutton"])
boutton_multijoueur = boutton.Boutton(largeur_fenetre // 2, hauteur_fenetre // 2 + 100, 350, 75, "Multijoueur", dict_couleurs["bleu boutton"])
boutton_options = boutton.Boutton(largeur_fenetre // 2, hauteur_fenetre // 2 + 200, 350, 75, "Options", dict_couleurs["bleu boutton"])
def main():
    clock = pygame.time.Clock()
    fenetre = pygame.display.set_mode((largeur_fenetre, hauteur_fenetre))
    pygame.display.set_caption("Menu Puissance 4")
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEMOTION:
                if pygame.time.get_ticks() % 5 == 0:
                    if boutton_troll.rect.collidepoint(event.pos):
                        boutton_troll.x = random.randint(boutton_troll.largeur // 2,
                                                         largeur_fenetre - boutton_troll.largeur // 2)
                        boutton_troll.y = random.randint(boutton_troll.hauteur // 2,
                                                         hauteur_fenetre - boutton_troll.hauteur // 2)
                        boutton_troll.génère_rect()
                        while boutton_troll.rect.colliderect(boutton_solo.rect) or boutton_troll.rect.colliderect(boutton_local.rect) or boutton_troll.rect.colliderect(boutton_options.rect) or boutton_troll.rect.colliderect(boutton_multijoueur.rect):
                            boutton_troll.x = random.randint(boutton_troll.largeur // 2,
                                                             largeur_fenetre - boutton_troll.largeur // 2)
                            boutton_troll.y = random.randint(boutton_troll.hauteur // 2,
                                                             hauteur_fenetre - boutton_troll.hauteur // 2)
                            boutton_troll.génère_rect()
            if event.type == pygame.MOUSEBUTTONDOWN:

                if boutton_solo.boutton_clické(event):
                    menu_solo.main()
                    fenetre = pygame.display.set_mode((largeur_fenetre, hauteur_fenetre))
                if boutton_local.boutton_clické(event):
                    partie_en_cours.main(profondeur=0)
                    fenetre = pygame.display.set_mode((largeur_fenetre, hauteur_fenetre))
                if boutton_troll.boutton_clické(event):
                    pygame.quit()
                    exit()
                if boutton_options.boutton_clické(event):
                    menu_options.main()
                    fenetre = pygame.display.set_mode((largeur_fenetre, hauteur_fenetre))
                if boutton_multijoueur.boutton_clické(event):
                    menu_multijoueur.main()
                    fenetre = pygame.display.set_mode((largeur_fenetre, hauteur_fenetre))

        fenetre.blit(arriere_plan, (0, 0))
        afficher_texte(fenetre, largeur_fenetre//2, 75, "Jouer", 100, couleur=dict_couleurs["bleu marin"])
        boutton_troll.afficher(fenetre)
        boutton_solo.afficher(fenetre)
        boutton_local.afficher(fenetre)
        boutton_options.afficher(fenetre)
        boutton_multijoueur.afficher(fenetre)
        pygame.display.update()
        clock.tick(60)

if __name__ == "__main__":
    main()