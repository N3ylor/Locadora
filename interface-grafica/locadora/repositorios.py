import sqlite3
from datetime import date

from .excecoes import RegraNegocioError
from .models import Cliente, Filme, Funcionario, Jogo, Locacao
from .models.locacao import ItemLocacao


class ClienteRepositorio:
    def __init__(self, db):
        self.db = db

    @staticmethod
    def _de_linha(r):
        return Cliente(r["nome"], r["cpf"], r["rua"], r["numero"], r["cidade"], r["uf"], id=r["id"])

    def adicionar(self, c):
        try:
            cur = self.db.conn.execute(
                "INSERT INTO clientes (nome, cpf, rua, numero, cidade, uf) VALUES (?,?,?,?,?,?)",
                (c.nome, c.cpf, c.endereco.rua, c.endereco.numero, c.endereco.cidade, c.endereco.uf))
        except sqlite3.IntegrityError:
            raise RegraNegocioError("Já existe um cliente com esse CPF.")
        c.id = cur.lastrowid
        return c

    def buscar(self, id):
        r = self.db.conn.execute("SELECT * FROM clientes WHERE id=?", (id,)).fetchone()
        return self._de_linha(r) if r else None

    def listar(self):
        return [self._de_linha(r) for r in self.db.conn.execute("SELECT * FROM clientes ORDER BY nome")]

    def atualizar(self, c):
        try:
            cur = self.db.conn.execute(
                "UPDATE clientes SET nome=?, cpf=?, rua=?, numero=?, cidade=?, uf=? WHERE id=?",
                (c.nome, c.cpf, c.endereco.rua, c.endereco.numero, c.endereco.cidade, c.endereco.uf, c.id))
        except sqlite3.IntegrityError:
            raise RegraNegocioError("Já existe um cliente com esse CPF.")
        return cur.rowcount > 0

    def remover(self, id):
        try:
            cur = self.db.conn.execute("DELETE FROM clientes WHERE id=?", (id,))
        except sqlite3.IntegrityError:
            raise RegraNegocioError("Cliente possui locações registradas e não pode ser removido.")
        return cur.rowcount > 0


class FuncionarioRepositorio:
    def __init__(self, db):
        self.db = db

    @staticmethod
    def _de_linha(r):
        return Funcionario(r["nome"], r["cpf"], r["cargo"], id=r["id"])

    def adicionar(self, f):
        try:
            cur = self.db.conn.execute(
                "INSERT INTO funcionarios (nome, cpf, cargo) VALUES (?,?,?)", (f.nome, f.cpf, f.cargo))
        except sqlite3.IntegrityError:
            raise RegraNegocioError("Já existe um funcionário com esse CPF.")
        f.id = cur.lastrowid
        return f

    def buscar(self, id):
        r = self.db.conn.execute("SELECT * FROM funcionarios WHERE id=?", (id,)).fetchone()
        return self._de_linha(r) if r else None

    def listar(self):
        return [self._de_linha(r) for r in self.db.conn.execute("SELECT * FROM funcionarios ORDER BY nome")]

    def atualizar(self, f):
        try:
            cur = self.db.conn.execute(
                "UPDATE funcionarios SET nome=?, cpf=?, cargo=? WHERE id=?", (f.nome, f.cpf, f.cargo, f.id))
        except sqlite3.IntegrityError:
            raise RegraNegocioError("Já existe um funcionário com esse CPF.")
        return cur.rowcount > 0

    def remover(self, id):
        try:
            cur = self.db.conn.execute("DELETE FROM funcionarios WHERE id=?", (id,))
        except sqlite3.IntegrityError:
            raise RegraNegocioError("Funcionário possui locações registradas e não pode ser removido.")
        return cur.rowcount > 0


class ItemRepositorio:
    def __init__(self, db):
        self.db = db

    @staticmethod
    def _de_linha(r):
        disp = bool(r["disponivel"])
        if r["tipo"] == Filme.TIPO:
            return Filme(r["titulo"], r["ano"], r["genero"], r["duracao_min"],
                         bool(r["lancamento"]), disp, id=r["id"])
        return Jogo(r["titulo"], r["ano"], r["plataforma"], disp, id=r["id"])

    @staticmethod
    def _valores(item):
        if isinstance(item, Filme):
            return (item.TIPO, item.titulo, item.ano, int(item.disponivel),
                    item.genero, item.duracao_min, int(item.lancamento), None)
        return (item.TIPO, item.titulo, item.ano, int(item.disponivel), None, None, None, item.plataforma)

    def adicionar(self, item):
        cur = self.db.conn.execute(
            "INSERT INTO itens (tipo, titulo, ano, disponivel, genero, duracao_min, lancamento, plataforma) "
            "VALUES (?,?,?,?,?,?,?,?)", self._valores(item))
        item.id = cur.lastrowid
        return item

    def buscar(self, id):
        r = self.db.conn.execute("SELECT * FROM itens WHERE id=?", (id,)).fetchone()
        return self._de_linha(r) if r else None

    def listar(self, apenas_disponiveis=False):
        sql = "SELECT * FROM itens" + (" WHERE disponivel=1" if apenas_disponiveis else "") + " ORDER BY titulo"
        return [self._de_linha(r) for r in self.db.conn.execute(sql)]

    def atualizar(self, item):
        cur = self.db.conn.execute(
            "UPDATE itens SET tipo=?, titulo=?, ano=?, disponivel=?, genero=?, duracao_min=?, "
            "lancamento=?, plataforma=? WHERE id=?", self._valores(item) + (item.id,))
        return cur.rowcount > 0

    def atualizar_disponibilidade(self, item):
        self.db.conn.execute("UPDATE itens SET disponivel=? WHERE id=?", (int(item.disponivel), item.id))

    def remover(self, id):
        try:
            cur = self.db.conn.execute("DELETE FROM itens WHERE id=?", (id,))
        except sqlite3.IntegrityError:
            raise RegraNegocioError("Item possui locações registradas e não pode ser removido.")
        return cur.rowcount > 0


class LocacaoRepositorio:
    def __init__(self, db, clientes, funcionarios, itens):
        self.db = db
        self.clientes = clientes
        self.funcionarios = funcionarios
        self.itens = itens

    def adicionar(self, loc):
        cur = self.db.conn.execute(
            "INSERT INTO locacoes (cliente_id, funcionario_id, data_locacao) VALUES (?,?,?)",
            (loc.cliente.id, loc.funcionario.id, loc.data_locacao.isoformat()))
        loc.id = cur.lastrowid
        for il in loc.itens:
            self.db.conn.execute("INSERT INTO locacao_itens (locacao_id, item_id, dias) VALUES (?,?,?)",
                                 (loc.id, il.item.id, il.dias))
        return loc

    def salvar_devolucao(self, loc):
        self.db.conn.execute("UPDATE locacoes SET data_devolucao=?, multa=? WHERE id=?",
                             (loc.data_devolucao.isoformat(), loc.multa, loc.id))

    def _de_linha(self, r):
        loc = Locacao(self.clientes.buscar(r["cliente_id"]), self.funcionarios.buscar(r["funcionario_id"]),
                      date.fromisoformat(r["data_locacao"]), id=r["id"])
        if r["data_devolucao"]:
            loc.data_devolucao = date.fromisoformat(r["data_devolucao"])
        loc.multa = r["multa"]
        linhas = self.db.conn.execute("SELECT item_id, dias FROM locacao_itens WHERE locacao_id=? ORDER BY id",
                                      (loc.id,)).fetchall()
        for li in linhas:
            loc.itens.append(ItemLocacao(self.itens.buscar(li["item_id"]), li["dias"], loc.data_locacao))
        return loc

    def buscar(self, id):
        r = self.db.conn.execute("SELECT * FROM locacoes WHERE id=?", (id,)).fetchone()
        return self._de_linha(r) if r else None

    def listar(self, apenas_abertas=False):
        sql = "SELECT * FROM locacoes" + (" WHERE data_devolucao IS NULL" if apenas_abertas else "") + " ORDER BY id"
        return [self._de_linha(r) for r in self.db.conn.execute(sql).fetchall()]

    def contar_itens_abertos(self, cliente_id):
        return self.db.conn.execute(
            "SELECT COUNT(*) FROM locacao_itens li JOIN locacoes l ON l.id = li.locacao_id "
            "WHERE l.cliente_id=? AND l.data_devolucao IS NULL", (cliente_id,)).fetchone()[0]
