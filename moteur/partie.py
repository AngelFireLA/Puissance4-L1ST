import moteur.plateau as plateau
class Partie:
    def __init__(self, colonnes=7, lignes=6, joueur1=None, joueur2=None): self.plateau, self.joueur1, self.joueur2, self.tour_joueur = plateau.Plateau(colonnes, lignes), joueur1, joueur2, 1
    def jouer(self, colonne, num_joueur): return self.plateau.ajouter_jeton(colonne, self.joueur1.symbole if num_joueur == 1 else self.joueur2.symbole)