"""Procedure to register a new WiFi network on the robot, as data.

Shared by the widget (tutorial screen) and the command line (`wifi_check.py --tutorial`).
Nothing here is executed: the commands are only displayed, to be run by hand on the robot.
No secret is written in this file: the WiFi password is typed on the robot, without echo.
"""

SSH_REMOTE_HINT = "ssh pi@picrawler.local"

STEPS = [
    {
        "title": "1. Activer le partage de connexion du téléphone",
        "text": "Connecter le PC à ce partage de connexion. Le robot connaît le profil "
                "hotspot-telephone et s'y connecte seul s'il n'est à portée d'aucun autre réseau connu.",
        "commands": [],
    },
    {
        "title": "2. Vérifier la connexion",
        "text": "Dans ce widget, cliquer sur ↻. Le robot doit afficher le nom du partage de connexion. "
                "S'il est injoignable, attendre une minute puis réessayer.",
        "commands": [],
    },
    {
        "title": "3. Ouvrir une session SSH sur le robot",
        "text": "Si le nom picrawler.local n'est pas reconnu, brancher un écran et un clavier sur le robot, "
                "lancer hostname -I, puis utiliser l'adresse obtenue à la place du nom.",
        "commands": [SSH_REMOTE_HINT],
    },
    {
        "title": "4. Enregistrer le nouveau réseau",
        "text": "Coller les commandes une par une, dans la session SSH. Le mot de passe WiFi est saisi sans "
                "affichage. sudo demande le mot de passe du compte pi. Cette étape ne change pas de réseau : "
                "la connexion en cours ne coupe pas.",
        "commands": [
            'read -r -p "Nom du WiFi : " SSID',
            'read -rs -p "Mot de passe WiFi : " PSK; echo',
            'sudo nmcli connection add type wifi con-name "$SSID" ssid "$SSID" '
            'wifi-sec.key-mgmt wpa-psk wifi-sec.psk "$PSK" connection.autoconnect yes',
            "unset PSK",
            "nmcli -t -f NAME,TYPE connection show | grep wireless",
        ],
    },
    {
        "title": "5. Basculer avec un retour automatique",
        "text": "Remplacer NOM_DU_WIFI par le nom exact du profil créé. Sans le fichier témoin de l'étape 6, "
                "le robot revient seul sur le partage de connexion après 240 secondes. La session SSH "
                "peut se couper : c'est normal.",
        "commands": [
            "sudo nohup bash -c 'nmcli connection up \"NOM_DU_WIFI\"; sleep 240; "
            "[ -e /tmp/picrawler-stay ] || nmcli connection up hotspot-telephone' >/dev/null 2>&1 &",
        ],
    },
    {
        "title": "6. Reconnecter le PC puis confirmer",
        "text": "Connecter le PC au nouveau WiFi, rouvrir une session SSH sur le robot (nom ou adresse de "
                "l'étape 3) puis créer le fichier témoin, dans les 4 minutes, pour annuler le retour automatique.",
        "commands": ["touch /tmp/picrawler-stay"],
    },
    {
        "title": "7. Vérifier",
        "text": "Dans ce widget, cliquer sur ↻ : le WiFi du PC et celui du robot doivent être identiques.",
        "commands": [],
    },
]

LIMITS = (
    "Limites : le PC et le robot doivent être sur le même réseau pour que ce widget les voie. "
    "Un WiFi avec identifiant personnel (WPA-Enterprise) ou avec portail de connexion n'est pas "
    "couvert par cette procédure. Certains réseaux isolent les appareils entre eux."
)


def as_text():
    """Whole procedure as plain text, for the command line."""
    out = []
    for step in STEPS:
        out.append(step["title"])
        out.append("  " + step["text"])
        out.extend("    " + c for c in step["commands"])
        out.append("")
    out.append(LIMITS)
    return "\n".join(out)
