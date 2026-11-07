"""Acesso ao SQLite compartilhado por usuários (Portal) e filmes (Banco)."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT NOT NULL,           -- hash PBKDF2, nunca texto puro
    role     TEXT NOT NULL DEFAULT 'cliente',   -- 'admin' | 'cliente'
    nome     TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS filmes (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo       TEXT NOT NULL,
    genero       TEXT NOT NULL,
    valor_diaria REAL NOT NULL CHECK (valor_diaria >= 0)
);
CREATE TABLE IF NOT EXISTS jogos (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo       TEXT NOT NULL,
    plataforma   TEXT NOT NULL,
    valor_diaria REAL NOT NULL CHECK (valor_diaria >= 0)
);
CREATE TABLE IF NOT EXISTS locacoes (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    username       TEXT NOT NULL,
    tipo           TEXT NOT NULL CHECK (tipo IN ('filme', 'jogo')),
    item_id        INTEGER NOT NULL,
    titulo         TEXT NOT NULL,      -- cópia do título/preço no momento da locação
    valor_diaria   REAL NOT NULL,
    dias           INTEGER NOT NULL CHECK (dias > 0),
    valor_total    REAL NOT NULL,
    data_locacao   TEXT NOT NULL,
    data_prevista  TEXT NOT NULL,
    data_devolucao TEXT,
    multa          REAL
);
-- Um item só pode ter uma locação em aberto por vez.
CREATE UNIQUE INDEX IF NOT EXISTS ux_locacao_item_aberta
    ON locacoes (tipo, item_id) WHERE data_devolucao IS NULL;
CREATE INDEX IF NOT EXISTS ix_locacoes_username ON locacoes (username);
"""


class Database:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.executescript(SCHEMA)
            self._migrar(db)

    @staticmethod
    def _migrar(db):
        """Atualiza bancos criados por versões anteriores (sem perfil de usuário)."""
        colunas = {r['name'] for r in db.execute('PRAGMA table_info(users)')}
        if 'role' not in colunas:
            db.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'cliente'")
        if 'nome' not in colunas:
            db.execute("ALTER TABLE users ADD COLUMN nome TEXT NOT NULL DEFAULT ''")

    @contextmanager
    def connection(self):
        """Abre uma conexão, confirma (commit) ao final e SEMPRE a fecha.

        (``with sqlite3.connect()`` apenas confirma a transação; não fecha a conexão.)
        """
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def ping(self):
        with self.connection() as db:
            db.execute('SELECT 1').fetchone()
