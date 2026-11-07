"""Perfis (administrador x cliente), cadastro de clientes e recurso Jogos."""
import sqlite3

import pytest
from conftest import FILME, PASSWORD, USER, make_config
from webtest import TestApp

from app.controllers.application import Application
from route import create_app

JOGO = {'titulo': 'Zelda', 'plataforma': 'Nintendo Switch', 'valor_diaria': 8.5}
CLIENTE = {'username': 'maria', 'nome': 'Maria Silva', 'senha': 'senha-da-maria'}


@pytest.fixture
def cliente_http(auth, ctl):
    """Cliente HTTP autenticado como 'maria' (perfil cliente). `auth` (admin) cria a conta."""
    auth.post_json('/api/clientes', CLIENTE)
    c = TestApp(create_app(ctl))
    resp = c.post('/portal', {'username': 'maria', 'password': CLIENTE['senha']})
    assert resp.status_int == 303 or resp.status_int == 302
    return c


# ---------- redirecionamento por perfil ----------
def test_admin_e_levado_ao_banco(client):
    resp = client.post('/portal', {'username': USER, 'password': PASSWORD})
    assert resp.headers['Location'].endswith('/banco')


def test_cliente_e_levado_a_area_do_cliente(auth, ctl):
    auth.post_json('/api/clientes', CLIENTE)
    c = TestApp(create_app(ctl))
    resp = c.post('/portal', {'username': 'maria', 'password': CLIENTE['senha']})
    assert resp.headers['Location'].endswith('/cliente')
    assert c.get('/portal').headers['Location'].endswith('/cliente')
    assert c.get('/').headers['Location'].endswith('/cliente')


def test_cliente_nao_acessa_o_painel_do_admin(cliente_http):
    assert cliente_http.get('/banco').headers['Location'].endswith('/cliente')


def test_admin_nao_usa_a_pagina_do_cliente(auth):
    assert auth.get('/cliente').headers['Location'].endswith('/banco')


def test_anonimo_nao_acessa_area_do_cliente(client):
    assert client.get('/cliente').headers['Location'].endswith('/portal')


def test_pagina_do_cliente_mostra_nome_e_catalogo_sem_dados_de_admin(auth, cliente_http):
    auth.post_json('/api/filmes', FILME)
    auth.post_json('/api/jogos', JOGO)
    html = cliente_http.get('/cliente').text
    for texto in ('Maria Silva', 'Matrix', 'Zelda', 'Nintendo Switch', '8,50', 'Sair'):
        assert texto in html
    assert 'Clientes cadastrados' not in html and 'senha-da-maria' not in html


def test_pagina_do_cliente_vazia_mostra_mensagens(cliente_http):
    html = cliente_http.get('/cliente').text
    assert 'Nenhum filme disponível' in html and 'Nenhum jogo disponível' in html


# ---------- permissões da API ----------
def test_cliente_pode_ler_mas_nao_escrever_no_catalogo(auth, cliente_http):
    auth.post_json('/api/filmes', FILME)
    assert cliente_http.get('/api/filmes').json['total'] == 1
    assert cliente_http.get('/api/filmes/1').status_int == 200
    for resp in (cliente_http.post_json('/api/filmes', FILME, expect_errors=True),
                 cliente_http.put_json('/api/filmes/1', FILME, expect_errors=True),
                 cliente_http.delete('/api/filmes/1', expect_errors=True),
                 cliente_http.post_json('/api/jogos', JOGO, expect_errors=True)):
        assert resp.status_int == 403 and 'administradores' in resp.json['erro']
    assert auth.get('/api/filmes').json['total'] == 1  # nada foi alterado


@pytest.mark.parametrize('metodo,url', [('get', '/api/clientes'), ('get', '/api/clientes/maria'),
                                        ('delete', '/api/clientes/maria')])
def test_cliente_nao_acessa_api_de_clientes(cliente_http, metodo, url):
    assert getattr(cliente_http, metodo)(url, expect_errors=True).status_int == 403


def test_api_de_clientes_e_jogos_exige_login(client):
    assert client.get('/api/clientes', expect_errors=True).status_int == 401
    assert client.post_json('/api/clientes', CLIENTE, expect_errors=True).status_int == 401
    assert client.get('/api/jogos', expect_errors=True).status_int == 401
    assert client.post_json('/api/jogos', JOGO, expect_errors=True).status_int == 401


# ---------- CRUD de clientes (admin) ----------
def test_admin_cria_cliente_sem_expor_senha(auth):
    resp = auth.post_json('/api/clientes', CLIENTE)
    assert resp.status_int == 201 and resp.headers['Location'] == '/api/clientes/maria'
    assert resp.json == {'username': 'maria', 'nome': 'Maria Silva', 'role': 'cliente'}
    assert 'senha' not in resp.text and 'pbkdf2' not in resp.text


def test_username_e_normalizado_para_minusculas_e_duplicado_da_409(auth):
    assert auth.post_json('/api/clientes', {**CLIENTE, 'username': ' Maria '}).json['username'] == 'maria'
    assert auth.post_json('/api/clientes', CLIENTE, expect_errors=True).status_int == 409


def test_cliente_nao_pode_reutilizar_username_do_admin(auth):
    assert auth.post_json('/api/clientes', {**CLIENTE, 'username': 'ADMIN'}, expect_errors=True).status_int == 409


@pytest.mark.parametrize('campo,valor', [('username', 'a'), ('username', 'com espaço'), ('username', 'x/y'),
                                         ('username', None), ('nome', ''), ('nome', 5),
                                         ('senha', 'curta'), ('senha', None), ('senha', 'x' * 129)])
def test_cliente_validacao_422(auth, campo, valor):
    resp = auth.post_json('/api/clientes', {**CLIENTE, campo: valor}, expect_errors=True)
    assert resp.status_int == 422 and campo in resp.json['campos']
    assert auth.get('/api/clientes').json['total'] == 0


def test_listar_obter_atualizar_e_excluir_cliente(auth):
    auth.post_json('/api/clientes', CLIENTE)
    assert auth.get('/api/clientes').json['clientes'][0]['username'] == 'maria'
    assert auth.get('/api/clientes/Maria').json['nome'] == 'Maria Silva'
    assert auth.put_json('/api/clientes/maria', {'nome': 'Maria Souza'}).json['nome'] == 'Maria Souza'
    assert auth.delete('/api/clientes/maria').status_int == 200
    assert auth.get('/api/clientes/maria', expect_errors=True).status_int == 404
    assert auth.delete('/api/clientes/maria', expect_errors=True).status_int == 404
    assert auth.put_json('/api/clientes/maria', {'nome': 'x'}, expect_errors=True).status_int == 404


def test_atualizar_cliente_exige_algum_campo(auth):
    auth.post_json('/api/clientes', CLIENTE)
    assert auth.put_json('/api/clientes/maria', {}, expect_errors=True).status_int == 422
    assert auth.put_json('/api/clientes/maria', {'senha': 'curta'}, expect_errors=True).status_int == 422


def test_admin_nao_aparece_nem_e_alteravel_pela_api_de_clientes(auth):
    assert auth.get('/api/clientes').json['total'] == 0
    assert auth.get(f'/api/clientes/{USER}', expect_errors=True).status_int == 404
    assert auth.delete(f'/api/clientes/{USER}', expect_errors=True).status_int == 404
    assert auth.put_json(f'/api/clientes/{USER}', {'senha': 'outra-senha-1'}, expect_errors=True).status_int == 404


def test_trocar_senha_do_cliente_derruba_sessoes_e_vale_a_nova(auth, cliente_http, ctl):
    assert cliente_http.get('/cliente').status_int == 200
    auth.put_json('/api/clientes/maria', {'senha': 'nova-senha-123'})
    assert cliente_http.get('/cliente').status_int == 302  # sessão antiga caiu
    novo = TestApp(create_app(ctl))
    assert novo.post('/portal', {'username': 'maria', 'password': CLIENTE['senha']}, expect_errors=True).status_int == 401
    assert novo.post('/portal', {'username': 'maria', 'password': 'nova-senha-123'}).headers['Location'].endswith('/cliente')


def test_excluir_cliente_derruba_a_sessao_dele(auth, cliente_http):
    auth.delete('/api/clientes/maria')
    assert cliente_http.get('/cliente').headers['Location'].endswith('/portal')
    assert cliente_http.get('/api/filmes', expect_errors=True).status_int == 401


def test_painel_admin_lista_clientes_sem_senha(auth):
    auth.post_json('/api/clientes', CLIENTE)
    html = auth.get('/banco').text
    assert 'Clientes cadastrados' in html and 'maria' in html and 'Maria Silva' in html
    assert 'Total: 1 registro<' in html and 'pbkdf2' not in html and 'senha-da-maria' not in html


def test_senha_do_cliente_fica_em_hash(auth, ctl):
    auth.post_json('/api/clientes', CLIENTE)
    with ctl.database.connection() as db:
        senha = db.execute("SELECT password FROM users WHERE username='maria'").fetchone()['password']
    assert senha.startswith('pbkdf2_sha256$') and CLIENTE['senha'] not in senha


# ---------- jogos ----------
def test_crud_de_jogos(auth):
    resp = auth.post_json('/api/jogos', JOGO)
    assert resp.status_int == 201 and resp.json == {'id': 1, **JOGO}
    assert auth.get('/api/jogos').json['jogos'][0]['plataforma'] == 'Nintendo Switch'
    novo = {'titulo': 'Zelda TOTK', 'plataforma': 'Switch', 'valor_diaria': 9}
    assert auth.put_json('/api/jogos/1', novo).json['titulo'] == 'Zelda TOTK'
    assert auth.delete('/api/jogos/1').json['mensagem'] == 'Jogo 1 excluído.'
    assert auth.delete('/api/jogos/1', expect_errors=True).status_int == 404


@pytest.mark.parametrize('campo,valor', [('titulo', ''), ('plataforma', ''), ('plataforma', 'p' * 51),
                                         ('valor_diaria', -1), ('valor_diaria', True)])
def test_jogo_validacao_422(auth, campo, valor):
    resp = auth.post_json('/api/jogos', {**JOGO, campo: valor}, expect_errors=True)
    assert resp.status_int == 422 and campo in resp.json['campos']


def test_filme_nao_aceita_campo_plataforma_e_jogo_nao_aceita_genero(auth):
    assert auth.post_json('/api/jogos', {'titulo': 'x', 'genero': 'y', 'valor_diaria': 1}, expect_errors=True).status_int == 422


def test_jogos_e_filmes_sao_independentes(auth):
    auth.post_json('/api/filmes', FILME)
    assert auth.get('/api/jogos').json['total'] == 0
    assert auth.get('/api/jogos/1', expect_errors=True).status_int == 404


def test_painel_admin_mostra_jogos(auth):
    auth.post_json('/api/jogos', JOGO)
    html = auth.get('/banco').text
    assert 'Zelda' in html and 'Nintendo Switch' in html and 'Nenhum jogo cadastrado' not in html


# ---------- migração de bancos criados pela versão anterior ----------
def test_banco_antigo_sem_perfil_e_migrado(tmp_path):
    db_path = tmp_path / 'antigo.db'
    con = sqlite3.connect(db_path)
    con.executescript('''
        CREATE TABLE users (username TEXT PRIMARY KEY, password TEXT NOT NULL);
        CREATE TABLE filmes (id INTEGER PRIMARY KEY AUTOINCREMENT, titulo TEXT NOT NULL,
                             genero TEXT NOT NULL, valor_diaria REAL NOT NULL);
        INSERT INTO filmes(titulo, genero, valor_diaria) VALUES ('Antigo', 'Drama', 3.5);
        INSERT INTO users VALUES ('admin', 'lixo');
    ''')
    con.commit(); con.close()
    c = TestApp(create_app(Application(make_config(tmp_path, db_path=db_path))))
    assert c.post('/portal', {'username': USER, 'password': PASSWORD}).headers['Location'].endswith('/banco')
    assert 'Antigo' in c.get('/banco').text  # dados antigos preservados
