class Plateau:
    def __init__(self, colonnes=7, lignes=6):
        self.colonnes = colonnes
        self.lignes = lignes
        self.grille = self.construire_grille()
        self.colonnes_jouables = set(range(self.colonnes))

    def construire_grille(self):
        return [[] for _ in range(self.colonnes)]

    def copier_grille(self):
        #without using colonne.copy
        return [colonne.copy() for colonne in self.grille]

    def afficher(self):
        for ligne in range(self.lignes - 1, -1, -1):
            for colonne in range(self.colonnes):
                if ligne < len(self.grille[colonne]):
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

        if self.colonne_pleine(colonne):
            self.colonnes_jouables.remove(colonne)

        return True

    def colonne_pleine(self, colonne):
        if not self.colonne_valide(colonne):
            raise IndexError("Colonne invalide")
        return len(self.grille[colonne]) >= self.lignes

    def est_nul(self):
        return len(self.colonnes_jouables) == 0

    def est_victoire(self, colonne):
        """
        Checks if the newly placed token at the top of 'colonne'
        creates a winning condition (4 in a row).
        """
        # Row of the newly placed token
        row = len(self.grille[colonne]) - 1
        if row < 0:
            # No token in this column, can't be a win
            return False

        jeton = self.grille[colonne][row]

        # Only 4 directions to check because we expand both ways
        directions = [
            (1, 0),  # Horizontal
            (0, 1),  # Vertical
            (1, 1),  # Diagonal down-right / up-left
            (1, -1),  # Diagonal up-right / down-left
        ]

        for dx, dy in directions:
            # Start with count = 1 for the newly placed token
            count = 1

            # 1) Check "forward" direction
            x, y = colonne + dx, row + dy
            while (0 <= x < self.colonnes) and (0 <= y < len(self.grille[x])):
                if self.grille[x][y] == jeton:
                    count += 1
                    x += dx
                    y += dy
                else:
                    break

            # 2) Check "backward" direction
            x, y = colonne - dx, row - dy
            while (0 <= x < self.colonnes) and (0 <= y < len(self.grille[x])):
                if self.grille[x][y] == jeton:
                    count += 1
                    x -= dx
                    y -= dy
                else:
                    break

            # Win if 4 or more in a row
            if count >= 4:
                return True

        return False

