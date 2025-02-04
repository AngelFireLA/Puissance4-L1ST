def souris_est_dans_zone(souris, zone):
    x, y, largeur, hauteur = zone
    return x < souris[0] < x + largeur and y < souris[1] < y + hauteur