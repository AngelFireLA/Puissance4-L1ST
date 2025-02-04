import pygame
from utils import souris_est_dans_zone, dict_couleurs

class Boutton:
    def __init__(self, x, y, largeur, hauteur, texte, couleur, couleur_surlignée=None,font="freesansbold.ttf", amplitude_arrondi=1.5, montrer=True, couleur_texte=None):
        self.hauteur = hauteur
        self.largeur = largeur
        self.ratio = min(largeur/hauteur, hauteur/largeur)
        self.x, self.y = x, y
        self.rect = None
        self.génère_rect()
        self.texte = texte
        self.couleur = couleur
        self.font = self.génère_font(font)
        self.amplitude_arrondi = amplitude_arrondi
        self.montrer = montrer
        if not couleur_surlignée:
            self.couleur_surlignée = (min(255, int(couleur[0]*1.2)), min(255, int(couleur[1]*1.2)), min(255, int(couleur[2]*1.2)))
        else:
            self.couleur_surlignée = couleur_surlignée
        self.couleur_texte = couleur_texte if couleur_texte else dict_couleurs["bleu marin"]
    def génère_rect(self):
        self.rect = pygame.Rect(0, 0, self.largeur, self.hauteur)
        self.rect.center = (self.x, self.y)

    def génère_font(self, font):
        # maximise la taille du texte pour qu'il puisse rentrer en hauteur et largeur
        taille = 1
        self.font = pygame.font.Font(font, taille)
        while self.font.size(self.texte)[1] < self.hauteur - int(self.hauteur/4) and self.font.size(self.texte)[0] < self.largeur - int(self.largeur/6):
            taille += 1
            self.font = pygame.font.Font(font, taille)
        return pygame.font.Font(font, taille)

    def boutton_clické(self, event) -> bool:
        if self.rect.collidepoint(event.pos) and self.montrer:
            return True
        return False

    def afficher(self, screen):
        if self.montrer:
            couleur = self.couleur
            if souris_est_dans_zone(pygame.mouse.get_pos(), self.rect):
                couleur = self.couleur_surlignée
            pygame.draw.rect(screen, couleur, self.rect, border_radius=int((self.ratio*40)**self.amplitude_arrondi))
            pygame.draw.rect(screen, (0, 0, 0), self.rect, 2, border_radius=int((self.ratio*40)**self.amplitude_arrondi))

            texte = self.font.render(self.texte, True, self.couleur_texte)
            text_rect = texte.get_rect(center=self.rect.center)
            screen.blit(texte, text_rect)
