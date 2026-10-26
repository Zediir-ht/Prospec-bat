"""Notification sur le téléphone : Termux (application Termux:API) et/ou ntfy.sh (gratuit, NTFY_TOPIC)."""
import shutil
import subprocess

import requests

from . import config


def notify(title, text):
    """Envoie une notification par tous les moyens disponibles. Retourne la liste des canaux utilisés ; n'échoue jamais."""
    used = []
    if shutil.which("termux-notification"):
        try:
            subprocess.run(["termux-notification", "--title", title, "--content", text, "--priority", "high"],
                           timeout=10, check=True, capture_output=True)
            used.append("termux")
        except Exception:
            pass
    topic = config.env("NTFY_TOPIC")
    if topic:
        try:
            requests.post("https://ntfy.sh/", json={"topic": topic, "title": title, "message": text, "priority": 4}, timeout=10).raise_for_status()
            used.append("ntfy")
        except Exception:
            pass
    return used
