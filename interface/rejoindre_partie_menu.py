import pygame
import pygame_widgets
from pygame_widgets.textbox import TextBox
from utils import afficher_texte, dict_couleurs, largeur_fenetre, hauteur_fenetre, mettre_à_jour_port, mettre_à_jour_ip, ip_est_valide
from interface.boutton import Boutton
import ipaddress
import partie_en_cours

arriere_plan = pygame.image.load("../assets/images/menu_arrière_plan.jpg")
arriere_plan = pygame.transform.scale(arriere_plan, (largeur_fenetre, hauteur_fenetre))



def main():
    clock = pygame.time.Clock()
    fenetre = pygame.display.set_mode((largeur_fenetre, hauteur_fenetre))
    pygame.display.set_caption("Menu Puissance 4")

    zone_texte_pour_port = TextBox(fenetre, largeur_fenetre // 2 + 75, 200, 300, 75, fontSize=36)
    zone_texte_pour_port.setText("")
    zone_texte_pour_ip = TextBox(fenetre, largeur_fenetre // 2 + 75, 300, 300, 75, fontSize=36)
    zone_texte_pour_ip.setText("")
    continue_button = Boutton(x=largeur_fenetre // 2, y=450, largeur=300, hauteur=50, texte="Se Connecter", couleur=dict_couleurs["bleu boutton"], montrer=False)

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
                    port_choisi = int(zone_texte_pour_port.getText())
                    if 1024 <= port_choisi <= 49151:
                        mettre_à_jour_port(port_choisi)
                    ip_choisie = zone_texte_pour_ip.getText()
                    if not ip_est_valide(ip_choisie):
                        continue
                    mettre_à_jour_ip(ip_choisie)
                    partie_en_cours.main_multi()
                    fenetre = pygame.display.set_mode((largeur_fenetre, hauteur_fenetre))
                    return
                except ValueError as e:
                    pass

        afficher_texte(fenetre, largeur_fenetre // 2 - 150, 240, "Entrez un port ouvert :", 38, couleur=dict_couleurs["bleu marin"])
        afficher_texte(fenetre, largeur_fenetre // 2 - 150, 340, "Entrez l'IP du serveur :", 38, couleur=dict_couleurs["bleu marin"])
        try:
            port_choisi = int(zone_texte_pour_port.getText())
            ip_choisie = zone_texte_pour_ip.getText()
            if 1024 <= port_choisi <= 49151 and ip_est_valide(ip_choisie):
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