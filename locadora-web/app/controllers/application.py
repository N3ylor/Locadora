"""Application: controlador principal do BMVC.

Compõe os controladores dos recursos (Portal e Banco), mantém o dicionário
``pages`` e o método ``render`` do framework original.
"""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import bottle
from bottle import template

from app.config import VIEWS_DIR, Config
from app.controllers.banco_controller import BancoController
from app.controllers.catalogo_controller import CatalogoController
from app.controllers.clientes_controller import ClientesController
from app.controllers.database import Database
from app.controllers.datarecord import DataRecord
from app.controllers.filmes_repository import FilmesRepository, JogosRepository
from app.controllers.locacoes_controller import LocacoesController
from app.controllers.locacoes_repository import LocacoesRepository
from app.controllers.portal_controller import PortalController
from app.models.filme import Filme
from app.models.jogo import Jogo

# Templates são localizados pelo nome, independentemente do diretório de execução.
if str(VIEWS_DIR) not in bottle.TEMPLATE_PATH:
    bottle.TEMPLATE_PATH.insert(0, str(VIEWS_DIR))


def _relogio_padrao(nome_fuso):
    """Função que devolve a data de hoje no fuso configurado (UTC se o fuso for inválido)."""
    try:
        fuso = ZoneInfo(nome_fuso)
    except Exception:
        fuso = timezone.utc
    return lambda: datetime.now(fuso).date()


class Application:
    def __init__(self, config=None, relogio=None):
        self.config = config or Config.from_env()
        self.database = Database(self.config.db_path)
        self.models = DataRecord(self.database, self.config)
        self.portal_controller = PortalController(self.models, self.config)
        locacoes_repo = LocacoesRepository(self.database)
        filmes = CatalogoController(FilmesRepository(self.database), Filme, 'Filme',
                                    em_uso=lambda i: locacoes_repo.item_alugado('filme', i))
        jogos = CatalogoController(JogosRepository(self.database), Jogo, 'Jogo',
                                   em_uso=lambda i: locacoes_repo.item_alugado('jogo', i))
        self.clientes_controller = ClientesController(self.models, locacoes_repo)
        self.locacoes_controller = LocacoesController(
            locacoes_repo, {'filme': filmes, 'jogo': jogos}, relogio or _relogio_padrao(self.config.timezone))
        self.banco_controller = BancoController(
            self.portal_controller, filmes, jogos, self.clientes_controller, self.locacoes_controller)
        self.pages = {
            'helper': self.helper,
            'portal': self.portal,
            'banco': self.banco,
            'cliente': self.cliente,
        }

    def render(self, page, parameter=None):
        content = self.pages.get(page, self.helper)
        if not parameter:
            return content()
        return content(parameter)

    # ---------- páginas ----------
    def helper(self):
        return template('helper')

    def portal(self, error=None):
        return self.portal_controller.portal(error)

    def banco(self):
        return self.banco_controller.banco()

    def cliente(self):
        return self.banco_controller.cliente()

    # ---------- atalhos usados pelo route.py ----------
    def current_user(self):
        return self.portal_controller.current_user()

    def authenticate_user(self, username, password, client_ip):
        return self.portal_controller.authenticate_user(username, password, client_ip)

    def logout_user(self):
        self.portal_controller.logout_user()

    def check_database(self):
        self.database.ping()
