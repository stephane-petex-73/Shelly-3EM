# Shelly 3EM Reader

Ce projet permet d'interroger un Shelly 3EM Gen1 sur le réseau local et d'afficher les valeurs des entrées A et B. LA version 3 afficher également l'entre C

## Prérequis

- Python 3.10+
- Accès réseau au Shelly 3EM sur 192.168.11.100

## Installation

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
```

## Utilisation

```bash
python shelly_3em_reader.py
```

Par défaut, le script interroge :

- IP : `192.168.11.100`
- Port : `80`

Pour un autre appareil :

```bash
python shelly_3em_reader.py --ip 192.168.11.200 --port 80
```

## Ce qui est affiché

- Entrée A : arrivée ENEDIS
- Entrée B : production solaire

Le script affiche les informations de puissance, tension, courant, total et validité.

## Historique des prompts utilisateur  *Ce programme à été entierement réalisé par un agent IA avec Visual Studio Code*

- "Met en place l'environnement necessaire dans ce répertoire pour ce projet : Ecrit un script Python qui permet de lire les information sur le smart meter Shelly 3EM. Tu accèdes à l'API du shelly à l'adresse IP 192.168.11.100. Le script Python doit permetre d'afficher les valeures lues sur l'entrrée A (connectée à l'arrivé ENEDIS) et les valeures de l'entrée B (correspond à la prodution solaire) lorsque j'execute le programme Python. Toutes les instruction de l'API pour le shelly 3EM se trouves ici : https://shelly-api-docs.shelly.cloud/gen1/#http-dialect. https://shelly-api-docs.shelly.cloud/gen1/#shelly-3em-overview"
- "Modifie le script pour n'afficher que les valeurs des entrées A et B."
- "Enregistre cette version, puis créer une version V2 qui va afficher les informations dans une interface graphique. En bas à droite de la fenètre graphique ajouter un bouton qui permet de rafrechir les données (lorsqu'on clique dessus, le script va faire une requète pour mettre à jour les données) "
- "Ajoute également un encart qui indique si je consomme l'énergie de ENEDIS (soutir) ou si j'injecte le trop d'énergie produite vers ENEDIS (injection)"
- "Ajout une explication en petit qui indique : Si la puissance de l’entrée A est positive → Soutirage ENEDIS. Si la puissance de l’entrée A est négative → Injection vers ENEDIS
- Si elle est nulle → Équilibre"
- "Dans les titres 'Entrée A' et 'Entrée B', indique également ENEDIS ou production solaire"
- "Ajoute un encart à droite qui indique la consommation de la maison en Watt"
- "Il y a 1 erreur, la consommation de la maison équivaut à : entrée A + entrée B"
- "Remplace le bouton 'rafraichir' par un champ qui permet de rentrer les valeurs en seconde pour rafraîchir les données. Valeur de 5 par défaut"
- "Ajoute également l'addresse IP du shelly dans un autre champ. Avec possbilité de modifier l'IP si j'amais le shelly change d'adresse IP"
- "Ajouter un message d'erreur si le chargement des données prend plus de 20 secondes et stoppe le rafraîchissement"
- "Le rafraîchissement doit se faire de manière continue avec la valeur indiquée dans le champ et pas seulement lorsqu'on clique sur OK"
- "Est-il possible de créer un fichier exécutable Shelly3EMViewer.exe"
- "Il y a une erreur dans le rafraîchissement des données. Elle ne fonctionne qu'une fois après avoir cliqué sur OK. Il faut que le process soit continu"
- "Peux-tu copier tous les prompts que j'ai écrit dans le fichier README"

Cette section reprend l'historique des demandes formulées pendant le développement de ce projet pour les version V1 et V2, pour garder une trace des évolutions demandées et validées.

## Lecture des données via l'API du Shelly
Le programme appelle fetch_status() pour aller lire les données du Shelly à chaque rafraîchissement.
Avec cette commande : http://192.168.11.100:80/status le script renvoie le JSON complet du Shelly, avec notamment la liste des compteurs : entrée A; entrée B; entrée C.
Ensuite, le programme récupère les compteurs avec la fonction get_meter_list
Voici un exemple typique de ce que renvoie l’API du Shelly :
{
  "wifi_sta": {
    "connected": true,
    "ssid": "MonRéseau",
    "ip": "192.168.11.100"
  },
  "meters": [
    {
      "power": 1234.5,
      "current": 5.42,
      "voltage": 230.1,
      "total": 45678.9
    },
    {
      "power": -456.7,
      "current": -1.98,
      "voltage": 230.3,
      "total": 12345.6
    },
    {
      "power": 789.1,
      "current": 3.42,
      "voltage": 229.9,
      "total": 9876.5
    }
     ]
}