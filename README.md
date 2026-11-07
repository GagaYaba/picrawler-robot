# picrawler-robot

Programmes liés au robot SunFounder PiCrawler (Raspberry Pi 4) : outils côté PC pour le piloter,
et plus tard le code qui tourne sur le Pi. Ce dépôt est un sous-module de `picrawler-control`.

## Outils WiFi (`tools/wifi/`)

| Fichier | Rôle |
|---|---|
| `wifi_check.py` | Compare le WiFi du PC et celui du robot, en lecture seule. `--tutorial` affiche la procédure d'ajout d'un nouveau réseau. |
| `wifi_widget.py` | Fenêtre (Tkinter) en lecture seule : WiFi du PC, WiFi du robot, réseaux connus du robot, et un écran tutoriel avec les commandes à copier. |
| `wifi_tutorial.py` | Texte de la procédure, partagé par la fenêtre et la ligne de commande. |
| `picrawler_ssh.py` | Lance la connexion SSH et signale d'abord si le robot ne connaît pas le WiFi du PC. |

Prérequis : Python 3 (Tkinter inclus), client SSH avec une clé configurée pour `pi`, NetworkManager sur le Pi.

```
cd tools/wifi
python wifi_widget.py --host picrawler.local
```

Les outils n'écrivent rien sur le robot et ne demandent aucun mot de passe. L'ajout d'un réseau se fait à la main, en suivant le tutoriel : partage de connexion du téléphone, session SSH, enregistrement du profil avec saisie du mot de passe sans affichage, bascule avec retour automatique.

Limites : le PC et le robot doivent être sur le même réseau. Les WiFi avec identifiant personnel (WPA-Enterprise) ou portail de connexion ne sont pas couverts.

## Tests

```
python -m unittest discover -s tests
```

Les tests couvrent la lecture des sorties `netsh` et `nmcli`, le verdict de comparaison et le contenu du tutoriel (aucun secret dans les commandes). L'interface et la lecture sur le robot réel ont été vérifiées à la main.
