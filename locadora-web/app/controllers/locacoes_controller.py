"""Regras de locação e devolução."""
from datetime import timedelta

from app.controllers.errors import ApiError
from app.controllers.locacoes_repository import ItemIndisponivel, LimiteExcedido
from app.models.locacao import LIMITE_ITENS, calcular_multa, calcular_valor, validar_pedido
from app.models.validacao import ValidationError


class LocacoesController:
    def __init__(self, repo, catalogos, relogio):
        self.repo = repo            # LocacoesRepository
        self.catalogos = catalogos  # {'filme': CatalogoController, 'jogo': CatalogoController}
        self.relogio = relogio      # função que devolve a data de hoje

    def hoje(self):
        return self.relogio()

    def listar(self, conta):
        """Administrador vê todas; cliente vê apenas as suas."""
        return self.repo.listar(None if conta.is_admin else conta.username)

    def obter(self, conta, id):
        loc = self.repo.obter(id)
        if loc is None or (not conta.is_admin and loc.username != conta.username):
            raise ApiError(404, f'Locação {id} não encontrada.')
        return loc

    def alugar(self, conta, dados):
        if conta.is_admin:
            raise ApiError(403, 'Apenas clientes podem alugar itens.', codigo='somente_cliente')
        try:
            tipo, item_id, dias = validar_pedido(dados)
        except ValidationError as err:
            raise ApiError(422, 'Dados inválidos.', err.campos, codigo='invalido')
        item = self.catalogos[tipo].obter(item_id)  # 404 se o item não existir
        hoje = self.hoje()
        try:
            novo_id = self.repo.criar(conta.username, tipo, item, dias,
                                      calcular_valor(tipo, item.valor_diaria, dias),
                                      hoje, hoje + timedelta(days=dias), LIMITE_ITENS)
        except LimiteExcedido:
            raise ApiError(409, f'Limite de {LIMITE_ITENS} itens alugados ao mesmo tempo atingido. '
                                'Devolva um item para alugar outro.', codigo='limite')
        except ItemIndisponivel:
            raise ApiError(409, 'Este item já está alugado no momento.', codigo='indisponivel')
        return self.repo.obter(novo_id)

    def devolver(self, conta, id):
        loc = self.obter(conta, id)  # cliente só devolve as próprias; admin devolve qualquer uma
        hoje = self.hoje()
        multa = calcular_multa(loc.tipo, loc.dias_atraso(hoje))
        if not self.repo.devolver(loc.id, hoje, multa):
            raise ApiError(409, f'Locação {id} já foi devolvida.', codigo='ja_devolvida')
        return self.repo.obter(loc.id)
