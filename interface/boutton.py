import pygame
from utils import souris_est_dans_zone

class Boutton:
    def __init__(self, x, y, largeur, hauteur, texte, couleur, font="freesansbold.ttf", amplitude_arrondi=1.5):
        self.hauteur = hauteur
        self.largeur = largeur
        self.ratio = min(largeur/hauteur, hauteur/largeur)
        self.rect = pygame.Rect(x, y, largeur, hauteur)
        self.rect.center = (x, y)
        self.texte = texte
        self.couleur = couleur
        self.font = self.génère_font(font)
        self.amplitude_arrondi = amplitude_arrondi

    def génère_font(self, font):
        # maximise la taille du texte pour qu'il puisse rentrer en hauteur et largeur
        taille = 1
        self.font = pygame.font.Font(font, taille)
        while self.font.size(self.texte)[1] < self.hauteur - int(self.hauteur/4) and self.font.size(self.texte)[0] < self.largeur - int(self.largeur/6):
            taille += 1
            self.font = pygame.font.Font(font, taille)
        return pygame.font.Font(font, taille)

    def afficher(self, screen):
        couleur = self.couleur
        if souris_est_dans_zone(pygame.mouse.get_pos(), self.rect):
            couleur = (self.couleur[0] - 50, self.couleur[1] - 50, self.couleur[2] - 50)
        pygame.draw.rect(screen, couleur, self.rect, border_radius=int((self.ratio*40)**self.amplitude_arrondi))
        pygame.draw.rect(screen, (0, 0, 0), self.rect, 2, border_radius=int((self.ratio*40)**self.amplitude_arrondi))

        texte = self.font.render(self.texte, True, (0, 0, 0))
        text_rect = texte.get_rect(center=self.rect.center)
        screen.blit(texte, text_rect)
