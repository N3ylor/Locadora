"""READ na interface web, templates e integração API <-> página."""
from conftest import FILME


def test_banco_vazio_mostra_mensagem_e_total_zero(auth):
    html = auth.get('/banco').text
    assert 'Nenhum filme cadastrado' in html and 'Total: 0 registros' in html
    assert '<table' not in html


def test_banco_lista_filmes_vindos_do_banco_de_dados(auth):
    auth.post_json('/api/filmes', FILME)
    html = auth.get('/banco').text
    for texto in ('Matrix', 'Ficção científica', '5,00', 'Total: 1 registro<'):
        assert texto in html
    for cabecalho in ('ID', 'Título', 'Gênero', 'Diária'):
        assert '<th' in html and cabecalho in html
    assert 'Nenhum filme cadastrado' not in html


def test_fluxo_completo_create_read_delete(auth):
    """Reproduz a demonstração do enunciado: cURL altera, a página reflete."""
    assert 'Matrix' not in auth.get('/banco').text
    fid = auth.post_json('/api/filmes', FILME).json['id']
    assert 'Matrix' in auth.get('/banco').text
    auth.put_json(f'/api/filmes/{fid}', {**FILME, 'titulo': 'Matrix Reloaded'})
    html = auth.get('/banco').text
    assert 'Matrix Reloaded' in html
    auth.delete(f'/api/filmes/{fid}')
    assert 'Matrix' not in auth.get('/banco').text


def test_html_e_escapado_contra_xss(auth):
    auth.post_json('/api/filmes', {**FILME, 'titulo': '<script>alert(1)</script>', 'genero': '"><img src=x>'})
    html = auth.get('/banco').text
    assert '<script>alert(1)' not in html and '&lt;script&gt;' in html
    assert '<img src=x>' not in html


def test_valor_formatado_em_real(auth):
    auth.post_json('/api/filmes', {**FILME, 'valor_diaria': 1234.5})
    assert '1234,50' in auth.get('/banco').text


def test_persistencia_apos_reiniciar_a_aplicacao(config):
    """Equivale a reiniciar o contêiner: nova Application sobre o mesmo arquivo SQLite."""
    from app.controllers.application import Application
    from route import create_app
    from webtest import TestApp
    from conftest import PASSWORD, USER

    c1 = TestApp(create_app(Application(config)))
    c1.post('/portal', {'username': USER, 'password': PASSWORD})
    c1.post_json('/api/filmes', FILME)

    c2 = TestApp(create_app(Application(config)))  # "reinício"
    c2.post('/portal', {'username': USER, 'password': PASSWORD})
    assert 'Matrix' in c2.get('/banco').text
    assert c2.get('/api/filmes').json['total'] == 1


def test_helper_do_bmvc_continua_disponivel(client):
    resp = client.get('/helper')
    assert resp.status_int == 200 and 'BMVC' in resp.text


def test_render_desconhecido_cai_no_helper(ctl):
    assert 'BMVC' in ctl.render('inexistente')


def test_home_redireciona_conforme_login(client, auth):
    anon = client.__class__(client.app)
    assert anon.get('/').headers['Location'].endswith('/portal')
    assert auth.get('/').headers['Location'].endswith('/banco')


def test_arquivos_estaticos(client):
    assert client.get('/static/css/locadora.css').status_int == 200
    assert client.get('/static/../route.py', expect_errors=True).status_int in (400, 403, 404)
    assert client.get('/static/%2e%2e/route.py', expect_errors=True).status_int in (400, 403, 404)


def test_pagina_inexistente_tem_erro_html_amigavel(client):
    resp = client.get('/nada', expect_errors=True)
    assert resp.status_int == 404 and 'Voltar ao início' in resp.text


def test_health(client):
    assert client.get('/health').json == {'status': 'ok'}
