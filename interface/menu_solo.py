import pygame
from utils import afficher_texte, dict_couleurs
from interface import boutton
from interface import partie_en_cours
def main():
    largeur_fenetre, hauteur_fenetre = 800, 600

    fenetre = pygame.display.set_mode((largeur_fenetre, hauteur_fenetre))
    pygame.display.set_caption("Menu Puissance 4")
    arriere_plan = pygame.image.load("../assets/images/menu_arrière_plan.jpg")
    arriere_plan = pygame.transform.scale(arriere_plan, (largeur_fenetre, hauteur_fenetre))
    boutton_difficulté_facile = boutton.Boutton(largeur_fenetre//2, hauteur_fenetre//2 - 150, 300, 75, "Facile", dict_couleurs["vert"], couleur_surlignée=(100, 255, 100))
    boutton_difficulté_moyen = boutton.Boutton(largeur_fenetre//2, hauteur_fenetre//2 - 50, 300, 75, "Moyen", dict_couleurs["jaune"], couleur_surlignée=(255, 255, 100))
    boutton_difficulté_difficile = boutton.Boutton(largeur_fenetre//2, hauteur_fenetre//2 + 50, 300, 75, "Difficile", dict_couleurs["orange"])
    boutton_difficulté_extreme = boutton.Boutton(largeur_fenetre//2, hauteur_fenetre//2 + 150, 300, 75, "Extrême", dict_couleurs["rouge"], couleur_surlignée=(255, 100, 100))
    en_cours = True
    while en_cours:
        fenetre.blit(arriere_plan, (0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                en_cours = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if boutton_difficulté_facile.boutton_clické(event):
                    partie_en_cours.main(profondeur=2)
                    en_cours = False
                if boutton_difficulté_moyen.boutton_clické(event):
                    partie_en_cours.main(profondeur=6)
                    en_cours = False
                if boutton_difficulté_difficile.boutton_clické(event):
                    partie_en_cours.main(profondeur=8)
                    en_cours = False
                if boutton_difficulté_extreme.boutton_clické(event):
                    partie_en_cours.main(profondeur=10)
                    en_cours = False

        afficher_texte(fenetre, largeur_fenetre//2, 50, "Difficulté : ", 50, couleur=(255, 255, 255))
        boutton_difficulté_facile.afficher(fenetre)
        boutton_difficulté_moyen.afficher(fenetre)
        boutton_difficulté_difficile.afficher(fenetre)
        boutton_difficulté_extreme.afficher(fenetre)
        if en_cours: pygame.display.update()
