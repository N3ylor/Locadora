from datetime import date, timedelta

from ..excecoes import RegraNegocioError, ValidacaoError


class ItemLocacao:
    def __init__(self, item, dias, data_locacao):
        if dias <= 0:
            raise ValidacaoError("Dias deve ser maior que zero.")
        self.item = item
        self.dias = dias
        self.data_prevista = data_locacao + timedelta(days=dias)

    @property
    def valor(self):
        return self.item.calcular_valor(self.dias)

    def multa(self, data_devolucao):
        return self.item.calcular_multa((data_devolucao - self.data_prevista).days)


class Locacao:
    def __init__(self, cliente, funcionario, data_locacao=None, id=None):
        self.id = id
        self.cliente = cliente
        self.funcionario = funcionario
        self.data_locacao = data_locacao or date.today()
        self.data_devolucao = None
        self.multa = 0.0
        self.itens = []

    @property
    def devolvida(self):
        return self.data_devolucao is not None

    def adicionar_item(self, item, dias):
        if self.devolvida:
            raise RegraNegocioError("Locação já encerrada.")
        if any(il.item.id is not None and il.item.id == item.id for il in self.itens):
            raise RegraNegocioError(f"'{item.titulo}' já está nesta locação.")
        if dias <= 0:
            raise ValidacaoError("Dias deve ser maior que zero.")
        item.emprestar()
        self.itens.append(ItemLocacao(item, dias, self.data_locacao))

    @property
    def total(self):
        return round(sum(il.valor for il in self.itens), 2)

    def devolver(self, data_devolucao=None):
        data_devolucao = data_devolucao or date.today()
        if self.devolvida:
            raise RegraNegocioError("Locação já foi devolvida.")
        if data_devolucao < self.data_locacao:
            raise ValidacaoError("Data de devolução anterior à locação.")
        self.multa = round(sum(il.multa(data_devolucao) for il in self.itens), 2)
        self.data_devolucao = data_devolucao
        for il in self.itens:
            il.item.devolver()

    def __str__(self):
        situacao = f"devolvida em {self.data_devolucao:%d/%m/%Y}" if self.devolvida else "em aberto"
        titulos = ", ".join(il.item.titulo for il in self.itens)
        return (f"[{self.id}] {self.data_locacao:%d/%m/%Y} | {self.cliente.nome} | {titulos} | "
                f"Total R$ {self.total:.2f} | {situacao}")
