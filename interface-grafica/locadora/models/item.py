from abc import ABC, abstractmethod
from datetime import date

from ..excecoes import RegraNegocioError, ValidacaoError


class Item(ABC):
    TIPO = ""

    def __init__(self, titulo, ano, disponivel=True, id=None):
        titulo = (titulo or "").strip()
        if not titulo:
            raise ValidacaoError("Título é obrigatório.")
        if not isinstance(ano, int) or not 1888 <= ano <= date.today().year + 1:
            raise ValidacaoError("Ano inválido.")
        self.id = id
        self.titulo = titulo
        self.ano = ano
        self.disponivel = disponivel

    @property
    @abstractmethod
    def valor_diaria(self) -> float: ...

    @property
    @abstractmethod
    def multa_por_dia(self) -> float: ...

    @abstractmethod
    def descricao(self) -> str: ...

    def calcular_valor(self, dias):
        if dias <= 0:
            raise ValidacaoError("Dias deve ser maior que zero.")
        return round(self.valor_diaria * dias, 2)

    def calcular_multa(self, dias_atraso):
        return round(self.multa_por_dia * max(0, dias_atraso), 2)

    def emprestar(self):
        if not self.disponivel:
            raise RegraNegocioError(f"'{self.titulo}' não está disponível.")
        self.disponivel = False

    def devolver(self):
        self.disponivel = True

    def _status(self):
        return "Disponível" if self.disponivel else "Alugado"

    def __str__(self):
        return self.descricao()


class Filme(Item):
    TIPO = "filme"

    def __init__(self, titulo, ano, genero, duracao_min, lancamento=False, disponivel=True, id=None):
        super().__init__(titulo, ano, disponivel, id)
        if not isinstance(duracao_min, int) or duracao_min <= 0:
            raise ValidacaoError("Duração deve ser um número positivo.")
        self.genero = (genero or "").strip() or "Geral"
        self.duracao_min = duracao_min
        self.lancamento = bool(lancamento)

    @property
    def valor_diaria(self):
        return 9.0 if self.lancamento else 6.0

    @property
    def multa_por_dia(self):
        return 3.0 if self.lancamento else 2.0

    def descricao(self):
        lanc = " (LANÇAMENTO)" if self.lancamento else ""
        return (f"[{self.id}] Filme: {self.titulo} ({self.ano}){lanc} | {self.genero} | "
                f"{self.duracao_min} min | R$ {self.valor_diaria:.2f}/dia | {self._status()}")


class Jogo(Item):
    TIPO = "jogo"

    def __init__(self, titulo, ano, plataforma, disponivel=True, id=None):
        super().__init__(titulo, ano, disponivel, id)
        plataforma = (plataforma or "").strip()
        if not plataforma:
            raise ValidacaoError("Plataforma é obrigatória.")
        self.plataforma = plataforma

    @property
    def valor_diaria(self):
        return 10.0

    @property
    def multa_por_dia(self):
        return 4.0

    def calcular_valor(self, dias):
        valor = super().calcular_valor(dias)
        return round(valor * 0.9, 2) if dias >= 5 else valor

    def descricao(self):
        return (f"[{self.id}] Jogo: {self.titulo} ({self.ano}) | {self.plataforma} | "
                f"R$ {self.valor_diaria:.2f}/dia | {self._status()}")
