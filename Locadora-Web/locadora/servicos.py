from .excecoes import NaoEncontradoError, RegraNegocioError, ValidacaoError
from .models import Cliente, Filme, Funcionario, Jogo, Locacao, Recibo
from .repositorios import (ClienteRepositorio, FuncionarioRepositorio,
                           ItemRepositorio, LocacaoRepositorio)


class Locadora:
    def __init__(self, db):
        self.db = db
        self.clientes = ClienteRepositorio(db)
        self.funcionarios = FuncionarioRepositorio(db)
        self.itens = ItemRepositorio(db)
        self.locacoes = LocacaoRepositorio(db, self.clientes, self.funcionarios, self.itens)

    @staticmethod
    def _exigir(obj, nome, id):
        if obj is None:
            raise NaoEncontradoError(f"{nome} {id} não encontrado(a).")
        return obj

    def cadastrar_cliente(self, nome, cpf, rua, numero, cidade, uf):
        cliente = Cliente(nome, cpf, rua, numero, cidade, uf)
        with self.db.transacao():
            return self.clientes.adicionar(cliente)

    def atualizar_cliente(self, id, nome, cpf, rua, numero, cidade, uf):
        self._exigir(self.clientes.buscar(id), "Cliente", id)
        novo = Cliente(nome, cpf, rua, numero, cidade, uf, id=id)
        with self.db.transacao():
            self.clientes.atualizar(novo)
        return novo

    def remover_cliente(self, id):
        self._exigir(self.clientes.buscar(id), "Cliente", id)
        with self.db.transacao():
            self.clientes.remover(id)

    def listar_clientes(self):
        return self.clientes.listar()

    def cadastrar_funcionario(self, nome, cpf, cargo="Atendente"):
        func = Funcionario(nome, cpf, cargo)
        with self.db.transacao():
            return self.funcionarios.adicionar(func)

    def atualizar_funcionario(self, id, nome, cpf, cargo):
        self._exigir(self.funcionarios.buscar(id), "Funcionário", id)
        novo = Funcionario(nome, cpf, cargo, id=id)
        with self.db.transacao():
            self.funcionarios.atualizar(novo)
        return novo

    def remover_funcionario(self, id):
        self._exigir(self.funcionarios.buscar(id), "Funcionário", id)
        with self.db.transacao():
            self.funcionarios.remover(id)

    def listar_funcionarios(self):
        return self.funcionarios.listar()

    def cadastrar_filme(self, titulo, ano, genero, duracao_min, lancamento=False):
        filme = Filme(titulo, ano, genero, duracao_min, lancamento)
        with self.db.transacao():
            return self.itens.adicionar(filme)

    def cadastrar_jogo(self, titulo, ano, plataforma):
        jogo = Jogo(titulo, ano, plataforma)
        with self.db.transacao():
            return self.itens.adicionar(jogo)

    def atualizar_item(self, id, item):
        atual = self._exigir(self.itens.buscar(id), "Item", id)
        if type(atual) is not type(item):
            raise RegraNegocioError("Não é possível trocar o tipo do item (filme ou jogo).")
        item.id = id
        item.disponivel = atual.disponivel
        with self.db.transacao():
            self.itens.atualizar(item)
        return item

    def remover_item(self, id):
        item = self._exigir(self.itens.buscar(id), "Item", id)
        if not item.disponivel:
            raise RegraNegocioError("Item está alugado e não pode ser removido.")
        with self.db.transacao():
            self.itens.remover(id)

    def listar_itens(self, apenas_disponiveis=False):
        return self.itens.listar(apenas_disponiveis)

    def alugar(self, cliente_id, funcionario_id, pedidos, data=None):
        cliente = self._exigir(self.clientes.buscar(cliente_id), "Cliente", cliente_id)
        func = self._exigir(self.funcionarios.buscar(funcionario_id), "Funcionário", funcionario_id)
        if not pedidos:
            raise ValidacaoError("Informe ao menos um item.")
        if self.locacoes.contar_itens_abertos(cliente_id) + len(pedidos) > Cliente.LIMITE_ITENS:
            raise RegraNegocioError(
                f"Limite de {Cliente.LIMITE_ITENS} itens alugados ao mesmo tempo excedido.")
        locacao = Locacao(cliente, func, data)
        for item_id, dias in pedidos:
            item = self._exigir(self.itens.buscar(item_id), "Item", item_id)
            locacao.adicionar_item(item, dias)
        with self.db.transacao():
            self.locacoes.adicionar(locacao)
            for il in locacao.itens:
                self.itens.atualizar_disponibilidade(il.item)
        return locacao

    def devolver(self, locacao_id, data=None):
        locacao = self._exigir(self.locacoes.buscar(locacao_id), "Locação", locacao_id)
        locacao.devolver(data)
        with self.db.transacao():
            self.locacoes.salvar_devolucao(locacao)
            for il in locacao.itens:
                self.itens.atualizar_disponibilidade(il.item)
        return Recibo.gerar(locacao)

    def recibo(self, locacao_id):
        locacao = self._exigir(self.locacoes.buscar(locacao_id), "Locação", locacao_id)
        return Recibo.gerar(locacao)

    def listar_locacoes(self, apenas_abertas=False):
        return self.locacoes.listar(apenas_abertas)
