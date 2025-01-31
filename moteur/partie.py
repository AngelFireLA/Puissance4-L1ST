import moteur.plateau as plateau
from moteur.joueur import Joueur
class Partie:

    def __init__(self, colonnes=7, lignes=6):
        self.plateau = plateau.Plateau(colonnes, lignes)
        self.joueur1 = None
        self.joueur2 = None
        self.tour = 0
        self.historique_des_coups = []
        self.tour_joueur = 1

    def ajouter_joueur(self, joueur):
        if not self.joueur1:
            self.joueur1 = joueur
        elif not self.joueur2:
            self.joueur2 = joueur
        else:
            raise ValueError("La partie est déjà pleine")

    def jouer(self, colonne, num_joueur):
        if num_joueur != self.tour_joueur:
            print("Ce n'est pas votre tour")
            return
        if num_joueur == 1:
            symbole = self.joueur1.symbole
        elif num_joueur == 2:
            symbole = self.joueur2.symbole

        else:
            raise ValueError("Joueur inconnu")

        self.tour += 1
        self.historique_des_coups.append((colonne, num_joueur))
        return self.plateau.ajouter_jeton(colonne, symbole)

    def partie_textuelle(self):
        self.plateau.afficher()
        while True:
            colonne = int(input(f"Entrez le numéro de colonne Joueur {self.tour_joueur}: "))
            if self.jouer(colonne-1, self.tour_joueur) is True:
                if self.tour_joueur == 1:
                    self.tour_joueur = 2
                else:
                    self.tour_joueur = 1
                self.plateau.afficher()
                if self.plateau.est_nul():
                    print("Match nul")
                    break
                if self.plateau.est_victoire(colonne-1):
                    print(f"Le joueur {self.tour_joueur} a gagné")
                    break

# partie = Partie()
# joueur1 = Joueur("Joueur 1", "X")
# joueur2 = Joueur("Joueur 2", "O")
# partie.ajouter_joueur(joueur1)
# partie.ajouter_joueur(joueur2)
# partie.partie_textuelle()