import pygame
from moteur import partie, joueur
pygame.init()
partie = partie.Partie(joueur1=joueur.Joueur("Joueur 1", 1), joueur2=joueur.Joueur("Joueur 2", 2))
fenetre = pygame.display.set_mode((partie.plateau.colonnes * 100 + 50*2, partie.plateau.lignes * 100 + 50*2))
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if partie.jouer((event.pos[0] - 50) // 100, partie.tour_joueur):
                partie.tour_joueur = 1 if partie.tour_joueur == 2 else 2
                if partie.plateau.est_nul():
                    print("Match nul")
                    exit()
                if partie.plateau.est_victoire((event.pos[0] - 50) // 100):
                    print(f"Le joueur {partie.tour_joueur} a gagné")
                    exit()
    for x in range(partie.plateau.colonnes + 1):
        pygame.draw.line(fenetre, (255, 255, 255), (x * 100 + 50, 50),(x * 100 + 50, partie.plateau.lignes * 100 + 50), width=3)
        for y in range(partie.plateau.lignes + 1): pygame.draw.line(fenetre, (255, 255, 255), (50, y * 100 + 50), (partie.plateau.colonnes * 100 + 50, y * 100 + 50), width=3)
    for ligne in range(partie.plateau.lignes - 1, -1, -1):
        for colonne in range(partie.plateau.colonnes):
            if ligne < partie.plateau.hauteurs_colonnes[colonne]: pygame.draw.circle(fenetre, (100 * partie.plateau.grille[colonne][ligne], 100 * partie.plateau.grille[colonne][ligne], 100 * partie.plateau.grille[colonne][ligne]), (colonne * 100 + 100 // 2 + 50,((partie.plateau.lignes - 1 - ligne) * 100 + 100 // 2) + 50), 100 // 3)
    pygame.display.flip()