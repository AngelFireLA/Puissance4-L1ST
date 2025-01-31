import pygame
pygame.init()
class Partie:
    def __init__(self, colonnes=7, lignes=6, joueur1=None, joueur2=None): self.plateau, self.joueur1, self.joueur2, self.tour_joueur = Plateau(colonnes, lignes), joueur1, joueur2, 1
    def jouer(self, colonne, num_joueur): return self.plateau.ajouter_jeton(colonne, self.joueur1.symbole if num_joueur == 1 else self.joueur2.symbole)
class Joueur:
    def __init__(self, nom, symbole): self.nom, self.symbole = nom, symbole
class Plateau:
    def __init__(self, colonnes=7, lignes=6): self.colonnes, self.lignes, self.grille, self.colonnes_jouables, self.hauteurs_colonnes = colonnes, lignes, [[] for _ in range(colonnes)], set(range(colonnes)), [0] * colonnes
    def colonne_valide(self, colonne): return 0 <= colonne < self.colonnes
    def ajouter_jeton(self, colonne, symbole):
        if colonne not in self.colonnes_jouables: return False
        self.grille[colonne].append(symbole)
        self.hauteurs_colonnes[colonne] += 1
        if self.colonne_pleine(colonne): self.colonnes_jouables.remove(colonne)
        return True
    def colonne_pleine(self, colonne): return self.hauteurs_colonnes[colonne] >= self.lignes
    def est_nul(self): return len(self.colonnes_jouables) == 0
    def est_victoire(self, colonne):
        jeton, jeton_ligne, directions, directions_potentielles = self.grille[colonne][-1], self.hauteurs_colonnes[colonne] - 1, [(1, 0), (-1, 0), (1, 1), (-1, 1), (1, -1), (-1, -1)], []
        if jeton_ligne > 2: directions_potentielles.append((0, 1))
        for direction in directions:
            c, l = colonne + direction[0], jeton_ligne + direction[1]
            if self.colonne_valide(c) and 0 <= l < self.hauteurs_colonnes[c] and self.grille[c][l] == jeton:directions_potentielles.append(direction)
        for direction_potentielle in directions_potentielles:
            compte = 1
            for i in [-1, 1]:
                while True:
                    c, l = colonne + i * direction_potentielle[0] * compte, jeton_ligne + i * direction_potentielle[1] * compte
                    if self.colonne_valide(c) and 0 <= l < self.hauteurs_colonnes[c] and self.grille[c][l] == jeton: compte += 1
                    else: break
            if compte >= 4: return True
partie = Partie(joueur1=Joueur("Joueur 1", 1), joueur2=Joueur("Joueur 2", 2))
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