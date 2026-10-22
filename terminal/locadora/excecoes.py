"""Exceções do domínio da locadora."""


class LocadoraError(Exception):
    """Erro base do sistema."""


class ValidacaoError(LocadoraError):
    """Dados inválidos informados pelo usuário."""


class NaoEncontradoError(LocadoraError):
    """Registro não encontrado."""


class RegraNegocioError(LocadoraError):
    """Violação de uma regra de negócio."""
