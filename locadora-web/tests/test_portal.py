"""Recurso Portal: login, logout, sessão e segurança."""
from conftest import PASSWORD, USER, make_config

from app.controllers.application import Application
from route import create_app
from webtest import TestApp


def login(client, username=USER, password=PASSWORD, **kw):
    return client.post('/portal', {'username': username, 'password': password}, expect_errors=True, **kw)


def test_pagina_de_login_tem_formulario(client):
    html = client.get('/portal').text
    for trecho in ('name="username"', 'name="password"', 'type="password"', 'Entrar'):
        assert trecho in html


def test_login_valido_redireciona_para_banco_e_define_cookie_seguro(client):
    resp = login(client)
    assert resp.status_int == 302 and resp.headers['Location'].endswith('/banco')
    cookie = resp.headers['Set-Cookie']
    assert 'session_id=' in cookie and 'HttpOnly' in cookie and 'samesite=strict' in cookie.lower()


def test_credenciais_invalidas_sao_rejeitadas_com_mensagem(client):
    for user, pwd in [(USER, 'errada'), ('naoexiste', PASSWORD), (USER.upper(), PASSWORD)]:
        resp = login(client, user, pwd)
        assert resp.status_int == 401
        assert 'Usuário ou senha incorretos.' in resp.text
        assert 'session_id' not in resp.headers.get('Set-Cookie', '')


def test_campos_vazios_sao_rejeitados(client):
    assert login(client, '', '').status_int == 400


def test_senha_com_acentos_autentica(tmp_path):
    cfg = make_config(tmp_path, admin_password='açaí-Ção-123')
    c = TestApp(create_app(Application(cfg)))
    assert login(c, USER, 'açaí-Ção-123').status_int == 302


def test_banco_exige_autenticacao(client):
    resp = client.get('/banco')
    assert resp.status_int == 302 and resp.headers['Location'].endswith('/portal')


def test_banco_apos_login_mostra_usuario_e_titulo(auth):
    html = auth.get('/banco').text
    assert 'Catálogo de filmes' in html and USER in html and 'Sair' in html


def test_logout_encerra_a_sessao(auth):
    resp = auth.post('/logout')
    assert resp.status_int == 302 and resp.headers['Location'].endswith('/portal')
    assert auth.get('/banco').status_int == 302


def test_logout_invalida_o_token_no_servidor(auth):
    token = auth.cookies['session_id']
    auth.post('/logout')
    auth.set_cookie('session_id', token)  # reenvia o cookie antigo
    assert auth.get('/banco').status_int == 302


def test_cookie_forjado_nao_autentica(client):
    client.set_cookie('session_id', 'qualquer-coisa')
    assert client.get('/banco').status_int == 302


def test_portal_redireciona_quem_ja_esta_logado(auth):
    assert auth.get('/portal').status_int == 302


def test_senha_nao_fica_em_texto_puro_no_banco(ctl):
    with ctl.database.connection() as db:
        senha = db.execute('SELECT password FROM users').fetchone()['password']
    assert PASSWORD not in senha and senha.startswith('pbkdf2_sha256$')


def test_trocar_a_senha_no_ambiente_atualiza_o_hash(tmp_path):
    Application(make_config(tmp_path))
    nova = Application(make_config(tmp_path, admin_password='nova-senha-456'))
    assert nova.models.check_user(USER, 'nova-senha-456')
    assert not nova.models.check_user(USER, PASSWORD)


def test_sessao_expira_no_servidor(tmp_path):
    relogio = [0.0]
    ctl = Application(make_config(tmp_path, session_ttl=60))
    ctl.models._clock = lambda: relogio[0]
    sid = ctl.models.check_user(USER, PASSWORD)
    assert ctl.models.get_username_by_session_id(sid) == USER
    relogio[0] = 61
    assert ctl.models.get_username_by_session_id(sid) is None


def test_bloqueio_temporario_apos_falhas_repetidas(tmp_path):
    c = TestApp(create_app(Application(make_config(tmp_path, login_max_attempts=3))))
    for _ in range(3):
        assert login(c, USER, 'errada').status_int == 401
    resp = login(c, USER, PASSWORD)  # mesmo com a senha certa, está bloqueado
    assert resp.status_int == 429 and 'Muitas tentativas' in resp.text


def test_cabecalhos_de_seguranca(client):
    h = client.get('/portal').headers
    assert h['X-Content-Type-Options'] == 'nosniff' and h['X-Frame-Options'] == 'DENY'
    assert "default-src 'self'" in h['Content-Security-Policy'] and h['Cache-Control'] == 'no-store'
