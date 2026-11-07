"""Validação dos dados de cliente (conta com perfil ``cliente``)."""
import re

from app.models.validacao import ValidationError, texto

USERNAME_RE = re.compile(r'^[a-z0-9][a-z0-9_.-]{2,31}$')
SENHA_MIN, SENHA_MAX = 8, 128
NOME_MAX = 100


def normalizar_username(username):
    return username.strip().lower() if isinstance(username, str) else ''


def _username(valor):
    username = normalizar_username(valor)
    if not USERNAME_RE.match(username):
        return None, ('username deve ter 3 a 32 caracteres: letras minúsculas, números, '
                      'ponto, hífen ou sublinhado (começando por letra ou número).')
    return username, None


def _senha(valor):
    if not isinstance(valor, str) or not (SENHA_MIN <= len(valor) <= SENHA_MAX):
        return None, f'senha deve ter de {SENHA_MIN} a {SENHA_MAX} caracteres.'
    return valor, None


class Cliente:
    @staticmethod
    def validar_novo(dados):
        """Devolve ``(username, nome, senha)``."""
        if not isinstance(dados, dict):
            raise ValidationError({'corpo': 'envie um objeto JSON com username, nome e senha.'})
        erros = {}
        username, erro = _username(dados.get('username'))
        if erro:
            erros['username'] = erro
        nome, erro = texto(dados.get('nome'), 'nome', NOME_MAX)
        if erro:
            erros['nome'] = erro
        senha, erro = _senha(dados.get('senha'))
        if erro:
            erros['senha'] = erro
        if erros:
            raise ValidationError(erros)
        return username, nome, senha

    @staticmethod
    def validar_edicao(dados):
        """Edição parcial: ``nome`` e/ou ``senha``. Devolve ``(nome|None, senha|None)``."""
        if not isinstance(dados, dict):
            raise ValidationError({'corpo': 'envie um objeto JSON com nome e/ou senha.'})
        if 'nome' not in dados and 'senha' not in dados:
            raise ValidationError({'corpo': 'informe nome e/ou senha para atualizar.'})
        erros, nome, senha = {}, None, None
        if 'nome' in dados:
            nome, erro = texto(dados['nome'], 'nome', NOME_MAX)
            if erro:
                erros['nome'] = erro
        if 'senha' in dados:
            senha, erro = _senha(dados['senha'])
            if erro:
                erros['senha'] = erro
        if erros:
            raise ValidationError(erros)
        return nome, senha
