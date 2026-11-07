"""Rotas da Locadora Web (framework BMVC sobre Bottle).

Este arquivo só mapeia URLs para ações do controlador ``Application``; as regras
de negócio ficam em app/controllers e a validação em app/models.

    /portal      GET/POST  login (admin -> /banco, cliente -> /cliente)
    /logout      POST      logout
    /banco       GET       painel do administrador (READ de filmes, jogos e clientes)
    /cliente     GET       página do cliente (catálogo somente leitura)
    /api/filmes   /api/jogos      GET (qualquer login) · POST, PUT, DELETE (admin)
    /api/clientes                 GET, POST, PUT, DELETE (admin)
    /api/locacoes      GET (cliente: as suas · admin: todas) · POST (cliente aluga)
    /api/locacoes/<id>/devolucao  POST (dono da locação ou admin)
    /cliente/alugar, /cliente/devolver/<id>   POST (formulários da página do cliente)
    /health      GET       verificação de saúde (Docker)
"""
import functools
import json
import logging
import sys

from bottle import Bottle, BaseRequest, redirect, request, response, run, static_file, template

from app.config import STATIC_DIR, ConfigError
from app.controllers.application import Application
from app.controllers.errors import ApiError

MAX_BODY_BYTES = 64 * 1024
BaseRequest.MEMFILE_MAX = MAX_BODY_BYTES

log = logging.getLogger('locadora')

CSP = ("default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; "
       "form-action 'self'; frame-ancestors 'none'; base-uri 'none'")


def json_response(corpo, status=200, headers=None):
    response.status = status
    response.content_type = 'application/json; charset=utf-8'
    for nome, valor in (headers or {}).items():
        response.set_header(nome, valor)
    return json.dumps(corpo, ensure_ascii=False)


def read_json():
    """Lê o corpo JSON da requisição, com erros claros (415/413/400)."""
    if not (request.content_type or '').lower().startswith('application/json'):
        raise ApiError(415, 'Envie o cabeçalho "Content-Type: application/json".')
    if request.content_length > MAX_BODY_BYTES:
        raise ApiError(413, 'Corpo da requisição grande demais.')
    try:
        return json.loads(request.body.read(MAX_BODY_BYTES + 1).decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        raise ApiError(400, 'JSON malformado.')


def create_app(ctl=None):
    ctl = ctl or Application()
    app = Bottle()

    def api(handler=None, *, admin=False):
        """Exige login (e perfil admin, se ``admin=True``), converte ApiError em JSON e serializa."""
        def decorar(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    if admin:
                        ctl.portal_controller.require_admin()
                    else:
                        ctl.portal_controller.require_user()
                    status, corpo, headers = func(*args, **kwargs)
                except ApiError as err:
                    return json_response(err.to_dict(), err.status)
                return json_response(corpo, status, headers)
            return wrapper
        return decorar(handler) if handler else decorar

    # ---------- hooks ----------
    @app.hook('after_request')
    def security_and_log():
        response.set_header('X-Content-Type-Options', 'nosniff')
        response.set_header('X-Frame-Options', 'DENY')
        response.set_header('Referrer-Policy', 'same-origin')
        response.set_header('Content-Security-Policy', CSP)
        if not request.path.startswith('/static/'):
            response.set_header('Cache-Control', 'no-store')
        if request.path != '/health':
            log.info('%s %s %s -> %s', request.remote_addr, request.method, request.path,
                     response.status_code)

    @app.error(400)
    @app.error(401)
    @app.error(403)
    @app.error(404)
    @app.error(405)
    @app.error(413)
    @app.error(500)
    def error_handler(err):
        if err.status_code == 500:
            log.error('Erro interno em %s %s: %r\n%s', request.method, request.path,
                      err.exception, err.traceback)
        mensagem = 'Erro interno do servidor.' if err.status_code == 500 else (
            'Recurso não encontrado.' if err.status_code == 404 else
            'Método não permitido.' if err.status_code == 405 else str(err.body or err.status_line))
        if request.path.startswith('/api/'):
            return json_response({'erro': mensagem}, err.status_code)
        response.content_type = 'text/html; charset=utf-8'
        return template('erro', status=err.status_code, mensagem=mensagem)

    # ---------- estáticos e utilitários ----------
    @app.get('/static/<filepath:path>')
    def static(filepath):
        return static_file(filepath, root=str(STATIC_DIR))

    @app.get('/health')
    def health():
        try:
            ctl.check_database()
        except Exception:
            log.exception('Falha no health check')
            return json_response({'status': 'erro'}, 503)
        return json_response({'status': 'ok'})

    # ---------- páginas (BMVC: ctl.render) ----------
    @app.get('/')
    def home():
        conta = ctl.portal_controller.current_account()
        redirect(ctl.portal_controller.destino(conta) if conta else '/portal')

    @app.get('/helper')
    def action_helper():
        return ctl.render('helper')

    @app.get('/portal')
    def action_portal_get():
        return ctl.render('portal')

    @app.post('/portal')
    def action_portal_post():
        session_id, erro, status, destino = ctl.authenticate_user(
            request.forms.getunicode('username'), request.forms.getunicode('password'),
            request.remote_addr)
        if not session_id:
            response.status = status
            return ctl.render('portal', erro)
        response.set_cookie('session_id', session_id, httponly=True, path='/',
                            secure=ctl.config.cookie_secure, samesite='Strict',
                            max_age=ctl.config.session_ttl)
        redirect(destino)

    @app.post('/logout')
    def action_logout():
        ctl.logout_user()
        response.delete_cookie('session_id', path='/')
        redirect('/portal')

    @app.get('/banco')
    def action_banco():
        return ctl.render('banco')

    @app.get('/cliente')
    def action_cliente():
        return ctl.render('cliente')

    def formulario_cliente(acao):
        """Executa uma ação dos formulários da página do cliente e volta com um aviso."""
        conta = ctl.portal_controller.current_account()
        if not conta:
            redirect('/portal')
        try:
            aviso = acao(conta)
        except ApiError as err:
            aviso = err.codigo or ('nao_encontrado' if err.status == 404 else 'erro')
        redirect(f'{ctl.portal_controller.destino(conta)}?aviso={aviso}')

    @app.post('/cliente/alugar')
    def action_cliente_alugar():
        def acao(conta):
            ctl.locacoes_controller.alugar(conta, {
                'tipo': request.forms.getunicode('tipo'), 'item_id': request.forms.getunicode('item_id'),
                'dias': request.forms.getunicode('dias')})
            return 'alugado'
        formulario_cliente(acao)

    @app.post('/cliente/devolver/<id:int>')
    def action_cliente_devolver(id):
        def acao(conta):
            loc = ctl.locacoes_controller.devolver(conta, id)
            return 'devolvido_multa' if loc.multa else 'devolvido'
        formulario_cliente(acao)

    # ---------- API CRUD dos itens do catálogo (filmes e jogos) ----------
    def registrar_catalogo(nome, ctrl):
        """Leitura: qualquer usuário autenticado. Escrita: somente administrador."""
        base = f'/api/{nome}'

        @app.get(base, name=f'{nome}_listar')
        @api
        def listar():
            itens = ctrl.listar()
            return 200, {'total': len(itens), nome: [i.to_dict() for i in itens]}, None

        @app.get(base + '/<id:int>', name=f'{nome}_obter')
        @api
        def obter(id):
            return 200, ctrl.obter(id).to_dict(), None

        @app.post(base, name=f'{nome}_criar')
        @api(admin=True)
        def criar():
            item = ctrl.criar(read_json())
            return 201, item.to_dict(), {'Location': f'{base}/{item.id}'}

        @app.put(base + '/<id:int>', name=f'{nome}_atualizar')
        @api(admin=True)
        def atualizar(id):
            return 200, ctrl.atualizar(id, read_json()).to_dict(), None

        @app.delete(base + '/<id:int>', name=f'{nome}_excluir')
        @api(admin=True)
        def excluir(id):
            ctrl.excluir(id)
            return 200, {'mensagem': f'{ctrl.rotulo} {id} excluído.', 'id': id}, None

    registrar_catalogo('filmes', ctl.banco_controller.filmes)
    registrar_catalogo('jogos', ctl.banco_controller.jogos)

    # ---------- API CRUD de clientes (somente administrador) ----------
    clientes = ctl.clientes_controller

    @app.get('/api/clientes')
    @api(admin=True)
    def api_clientes_listar():
        lista = clientes.listar()
        return 200, {'total': len(lista), 'clientes': [c.to_dict() for c in lista]}, None

    @app.get('/api/clientes/<username>')
    @api(admin=True)
    def api_clientes_obter(username):
        return 200, clientes.obter(username).to_dict(), None

    @app.post('/api/clientes')
    @api(admin=True)
    def api_clientes_criar():
        conta = clientes.criar(read_json())
        return 201, conta.to_dict(), {'Location': f'/api/clientes/{conta.username}'}

    @app.put('/api/clientes/<username>')
    @api(admin=True)
    def api_clientes_atualizar(username):
        return 200, clientes.atualizar(username, read_json()).to_dict(), None

    @app.delete('/api/clientes/<username>')
    @api(admin=True)
    def api_clientes_excluir(username):
        clientes.excluir(username)
        return 200, {'mensagem': f'Cliente {username} excluído.', 'username': username}, None

    # ---------- API de locações ----------
    locacoes = ctl.locacoes_controller

    @app.get('/api/locacoes')
    @api
    def api_locacoes_listar():
        itens, hoje = locacoes.listar(ctl.portal_controller.require_user()), locacoes.hoje()
        return 200, {'total': len(itens), 'locacoes': [l.to_dict(hoje) for l in itens]}, None

    @app.get('/api/locacoes/<id:int>')
    @api
    def api_locacoes_obter(id):
        loc = locacoes.obter(ctl.portal_controller.require_user(), id)
        return 200, loc.to_dict(locacoes.hoje()), None

    @app.post('/api/locacoes')
    @api
    def api_locacoes_criar():
        loc = locacoes.alugar(ctl.portal_controller.require_user(), read_json())
        return 201, loc.to_dict(locacoes.hoje()), {'Location': f'/api/locacoes/{loc.id}'}

    @app.post('/api/locacoes/<id:int>/devolucao')
    @api
    def api_locacoes_devolver(id):
        loc = locacoes.devolver(ctl.portal_controller.require_user(), id)
        return 200, loc.to_dict(locacoes.hoje()), None

    return app


def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    try:
        application = Application()
    except ConfigError as err:
        sys.exit(f'Erro de configuração: {err}')
    log.info('Locadora Web iniciando em http://0.0.0.0:%s/portal', application.config.port)
    run(create_app(application), server='waitress', host='0.0.0.0',
        port=application.config.port, threads=4, quiet=True)


if __name__ == '__main__':
    main()
else:
    # Para servidores WSGI externos: `waitress-serve route:app`
    try:
        app = create_app()
    except ConfigError as err:
        sys.exit(f'Erro de configuração: {err}')
