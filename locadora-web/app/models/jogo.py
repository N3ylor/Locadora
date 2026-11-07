"""Modelo de jogo (recurso Banco)."""
from dataclasses import dataclass
from decimal import Decimal

from app.models.validacao import validar_catalogo

PLATAFORMA_MAX = 50


@dataclass
class Jogo:
    id: int
    titulo: str
    plataforma: str
    valor_diaria: Decimal

    @property
    def categoria(self):
        return self.plataforma

    @property
    def valor_formatado(self):
        return f'{self.valor_diaria:.2f}'.replace('.', ',')

    def to_dict(self):
        return {'id': self.id, 'titulo': self.titulo, 'plataforma': self.plataforma,
                'valor_diaria': float(self.valor_diaria)}

    @staticmethod
    def validar(dados):
        """Devolve ``(titulo, plataforma, valor_diaria)`` limpos ou levanta ValidationError."""
        return validar_catalogo(dados, 'plataforma', PLATAFORMA_MAX)
