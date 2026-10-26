#!/bin/sh
# Démarrage automatique du dashboard à l'allumage du téléphone (application Termux:Boot) : ./install-boot.sh
DIR="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$HOME/.termux/boot"
cat > "$HOME/.termux/boot/prospec-bat" <<SCRIPT
#!/data/data/com.termux/files/usr/bin/sh
# Lancé par Termux:Boot au démarrage du téléphone
sleep 15  # laisse au téléphone le temps de se connecter
"$DIR/server.sh" start
SCRIPT
chmod +x "$HOME/.termux/boot/prospec-bat"
echo "Démarrage automatique installé ($HOME/.termux/boot/prospec-bat)."
echo
echo "Il reste 3 réglages à faire une seule fois :"
echo " 1. Installer l'application Termux:Boot depuis F-Droid (la même source que Termux)."
echo " 2. Ouvrir Termux:Boot une fois, puis la fermer : c'est ce qui l'active."
echo " 3. Réglages Android > Applications > Termux ET Termux:Boot > Batterie : « Sans restriction »."
echo
echo "Pour le lancer tout de suite sans redémarrer : ./server.sh start"
