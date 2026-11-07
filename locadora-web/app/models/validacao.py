"""Validação compartilhada pelos itens do catálogo (filmes e jogos)."""
import unicodedata
from decimal import Decimal, InvalidOperation

TITULO_MAX = 200
VALOR_MAX = Decimal('9999.99')
CENTAVO = Decimal('0.01')


class ValidationError(ValueError):
    """Dados inválidos. ``campos`` mapeia o nome do campo à mensagem de erro."""

    def __init__(self, campos):
        super().__init__('; '.join(f'{k}: {v}' for k, v in campos.items()))
        self.campos = campos


def texto(valor, nome, maximo, minimo=1):
    if not isinstance(valor, str):
        return None, f'{nome} é obrigatório e deve ser texto.'
    valor = valor.strip()
    if not valor:
        return None, f'{nome} não pode ficar vazio.'
    if len(valor) < minimo:
        return None, f'{nome} deve ter no mínimo {minimo} caracteres.'
    if len(valor) > maximo:
        return None, f'{nome} deve ter no máximo {maximo} caracteres.'
    if any(unicodedata.category(c).startswith('C') for c in valor):
        return None, f'{nome} contém caracteres de controle não permitidos.'
    return valor, None


def valor_diaria(valor):
    if valor is None:
        return None, 'valor_diaria é obrigatório.'
    if isinstance(valor, bool) or not isinstance(valor, (int, float, str)):
        return None, 'valor_diaria deve ser um número.'
    try:
        numero = Decimal(repr(valor) if isinstance(valor, float) else str(valor).strip())
    except InvalidOperation:
        return None, 'valor_diaria deve ser um número.'
    if not numero.is_finite():
        return None, 'valor_diaria deve ser um número finito.'
    if numero < 0 or numero > VALOR_MAX:
        return None, f'valor_diaria deve estar entre 0 e {VALOR_MAX}.'
    if numero.normalize().as_tuple().exponent < -2:
        return None, 'valor_diaria aceita no máximo 2 casas decimais.'
    return numero.quantize(CENTAVO), None


def validar_catalogo(dados, campo_categoria, max_categoria):
    """Valida ``titulo``, o campo de categoria (genero/plataforma) e ``valor_diaria``."""
    if not isinstance(dados, dict):
        raise ValidationError({'corpo': f'envie um objeto JSON com titulo, {campo_categoria} e valor_diaria.'})
    erros = {}
    titulo, erro = texto(dados.get('titulo'), 'titulo', TITULO_MAX)
    if erro:
        erros['titulo'] = erro
    categoria, erro = texto(dados.get(campo_categoria), campo_categoria, max_categoria)
    if erro:
        erros[campo_categoria] = erro
    valor, erro = valor_diaria(dados.get('valor_diaria'))
    if erro:
        erros['valor_diaria'] = erro
    if erros:
        raise ValidationError(erros)
    return titulo, categoria, valor
