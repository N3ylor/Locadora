import re
from abc import ABC, abstractmethod

from ..excecoes import ValidacaoError
from .endereco import Endereco


class Pessoa(ABC):
    """Classe abstrata base (HERANÇA): Cliente e Funcionario herdam dela."""

    def __init__(self, nome, cpf, id=None):
        nome = (nome or "").strip()
        cpf = re.sub(r"\D", "", cpf or "")
        if not nome:
            raise ValidacaoError("Nome é obrigatório.")
        if len(cpf) != 11:
            raise ValidacaoError("CPF deve ter 11 dígitos.")
        self.id = id
        self.nome = nome
        self.cpf = cpf

    @abstractmethod
    def descricao(self) -> str:
        """Cada subclasse descreve a si mesma (POLIMORFISMO)."""

    def __str__(self):
        return self.descricao()


class Cliente(Pessoa):
    LIMITE_ITENS = 3  # máximo de itens alugados ao mesmo tempo

    def __init__(self, nome, cpf, rua, numero, cidade, uf, id=None):
        super().__init__(nome, cpf, id)
        # COMPOSIÇÃO: o Endereço é criado pelo Cliente e pertence a ele.
        self.endereco = Endereco(rua, numero, cidade, uf)

    def descricao(self):
        return f"[{self.id}] Cliente: {self.nome} | CPF: {self.cpf} | {self.endereco}"


class Funcionario(Pessoa):
    def __init__(self, nome, cpf, cargo="Atendente", id=None):
        super().__init__(nome, cpf, id)
        self.cargo = (cargo or "").strip() or "Atendente"

    def descricao(self):
        return f"[{self.id}] Funcionário: {self.nome} | CPF: {self.cpf} | Cargo: {self.cargo}"
