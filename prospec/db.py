import sqlite3
from datetime import datetime, timedelta

from .config import DATA_DIR, DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS companies (
    siren TEXT PRIMARY KEY,
    nom TEXT, commune TEXT, code_postal TEXT, naf TEXT, metier TEXT,
    dirigeant TEXT, effectif TEXT,
    site_url TEXT, site_status TEXT,   -- none | ok | outdated | unknown
    site_issues TEXT,
    email TEXT,
    status TEXT DEFAULT 'new',         -- new | qualified | no_email | drafted | sent | followed_up | replied | refused | skip
    subject TEXT, body TEXT,
    contacted_at TEXT, followup_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS suppression (email TEXT PRIMARY KEY, added_at TEXT DEFAULT CURRENT_TIMESTAMP);
"""


def connect(path=None):
    DATA_DIR.mkdir(exist_ok=True)
    con = sqlite3.connect(path or DB_PATH)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    con.execute("UPDATE companies SET status='no_email' WHERE status='to_call'")
    con.commit()
    return con


def now():
    return datetime.now().isoformat(timespec="seconds")


def is_suppressed(con, email):
    if not email:
        return False
    email = email.lower()
    domain = email.split("@")[-1]
    row = con.execute(
        "SELECT 1 FROM suppression WHERE email = ? OR email = ?", (email, "@" + domain)
    ).fetchone()
    return row is not None


def suppress(con, email):
    con.execute("INSERT OR IGNORE INTO suppression(email) VALUES (?)", (email.lower(),))
    con.execute("UPDATE companies SET status='refused' WHERE lower(email)=?", (email.lower(),))
    con.commit()


def due_followups(con, days):
    limit = (datetime.now() - timedelta(days=days)).isoformat(timespec="seconds")
    return con.execute(
        "SELECT * FROM companies WHERE status='sent' AND contacted_at <= ? AND followup_at IS NULL",
        (limit,),
    ).fetchall()


def get_setting(con, key, default=""):
    row = con.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default


def set_setting(con, key, value):
    con.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))
    con.commit()


def send_mode(con):
    """review (valider dans le dashboard) | draft (brouillons Gmail) | send (envoi direct)"""
    from .config import env
    return get_setting(con, "send_mode", env("SEND_MODE", "review"))
