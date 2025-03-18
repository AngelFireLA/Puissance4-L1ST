import pygame
import pygame_widgets
from pygame_widgets.textbox import TextBox
from ..utils import afficher_texte, dict_couleurs, largeur_fenetre, hauteur_fenetre, mettre_à_jour_port, chemin_absolu_dossier
from .boutton import Boutton

arriere_plan = pygame.image.load(chemin_absolu_dossier+"assets/images/menu_arrière_plan.jpg")
arriere_plan = pygame.transform.scale(arriere_plan, (largeur_fenetre, hauteur_fenetre))

def main():
    clock = pygame.time.Clock()
    fenetre = pygame.display.set_mode((largeur_fenetre, hauteur_fenetre))
    pygame.display.set_caption("Menu Puissance 4")

    zone_texte_pour_port = TextBox(fenetre, largeur_fenetre // 2 - 150, 200, 300, 75, fontSize=36)
    zone_texte_pour_port.setText("")

    continue_button = Boutton(x=largeur_fenetre // 2, y=350, largeur=300, hauteur=50, texte="Continuer", couleur=dict_couleurs["bleu boutton"], montrer=False)

    en_cours = True
    while en_cours:
        fenetre.blit(arriere_plan, (0, 0))
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            if event.type == pygame.MOUSEBUTTONDOWN and continue_button.boutton_clické(event):

                try:
                    port_value = int(zone_texte_pour_port.getText())
                    if 1024 <= port_value <= 49151:
                        mettre_à_jour_port(port_value)
                        return port_value
                except ValueError as e:
                    pass

        afficher_texte(fenetre, largeur_fenetre // 2, 150, "Entrez un port ouvert :", 40, couleur=dict_couleurs["bleu marin"])

        try:
            port_value = int(zone_texte_pour_port.getText())
            if 1024 <= port_value <= 49151:
                continue_button.montrer = True
            else:
                continue_button.montrer = False
        except ValueError:
            continue_button.montrer = False

        zone_texte_pour_port.draw()
        continue_button.afficher(fenetre)

        pygame_widgets.update(events)
        clock.tick(60)
        pygame.display.flip()
