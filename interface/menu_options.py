# Menu Options
import pygame
import pygame_widgets
from pygame_widgets.slider import Slider
from interface import boutton
from utils import afficher_texte, dict_couleurs, largeur_fenetre, hauteur_fenetre, couleur_plateau, couleurs_jetons

hauteur_slider_musique = hauteur_fenetre//2 - 125
arriere_plan = pygame.image.load("assets/images/menu_arrière_plan.jpg")
arriere_plan = pygame.transform.scale(arriere_plan, (largeur_fenetre, hauteur_fenetre))
boutton_revenir= boutton.Boutton(largeur_fenetre // 2, hauteur_fenetre // 2 + 250, 300, 75, "Revenir", dict_couleurs["bleu boutton"])
no_sound_image = pygame.image.load("assets/images/no-volume.png")
no_sound_image = pygame.transform.scale(no_sound_image, (150, 150))
no_sound_rect = no_sound_image.get_rect()
no_sound_rect.center = largeur_fenetre//2-275, hauteur_slider_musique + 25
sound_image = pygame.image.load("assets/images/volume.png")
sound_image = pygame.transform.scale(sound_image, (150, 150))
sound_image_rect = sound_image.get_rect()
sound_image_rect.center = largeur_fenetre//2-275, hauteur_slider_musique + 25

def main():
    en_cours = True
    clock = pygame.time.Clock()
    fenetre = pygame.display.set_mode((largeur_fenetre, hauteur_fenetre))
    slider_musique = Slider(fenetre, largeur_fenetre//2-int(300/2), hauteur_slider_musique, 300, 50, min=0, max=100, handleColour=couleur_plateau, valueColour=dict_couleurs["bleu boutton"])
    pygame.display.set_caption("Options")
    while en_cours:
        fenetre.blit(arriere_plan, (0, 0))
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if boutton_revenir.boutton_clické(event):
                    return
        afficher_texte(fenetre, largeur_fenetre//2, 75, "Options", 100, couleur=dict_couleurs["bleu marin"])
        boutton_revenir.afficher(fenetre)

        afficher_texte(fenetre, largeur_fenetre//2-100, largeur_fenetre//2, "Jetons :", 60, couleur=dict_couleurs["bleu marin"])

        if slider_musique.getValue() == 0:
            fenetre.blit(no_sound_image, no_sound_rect)
        else:
            fenetre.blit(sound_image, sound_image_rect)
        pygame_widgets.update(events)
        pygame.display.update()
        clock.tick(60)