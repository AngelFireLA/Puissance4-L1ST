import ipaddress
import os

import pygame
import json
def souris_est_dans_zone(souris, zone):
    x, y, largeur, hauteur = zone
    return x < souris[0] < x + largeur and y < souris[1] < y + hauteur

def afficher_texte(fenetre, x, y, texte, taille, couleur=(0, 0, 0), font="freesansbold.ttf"):
    font = pygame.font.Font(font, taille)
    texte = font.render(texte, True, couleur)
    text_rect = texte.get_rect(center=(x, y))
    fenetre.blit(texte, text_rect)

def charger_config():
    with open(chemin_absolu_dossier+"config.json", "r") as fichier:
        return json.load(fichier)

def récupérer_port():
    return charger_config()["port"]

def récupérer_ip_cible():
    return charger_config()["ip"]

def mettre_à_jour_ip(nouvelle_ip):
    config = charger_config()
    config["ip"] = nouvelle_ip
    with open(chemin_absolu_dossier+"config.json", "w") as fichier:
        json.dump(config, fichier)

def est_local():
    return charger_config()["local"]

def mettre_à_jour_port(nouveau_port):
    config = charger_config()
    config["port"] = nouveau_port
    with open(chemin_absolu_dossier+"config.json", "w") as fichier:
        json.dump(config, fichier)

def ip_est_valide(ip):
    try:
        ipaddress.IPv4Address(ip)
        return True
    except ValueError:
        return False

#liste de couleurs nom:rgb
dict_couleurs = {
    "rouge": (255, 0, 0),
    "vert": (0, 255, 0),
    "bleu": (0, 0, 255),
    "jaune": (255, 255, 0),
    "noir": (0, 0, 0),
    "blanc": (255, 255, 255),
    "gris": (128, 128, 128),
    "marron": (139, 69, 19),
    "rose": (255, 105, 180),
    "violet": (128, 0, 128),
    "cyan": (0, 255, 255),
    "orange": (255, 165, 0),
    "bleu marin": (20, 40, 70),
    "bleu boutton": (100, 150, 255)
}

largeur_fenetre, hauteur_fenetre = 800, 600
couleurs_jetons = {'X': (255, 150, 200), 'O': (80, 140, 230)}
couleur_plateau = (160, 170, 190)
serveur_tourne = False

def status_serveur(status=None):
    global serveur_tourne
    if status is None:
        return serveur_tourne
    serveur_tourne = status


chemin_absolu_dossier = os.path.dirname(os.path.abspath(__file__)) + "/"
