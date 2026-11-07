"""Persistência dos itens do catálogo (filmes e jogos) em SQLite."""
from decimal import Decimal

from app.models.filme import Filme
from app.models.jogo import Jogo
from app.models.validacao import CENTAVO

_INT64_MAX = 2**63 - 1


def _id_valido(id):
    # IDs fora do intervalo do SQLite não existem; evita OverflowError (HTTP 500).
    return isinstance(id, int) and 0 < id <= _INT64_MAX


class CatalogoRepository:
    """CRUD genérico. As subclasses definem tabela, campo de categoria e modelo."""
    tabela = None
    campo = None   # 'genero' (filmes) ou 'plataforma' (jogos)
    modelo = None

    def __init__(self, database):
        self._db = database

    def _para_item(self, row):
        return self.modelo(id=row['id'], titulo=row['titulo'], **{self.campo: row[self.campo]},
                           valor_diaria=Decimal(str(row['valor_diaria'])).quantize(CENTAVO))

    def listar(self):
        with self._db.connection() as db:
            return [self._para_item(r) for r in db.execute(f'SELECT * FROM {self.tabela} ORDER BY id DESC')]

    def obter(self, id):
        if not _id_valido(id):
            return None
        with self._db.connection() as db:
            row = db.execute(f'SELECT * FROM {self.tabela} WHERE id = ?', (id,)).fetchone()
        return self._para_item(row) if row else None

    def criar(self, titulo, categoria, valor_diaria):
        with self._db.connection() as db:
            cur = db.execute(f'INSERT INTO {self.tabela}(titulo, {self.campo}, valor_diaria) VALUES (?, ?, ?)',
                             (titulo, categoria, float(valor_diaria)))
            return cur.lastrowid

    def atualizar(self, id, titulo, categoria, valor_diaria):
        if not _id_valido(id):
            return False
        with self._db.connection() as db:
            cur = db.execute(f'UPDATE {self.tabela} SET titulo = ?, {self.campo} = ?, valor_diaria = ? '
                             'WHERE id = ?', (titulo, categoria, float(valor_diaria), id))
            return cur.rowcount > 0

    def excluir(self, id):
        if not _id_valido(id):
            return False
        with self._db.connection() as db:
            return db.execute(f'DELETE FROM {self.tabela} WHERE id = ?', (id,)).rowcount > 0


class FilmesRepository(CatalogoRepository):
    tabela, campo, modelo = 'filmes', 'genero', Filme


class JogosRepository(CatalogoRepository):
    tabela, campo, modelo = 'jogos', 'plataforma', Jogo
