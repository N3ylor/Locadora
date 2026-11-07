"""Regras do CRUD de clientes (somente administrador)."""
from app.controllers.errors import ApiError
from app.models.cliente import Cliente, normalizar_username
from app.models.validacao import ValidationError


class ClientesController:
    def __init__(self, models, locacoes=None):
        self.models = models      # DataRecord
        self.locacoes = locacoes  # LocacoesRepository

    def listar(self):
        return self.models.listar_clientes()

    def obter(self, username):
        conta = self.models.obter_cliente(normalizar_username(username))
        if conta is None:
            raise ApiError(404, f'Cliente {username} não encontrado.')
        return conta

    def criar(self, dados):
        try:
            username, nome, senha = Cliente.validar_novo(dados)
        except ValidationError as err:
            raise ApiError(422, 'Dados inválidos.', err.campos)
        conta = self.models.criar_cliente(username, nome, senha)
        if conta is None:
            raise ApiError(409, f'O username "{username}" já está em uso.')
        return conta

    def atualizar(self, username, dados):
        self.obter(username)  # 404 antes de validar o corpo
        try:
            nome, senha = Cliente.validar_edicao(dados)
        except ValidationError as err:
            raise ApiError(422, 'Dados inválidos.', err.campos)
        return self.models.atualizar_cliente(normalizar_username(username), nome, senha)

    def excluir(self, username):
        self.obter(username)  # 404 se não existir
        if self.locacoes and self.locacoes.contar_abertas(normalizar_username(username)):
            raise ApiError(409, f'O cliente {username} tem locações em aberto. Registre a devolução antes.')
        if not self.models.excluir_cliente(normalizar_username(username)):
            raise ApiError(404, f'Cliente {username} não encontrado.')
