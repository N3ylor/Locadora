"""Modelo de locação e regras de cálculo (valor, desconto e multa)."""
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from app.models.validacao import CENTAVO, ValidationError

TIPOS = ('filme', 'jogo')
LIMITE_ITENS = 3                         # itens alugados ao mesmo tempo, por cliente
DIAS_MAX = 30                            # prazo máximo de uma locação
JOGO_DIAS_DESCONTO = 5                   # jogo alugado por 5 dias ou mais...
JOGO_DESCONTO = Decimal('0.10')          # ...ganha 10% de desconto
MULTA_DIA = {'filme': Decimal('2.00'), 'jogo': Decimal('4.00')}  # por dia de atraso
_INT64_MAX = 2**63 - 1


def calcular_valor(tipo, valor_diaria, dias):
    total = Decimal(valor_diaria) * dias
    if tipo == 'jogo' and dias >= JOGO_DIAS_DESCONTO:
        total *= (1 - JOGO_DESCONTO)
    return total.quantize(CENTAVO, rounding=ROUND_HALF_UP)


def calcular_multa(tipo, dias_atraso):
    return (MULTA_DIA[tipo] * max(0, dias_atraso)).quantize(CENTAVO)


def formatar_valor(valor):
    return f'{valor:.2f}'.replace('.', ',')


def formatar_data(data):
    return data.strftime('%d/%m/%Y') if data else '—'


def _inteiro(valor, nome, minimo, maximo):
    if isinstance(valor, bool):
        return None, f'{nome} deve ser um número inteiro.'
    if isinstance(valor, str):
        valor = valor.strip()
        valor = int(valor) if valor.isascii() and valor.isdigit() else None
    if not isinstance(valor, int):
        return None, f'{nome} deve ser um número inteiro.'
    if not (minimo <= valor <= maximo):
        return None, f'{nome} deve estar entre {minimo} e {maximo}.'
    return valor, None


def validar_pedido(dados):
    """Valida ``tipo`` ('filme'/'jogo'), ``item_id`` e ``dias``. Devolve ``(tipo, item_id, dias)``."""
    if not isinstance(dados, dict):
        raise ValidationError({'corpo': 'envie um objeto JSON com tipo, item_id e dias.'})
    erros = {}
    tipo = dados.get('tipo')
    if not isinstance(tipo, str) or tipo.strip().lower() not in TIPOS:
        erros['tipo'] = "tipo deve ser 'filme' ou 'jogo'."
    item_id, erro = _inteiro(dados.get('item_id'), 'item_id', 1, _INT64_MAX)
    if erro:
        erros['item_id'] = erro
    dias, erro = _inteiro(dados.get('dias'), 'dias', 1, DIAS_MAX)
    if erro:
        erros['dias'] = erro
    if erros:
        raise ValidationError(erros)
    return tipo.strip().lower(), item_id, dias


@dataclass
class Locacao:
    id: int
    username: str
    tipo: str
    item_id: int
    titulo: str
    valor_diaria: Decimal
    dias: int
    valor_total: Decimal
    data_locacao: date
    data_prevista: date
    data_devolucao: date | None = None
    multa: Decimal | None = None   # definida na devolução

    @property
    def aberta(self):
        return self.data_devolucao is None

    def dias_atraso(self, hoje):
        referencia = self.data_devolucao or hoje
        return max(0, (referencia - self.data_prevista).days)

    def multa_em(self, hoje):
        """Multa já fixada (devolvida) ou acumulada até hoje (em aberto)."""
        if not self.aberta and self.multa is not None:
            return self.multa
        return calcular_multa(self.tipo, self.dias_atraso(hoje))

    def total_em(self, hoje):
        return self.valor_total + self.multa_em(hoje)

    # ---------- textos para os templates ----------
    def situacao(self, hoje):
        if not self.aberta:
            return f'Devolvida em {formatar_data(self.data_devolucao)}'
        atraso = self.dias_atraso(hoje)
        return f'Atrasada {atraso} dia(s)' if atraso else 'No prazo'

    def valor_fmt(self):
        return formatar_valor(self.valor_total)

    def multa_fmt(self, hoje):
        return formatar_valor(self.multa_em(hoje))

    def total_fmt(self, hoje):
        return formatar_valor(self.total_em(hoje))

    def to_dict(self, hoje):
        return {
            'id': self.id, 'username': self.username, 'tipo': self.tipo, 'item_id': self.item_id,
            'titulo': self.titulo, 'dias': self.dias, 'valor_diaria': float(self.valor_diaria),
            'valor_total': float(self.valor_total),
            'data_locacao': self.data_locacao.isoformat(),
            'data_prevista': self.data_prevista.isoformat(),
            'data_devolucao': self.data_devolucao.isoformat() if self.data_devolucao else None,
            'status': 'aberta' if self.aberta else 'devolvida',
            'dias_atraso': self.dias_atraso(hoje),
            'multa': float(self.multa_em(hoje)),
            'total': float(self.total_em(hoje)),
        }
