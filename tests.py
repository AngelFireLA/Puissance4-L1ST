import random

import moteur.plateau as plateau
import time


def temps_pour_x_coups_sans_victoire(PlateauClass, iterations=1000):
    start = time.perf_counter()

    for _ in range(iterations):
        plateau = PlateauClass()
        colonne = 0
        while not plateau.est_nul():
            plateau.ajouter_jeton(colonne, "X")
            colonne = (colonne + 1) % plateau.colonnes

    end = time.perf_counter()
    return end - start

def temps_pour_x_coups_avec_victoire(PlateauClass, iterations=1000):
    start = time.perf_counter()

    for _ in range(iterations):
        plateau = PlateauClass()
        colonne = 0
        while not plateau.est_nul():
            plateau.ajouter_jeton(colonne, "X")
            plateau.est_victoire(colonne)
            colonne = (colonne + 1) % plateau.colonnes


    end = time.perf_counter()
    return end - start


def coups_en_x_secondes_sans_victoire(PlateauClass, duration=0.1):
    start = time.perf_counter()
    moves = 0
    plateau = PlateauClass()

    while time.perf_counter() - start < duration:
        colonne = moves % plateau.colonnes
        if not plateau.ajouter_jeton(colonne, "X"):
            plateau = PlateauClass()
        moves += 1

    return moves

def coups_en_x_secondes_avec_victoire(PlateauClass, duration=0.1):
    start = time.perf_counter()
    moves = 0
    plateau = PlateauClass()

    while time.perf_counter() - start < duration:
        colonne = moves % plateau.colonnes
        if not plateau.ajouter_jeton(colonne, "X"):
            plateau = PlateauClass()
        else:
            plateau.est_victoire(colonne)
        moves += 1

    return moves


# # Nombre de Coups en X secondes sans vérification de victoire
# durées = [0.1, 1, 10]
# for durée in durées:
#     print(f"\nTest du nombre de coups en {durée} seconde :")
#     coups_par_seconde = coups_en_x_secondes_sans_victoire(plateau.Plateau, duration=durée)
#     print(f"Version Actuelle : {coups_par_seconde} coups/s")



# # Temps pour faire X coups sans vérification de victoire
# coups = [1000, 10000, 100000]
# for coup in coups:
#     print(f"\nTemps pour faire {coup} coups :")
#     test_fill = temps_pour_x_coups_sans_victoire(plateau.Plateau, iterations=coup)
#     print(f"Version Actuelle : {test_fill:.4f} sec")

# Nombre de Coups en X secondes avec vérification de victoire
durées = [0.1, 1, 5]
for durée in durées:
    print(f"\nTest du nombre de coups en {durée} seconde :")
    coups_par_seconde = coups_en_x_secondes_avec_victoire(plateau.Plateau, duration=durée)
    print(f"Version Actuelle : {coups_par_seconde} coups/s")

# Temps pour faire X coups avec vérification de victoire
coups = [1000, 10000, 50000]
for coup in coups:
    print(f"\nTemps pour faire {coup} coups :")
    test_fill = temps_pour_x_coups_avec_victoire(plateau.Plateau, iterations=coup)
    print(f"Version Actuelle : {test_fill:.4f} sec")




# # Test de performance pour la copie de grille
# grid = [[] for _ in range(7)]
# for ligne in grid:
#     for _ in range(random.randint(0, 6)):
#         ligne.append("X")
# iterations = [1, 100, 10000]
# for it in iterations:
#     start = time.perf_counter()
#     for i in range(it):
#         copy1 = [col[:] for col in grid]
#     end = time.perf_counter()
#     print(f"Slicing [:]: {end - start:.8f} sec en {it} itérations")
#
#     start = time.perf_counter()
#     for i in range(it):
#         copy2 = [col.copy() for col in grid]
#     end = time.perf_counter()
#     print(f".copy(): {end - start:.8f} sec en {it} itérations")
