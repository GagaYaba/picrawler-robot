# picrawler-robot

Programmes liés au robot SunFounder PiCrawler (Raspberry Pi 4) : outils côté PC pour le piloter,
et plus tard le code qui tourne sur le Pi. Ce dépôt est un sous-module de `picrawler-control`.

## Outils WiFi (`tools/wifi/`)

| Fichier | Rôle |
|---|---|
| `wifi_check.py` | Compare le WiFi du PC et celui du robot, en lecture seule. `--add-help NOM` affiche la commande d'ajout sans l'exécuter. |
| `wifi_widget.py` | Fenêtre (Tkinter) pour voir les réseaux connus du robot et en ajouter un. N'écrit sur le Pi qu'après validation et confirmation. |
| `picrawler_ssh.py` | Lance la connexion SSH, en ouvrant d'abord la fenêtre si le robot ne connaît pas le WiFi du PC. |

Prérequis : Python 3 (Tkinter inclus), client SSH avec une clé configurée pour `pi`, NetworkManager sur le Pi.

```
cd tools/wifi
python wifi_widget.py --host picrawler.local
```

Le mot de passe WiFi n'est ni affiché ni enregistré sur le PC : il est envoyé au Pi par l'entrée standard de SSH.

## Tests

```
python -m unittest discover -s tests
```

Les tests couvrent la lecture des sorties `netsh` et `nmcli`. L'écriture sur le Pi et l'interface n'ont été vérifiées qu'à la main.
