import sqlite3
from contextlib import contextmanager

SCHEMA = """
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cpf TEXT NOT NULL UNIQUE,
    rua TEXT NOT NULL, numero TEXT NOT NULL, cidade TEXT NOT NULL, uf TEXT NOT NULL,
    ativo INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS funcionarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cpf TEXT NOT NULL UNIQUE,
    cargo TEXT NOT NULL,
    ativo INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS itens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL CHECK (tipo IN ('filme', 'jogo')),
    titulo TEXT NOT NULL,
    ano INTEGER NOT NULL,
    disponivel INTEGER NOT NULL DEFAULT 1,
    genero TEXT, duracao_min INTEGER, lancamento INTEGER,
    plataforma TEXT,
    ativo INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS locacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
    funcionario_id INTEGER NOT NULL REFERENCES funcionarios(id),
    data_locacao TEXT NOT NULL,
    data_devolucao TEXT,
    multa REAL NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS locacao_itens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    locacao_id INTEGER NOT NULL REFERENCES locacoes(id),
    item_id INTEGER NOT NULL REFERENCES itens(id),
    dias INTEGER NOT NULL
);
"""


class Database:
    def __init__(self, caminho="locadora.db"):
        self.conn = sqlite3.connect(caminho)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)
        self._migrar()
        self.conn.commit()

    def _migrar(self):
        # bancos criados antes da exclusão lógica não têm a coluna 'ativo'
        for tabela in ("clientes", "funcionarios", "itens"):
            colunas = [r["name"] for r in self.conn.execute(f"PRAGMA table_info({tabela})")]
            if "ativo" not in colunas:
                self.conn.execute(f"ALTER TABLE {tabela} ADD COLUMN ativo INTEGER NOT NULL DEFAULT 1")

    @contextmanager
    def transacao(self):
        try:
            yield self.conn
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def fechar(self):
        self.conn.close()
