import random
import socket
import threading
import time
from ..utils import status_serveur

class Serveur:
    def __init__(self, ip='0.0.0.0', port=25565):
        self.ip = ip
        self.port = port
        self.socket_serveur = None
        self.clients = {}

    def démarre_serveur(self):

        self.socket_serveur = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_serveur.bind((self.ip, self.port))
        self.socket_serveur.listen(2)
        print(f"Serveur Démarré sur {self.ip}:{self.port}, en attente connexion")
        status_serveur(True)
        while len(self.clients) < 2:
            if status_serveur() is False:
                break
            socket_client, ip_client = self.socket_serveur.accept()
            print(f"Connexion reçue de {ip_client}")
            threading.Thread(target=self.gère_client, args=(socket_client,), daemon=True).start()


    def envoyer_message(self, nom_cible, message):
        self.clients[nom_cible].sendall(message.encode('utf-8'))

    def gère_client(self, socket_client):
        try:
            i = 0
            nom_utilisateur = None
            connecté = False
            while True:
                i += 1

                print(f"i: {i}")
                try:
                    data = socket_client.recv(2048).decode('utf-8').strip()
                except ConnectionResetError:
                    break
                if not data:
                    break
                if data.startswith("@connexion:"):
                    nom_utilisateur = data.split(":")[1]
                    if nom_utilisateur in self.clients:
                        break
                    print(f"Joueur {nom_utilisateur} connecté")
                    self.clients[nom_utilisateur] = socket_client
                    connecté = True
                    if len(self.clients) == 2:
                        on_commence = random.choice([True, False])
                        j1_tour = 1 if on_commence else 2
                        j2_tour = 2 if on_commence else 1
                        autre_utilisateur = [client for client in self.clients if client != nom_utilisateur][0]
                        self.envoyer_message(nom_utilisateur, f"@commencer:{j1_tour}|{autre_utilisateur}")
                        self.envoyer_message(autre_utilisateur, f"@commencer:{j2_tour}|{nom_utilisateur}")

                if connecté:
                    print(f"Message reçu de {nom_utilisateur}: {data}")
                    if data.startswith("@jouer:"):
                        colonne = int(data.split(":")[1])
                        for client in self.clients:
                            if client != nom_utilisateur:
                                self.envoyer_message(client, f"@jouer:{colonne}")

        except ConnectionResetError:
            pass
        finally:

            socket_client.close()
            print("Client déconnecté")

    def éteint_serveur(self):
        for client, client_socket in self.clients.items():
            client_socket.close()
        self.socket_serveur.close()
        status_serveur(False)
        print("Serveur éteint")

def éteint_serveur():
    global serveur
    serveur.éteint_serveur()

serveur:Serveur = None


def main(port):
    global serveur
    serveur = Serveur(ip='0.0.0.0', port=port)
    serveur.démarre_serveur()


