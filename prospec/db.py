import sqlite3
from datetime import datetime, timedelta

from .config import DATA_DIR, DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS companies (
    siren TEXT PRIMARY KEY,
    nom TEXT, enseigne TEXT, commune TEXT, code_postal TEXT, naf TEXT, metier TEXT,
    dirigeant TEXT, effectif TEXT, nature_juridique TEXT,
    site_url TEXT, site_status TEXT,   -- none | ok | outdated | unknown
    site_issues TEXT,
    email TEXT, email_source TEXT,
    status TEXT DEFAULT 'new',         -- new | qualified | no_email | drafted | sent | followed_up | replied | refused | bounced | skip
    subject TEXT, body TEXT,
    contacted_at TEXT, followup_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS osm_places (osm_id TEXT PRIMARY KEY, dept TEXT, name TEXT, email TEXT, website TEXT, city TEXT, postcode TEXT);
CREATE TABLE IF NOT EXISTS discovered (query TEXT PRIMARY KEY, done_at TEXT);
CREATE TABLE IF NOT EXISTS send_log (ts TEXT, siren TEXT, kind TEXT);
CREATE TABLE IF NOT EXISTS inbox_seen (uid TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS sourced (dept TEXT, naf TEXT, PRIMARY KEY (dept, naf));
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS suppression (email TEXT PRIMARY KEY, added_at TEXT DEFAULT CURRENT_TIMESTAMP);
"""


_migrated = set()  # bases déjà mises à jour par ce processus


def migrate(con):
    """Crée et met à jour la structure de la base. Une seule fois par processus et par fichier."""
    con.executescript(SCHEMA)
    for col in ("nature_juridique", "email_source", "enseigne", "message_ids", "reply_at", "reply_snippet",
                "followup_subject", "followup_body", "stage", "notes", "reminder"):  # colonnes ajoutées après la 1re version
        try:
            con.execute(f"ALTER TABLE companies ADD COLUMN {col} TEXT")
        except sqlite3.OperationalError:
            pass
    con.executescript("""
        CREATE INDEX IF NOT EXISTS idx_companies_status ON companies(status);
        CREATE INDEX IF NOT EXISTS idx_companies_email ON companies(lower(email));
        CREATE INDEX IF NOT EXISTS idx_send_log_ts ON send_log(ts);
    """)
    con.execute("UPDATE companies SET status='no_email' WHERE status='to_call'")
    # les entreprises téléchargées avant l'ajout de l'enseigne seront retéléchargées peu à peu pour la compléter
    if not con.execute("SELECT 1 FROM settings WHERE key='sourced_v2'").fetchone():
        con.execute("DELETE FROM sourced")
        con.execute("INSERT INTO settings(key, value) VALUES('sourced_v2', '1')")
    # historique des envois reconstitué depuis les mails déjà envoyés
    if not con.execute("SELECT 1 FROM send_log LIMIT 1").fetchone():
        con.execute("INSERT INTO send_log SELECT contacted_at, siren, 'first' FROM companies WHERE contacted_at IS NOT NULL "
                    "AND status IN ('sent','followed_up','replied','refused','bounced')")
    # avant l'ajout de email_source, toute adresse venait d'une lecture du site de l'entreprise
    con.execute("UPDATE companies SET email_source='site' WHERE email IS NOT NULL AND email_source IS NULL")
    con.commit()


def connect(path=None):
    """Connexion à la base. Mode WAL : une recherche qui écrit en arrière-plan ne bloque plus l'affichage des pages."""
    DATA_DIR.mkdir(exist_ok=True)
    path = str(path or DB_PATH)
    con = sqlite3.connect(path, timeout=15, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA synchronous=NORMAL")
    if path not in _migrated or path == ":memory:":
        if path != ":memory:":
            con.execute("PRAGMA journal_mode=WAL")
        migrate(con)
        _migrated.add(path)
    return con


def suppressed_set(con):
    return {r[0] for r in con.execute("SELECT email FROM suppression")}


def in_suppressed(email, supp):
    """Même règle que is_suppressed, sur une liste déjà chargée (évite une requête par adresse)."""
    if not email:
        return False
    email = email.lower()
    return email in supp or "@" + email.split("@")[-1] in supp


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


def log_send(con, siren, kind="first"):
    """Enregistre un envoi réel (premier mail ou relance) : sert au compteur « envoyés aujourd'hui »."""
    con.execute("INSERT INTO send_log(ts, siren, kind) VALUES (?, ?, ?)", (now(), siren, kind))
    con.commit()


def sent_today(con):
    return con.execute("SELECT COUNT(*) FROM send_log WHERE substr(ts, 1, 10) = date('now', 'localtime')").fetchone()[0]


def first_send_date(con):
    row = con.execute("SELECT MIN(substr(ts, 1, 10)) FROM send_log").fetchone()[0]
    return datetime.fromisoformat(row).date() if row else None
