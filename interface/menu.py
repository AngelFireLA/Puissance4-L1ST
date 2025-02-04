import pygame
import interface.boutton as boutton
import partie_en_cours
pygame.init()

def main():
    largeur_fenetre, hauteur_fenetre = 800, 600

    fenetre = pygame.display.set_mode((largeur_fenetre, hauteur_fenetre))
    pygame.display.set_caption("Menu Puissance 4")
    arriere_plan = pygame.image.load("../assets/images/menu_arrière_plan.jpg")
    arriere_plan = pygame.transform.scale(arriere_plan, (largeur_fenetre, hauteur_fenetre))
    démarrer = boutton.Boutton(largeur_fenetre//2, hauteur_fenetre//2, 300, 200, "Jouer", (240, 220, 220), amplitude_arrondi=1.2)
    
    while True:
        fenetre.blit(arriere_plan, (0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if démarrer.rect.collidepoint(event.pos):
                    partie_en_cours.main()
                    fenetre = pygame.display.set_mode((largeur_fenetre, hauteur_fenetre))
        démarrer.afficher(fenetre)
        pygame.display.update()

if __name__ == "__main__":
    main()