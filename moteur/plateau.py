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