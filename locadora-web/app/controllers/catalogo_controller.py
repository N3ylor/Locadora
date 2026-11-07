"""Regras do CRUD de um item do catálogo (usado para filmes e jogos)."""
from app.controllers.errors import ApiError
from app.models.validacao import ValidationError


class CatalogoController:
    def __init__(self, repo, modelo, rotulo, em_uso=None):
        self.repo = repo        # CatalogoRepository
        self.modelo = modelo    # Filme ou Jogo (fornece .validar)
        self.rotulo = rotulo    # 'Filme' ou 'Jogo' (mensagens)
        self.em_uso = em_uso    # função(id) -> True se o item está alugado

    def listar(self):
        return self.repo.listar()

    def obter(self, id):
        item = self.repo.obter(id)
        if item is None:
            raise ApiError(404, f'{self.rotulo} {id} não encontrado.')
        return item

    def criar(self, dados):
        titulo, categoria, valor = self._validar(dados)
        return self.repo.obter(self.repo.criar(titulo, categoria, valor))

    def atualizar(self, id, dados):
        self.obter(id)  # 404 antes de validar o corpo
        titulo, categoria, valor = self._validar(dados)
        if not self.repo.atualizar(id, titulo, categoria, valor):
            raise ApiError(404, f'{self.rotulo} {id} não encontrado.')
        return self.repo.obter(id)

    def excluir(self, id):
        self.obter(id)  # 404 se não existir
        if self.em_uso and self.em_uso(id):
            raise ApiError(409, f'{self.rotulo} {id} está alugado no momento e não pode ser excluído.')
        if not self.repo.excluir(id):
            raise ApiError(404, f'{self.rotulo} {id} não encontrado.')

    def _validar(self, dados):
        try:
            return self.modelo.validar(dados)
        except ValidationError as err:
            raise ApiError(422, 'Dados inválidos.', err.campos)
