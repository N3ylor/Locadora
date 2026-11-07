"""Persistência das locações em SQLite."""
import sqlite3
from datetime import date
from decimal import Decimal

from app.controllers.filmes_repository import _id_valido
from app.models.locacao import Locacao
from app.models.validacao import CENTAVO


class LimiteExcedido(Exception):
    """O cliente já está com o máximo de itens alugados."""


class ItemIndisponivel(Exception):
    """O item já está alugado por alguém."""


def _dec(valor):
    return None if valor is None else Decimal(str(valor)).quantize(CENTAVO)


def _para_locacao(row):
    return Locacao(
        id=row['id'], username=row['username'], tipo=row['tipo'], item_id=row['item_id'],
        titulo=row['titulo'], valor_diaria=_dec(row['valor_diaria']), dias=row['dias'],
        valor_total=_dec(row['valor_total']),
        data_locacao=date.fromisoformat(row['data_locacao']),
        data_prevista=date.fromisoformat(row['data_prevista']),
        data_devolucao=date.fromisoformat(row['data_devolucao']) if row['data_devolucao'] else None,
        multa=_dec(row['multa']))


class LocacoesRepository:
    def __init__(self, database):
        self._db = database

    def listar(self, username=None):
        sql, args = 'SELECT * FROM locacoes', ()
        if username is not None:
            sql, args = sql + ' WHERE username = ?', (username,)
        with self._db.connection() as db:
            return [_para_locacao(r) for r in db.execute(sql + ' ORDER BY id DESC', args)]

    def obter(self, id):
        if not _id_valido(id):
            return None
        with self._db.connection() as db:
            row = db.execute('SELECT * FROM locacoes WHERE id = ?', (id,)).fetchone()
        return _para_locacao(row) if row else None

    def itens_abertos(self):
        """Conjunto de ``(tipo, item_id)`` atualmente alugados."""
        with self._db.connection() as db:
            rows = db.execute('SELECT tipo, item_id FROM locacoes WHERE data_devolucao IS NULL')
            return {(r['tipo'], r['item_id']) for r in rows}

    def item_alugado(self, tipo, item_id):
        return (tipo, item_id) in self.itens_abertos() if _id_valido(item_id) else False

    def contar_abertas(self, username):
        with self._db.connection() as db:
            return db.execute('SELECT COUNT(*) FROM locacoes WHERE username = ? AND data_devolucao IS NULL',
                              (username,)).fetchone()[0]

    def criar(self, username, tipo, item, dias, valor_total, hoje, prevista, limite):
        """Registra a locação de forma atômica (limite e disponibilidade checados na mesma transação)."""
        try:
            with self._db.connection() as db:
                db.execute('BEGIN IMMEDIATE')  # trava escritas concorrentes até o commit
                abertas = db.execute('SELECT COUNT(*) FROM locacoes WHERE username = ? '
                                     'AND data_devolucao IS NULL', (username,)).fetchone()[0]
                if abertas >= limite:
                    raise LimiteExcedido()
                cur = db.execute(
                    'INSERT INTO locacoes(username, tipo, item_id, titulo, valor_diaria, dias, valor_total, '
                    'data_locacao, data_prevista) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (username, tipo, item.id, item.titulo, float(item.valor_diaria), dias,
                     float(valor_total), hoje.isoformat(), prevista.isoformat()))
                return cur.lastrowid
        except sqlite3.IntegrityError:
            raise ItemIndisponivel()

    def devolver(self, id, data, multa):
        """Marca como devolvida. Retorna False se não existir ou já estiver devolvida."""
        with self._db.connection() as db:
            cur = db.execute('UPDATE locacoes SET data_devolucao = ?, multa = ? '
                             'WHERE id = ? AND data_devolucao IS NULL', (data.isoformat(), float(multa), id))
            return cur.rowcount > 0
