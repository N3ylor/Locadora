"""Modelo de filme (recurso Banco)."""
from dataclasses import dataclass
from decimal import Decimal

from app.models.validacao import CENTAVO, TITULO_MAX, VALOR_MAX, ValidationError, validar_catalogo

# Reexportados para compatibilidade com quem importa de app.models.filme.
__all__ = ['Filme', 'GENERO_MAX', 'CENTAVO', 'TITULO_MAX', 'VALOR_MAX', 'ValidationError']

GENERO_MAX = 100


@dataclass
class Filme:
    id: int
    titulo: str
    genero: str
    valor_diaria: Decimal

    @property
    def categoria(self):
        return self.genero

    @property
    def valor_formatado(self):
        """Valor no padrão brasileiro, ex.: 5,50."""
        return f'{self.valor_diaria:.2f}'.replace('.', ',')

    def to_dict(self):
        return {'id': self.id, 'titulo': self.titulo, 'genero': self.genero,
                'valor_diaria': float(self.valor_diaria)}

    @staticmethod
    def validar(dados):
        """Devolve ``(titulo, genero, valor_diaria)`` limpos ou levanta ValidationError."""
        return validar_catalogo(dados, 'genero', GENERO_MAX)
