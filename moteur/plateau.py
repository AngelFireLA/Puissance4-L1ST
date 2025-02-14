import random

class Plateau:
    def __init__(self, colonnes=7, lignes=6, grille=None, colonnes_jouables=None, hauteurs_colonnes=None):
        self.colonnes = colonnes
        self.lignes = lignes
        self.grille = self.construire_grille() if grille is None else grille
        self.colonnes_jouables = set(range(self.colonnes)) if colonnes_jouables is None else colonnes_jouables
        self.hauteurs_colonnes = [0] * self.colonnes if hauteurs_colonnes is None else hauteurs_colonnes
    def construire_grille(self):
        return [[] for _ in range(self.colonnes)]

    def copier_grille(self):
        #without using colonne.copy
        return Plateau(grille=[colonne.copy() for colonne in self.grille], colonnes=self.colonnes, lignes=self.lignes, colonnes_jouables=self.colonnes_jouables.copy(), hauteurs_colonnes=self.hauteurs_colonnes.copy())

    def afficher(self):
        for ligne in range(self.lignes - 1, -1, -1):
            for colonne in range(self.colonnes):
                if ligne < self.hauteurs_colonnes[colonne]:
                    print(self.grille[colonne][ligne], end=" ")
                else:
                    print(".", end=" ")
            print()

    def colonne_valide(self, colonne):
        return 0 <= colonne < self.colonnes

    def ajouter_jeton(self, colonne, symbole):
        if colonne not in self.colonnes_jouables:
            return False

        self.grille[colonne].append(symbole)
        self.hauteurs_colonnes[colonne] += 1

        if self.colonne_pleine(colonne):
            self.colonnes_jouables.remove(colonne)

        return True

    def colonne_pleine(self, colonne):
        return self.hauteurs_colonnes[colonne] >= self.lignes

    def est_nul(self):
        return len(self.colonnes_jouables) == 0


    def est_victoire(self, colonne):
        jeton = self.grille[colonne][-1]
        ligne = self.hauteurs_colonnes[colonne] - 1
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        for dx, dy in directions:
            compte = 1
            x, y = colonne, ligne
            while True:
                x += dx
                y += dy
                if 0 <= x < self.colonnes and 0 <= y < self.hauteurs_colonnes[x] and self.grille[x][y] == jeton:
                    compte += 1
                else:
                    break
            x, y = colonne, ligne
            while True:
                x -= dx
                y -= dy
                if 0 <= x < self.colonnes and 0 <= y < self.hauteurs_colonnes[x] and self.grille[x][y] == jeton:
                    compte += 1
                else:
                    break
            if compte >= 4:
                return True
        return False

    def jouer_coup_reversible(self, colonne, symbole):
        self.grille[colonne].append(symbole)
        self.hauteurs_colonnes[colonne] += 1

        colonne_est_enlevée = False
        if self.colonne_pleine(colonne) and colonne in self.colonnes_jouables:
            self.colonnes_jouables.remove(colonne)
            colonne_est_enlevée = True
        return colonne_est_enlevée

    def annuler_coup(self, colonne, colonne_est_enlevée, symbole):
        self.grille[colonne].pop()
        self.hauteurs_colonnes[colonne] -= 1

        if colonne_est_enlevée:
            self.colonnes_jouables.add(colonne)


