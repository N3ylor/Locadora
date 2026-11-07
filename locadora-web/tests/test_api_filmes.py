"""Recurso Banco: CRUD via API JSON (equivalente aos comandos cURL)."""
import pytest
from conftest import FILME

JSON = {'Content-Type': 'application/json'}


def post(c, dados=FILME, **kw):
    return c.post_json('/api/filmes', dados, expect_errors=True, **kw)


# ---------- autenticação ----------
@pytest.mark.parametrize('metodo,url', [('get', '/api/filmes'), ('get', '/api/filmes/1'),
                                        ('post', '/api/filmes'), ('put', '/api/filmes/1'),
                                        ('delete', '/api/filmes/1')])
def test_api_exige_autenticacao(client, metodo, url):
    resp = getattr(client, metodo)(url, expect_errors=True)
    assert resp.status_int == 401
    assert resp.content_type == 'application/json' and 'erro' in resp.json


# ---------- CREATE ----------
def test_create_retorna_201_location_e_grava(auth):
    resp = post(auth)
    assert resp.status_int == 201
    assert resp.json == {'id': 1, **FILME}
    assert resp.headers['Location'] == '/api/filmes/1'
    assert auth.get('/api/filmes/1').json['titulo'] == 'Matrix'


def test_create_aceita_inteiro_e_texto_numerico(auth):
    assert post(auth, {**FILME, 'valor_diaria': 5}).json['valor_diaria'] == 5.0
    assert post(auth, {**FILME, 'valor_diaria': '7.50'}).json['valor_diaria'] == 7.5


def test_create_remove_espacos_das_pontas(auth):
    assert post(auth, {**FILME, 'titulo': '  Alien  '}).json['titulo'] == 'Alien'


@pytest.mark.parametrize('campo,valor', [
    ('titulo', ''), ('titulo', '   '), ('titulo', None), ('titulo', 123), ('titulo', 'x' * 201),
    ('titulo', 'com\nquebra'), ('genero', ''), ('genero', None), ('genero', 'g' * 101),
    ('valor_diaria', None), ('valor_diaria', -1), ('valor_diaria', 10000), ('valor_diaria', 'abc'),
    ('valor_diaria', True), ('valor_diaria', [1]), ('valor_diaria', 1.999), ('valor_diaria', 'NaN'),
    ('valor_diaria', 'Infinity'), ('valor_diaria', 1e400),
])
def test_create_rejeita_dados_invalidos_com_422(auth, campo, valor):
    resp = post(auth, {**FILME, campo: valor})
    assert resp.status_int == 422
    assert campo in resp.json['campos']
    assert auth.get('/api/filmes').json['total'] == 0  # nada foi gravado


def test_create_sem_campos_lista_todos_os_erros(auth):
    assert set(post(auth, {}).json['campos']) == {'titulo', 'genero', 'valor_diaria'}


@pytest.mark.parametrize('corpo', [[], 'texto', 42, None])
def test_create_exige_objeto_json(auth, corpo):
    assert post(auth, corpo).status_int == 422


def test_create_json_malformado_400(auth):
    resp = auth.post('/api/filmes', '{quebrado', headers=JSON, expect_errors=True)
    assert resp.status_int == 400 and resp.json['erro'] == 'JSON malformado.'


def test_create_sem_content_type_json_415(auth):
    resp = auth.post('/api/filmes', {'titulo': 'x'}, expect_errors=True)
    assert resp.status_int == 415


def test_create_corpo_grande_demais_413(auth):
    resp = auth.post('/api/filmes', '{"titulo":"' + 'a' * 70_000 + '"}', headers=JSON, expect_errors=True)
    assert resp.status_int == 413


# ---------- READ ----------
def test_read_lista_e_obtem(auth):
    post(auth); post(auth, {**FILME, 'titulo': 'Alien'})
    lista = auth.get('/api/filmes').json
    assert lista['total'] == 2 and [f['titulo'] for f in lista['filmes']] == ['Alien', 'Matrix']
    assert auth.get('/api/filmes/2').json['titulo'] == 'Alien'


@pytest.mark.parametrize('id', [999, 0, -5, 99999999999999999999999])
def test_read_inexistente_404(auth, id):
    assert auth.get(f'/api/filmes/{id}', expect_errors=True).status_int == 404


def test_id_nao_numerico_404(auth):
    assert auth.get('/api/filmes/abc', expect_errors=True).status_int == 404


# ---------- UPDATE ----------
def test_update_altera_o_registro(auth):
    post(auth)
    novo = {'titulo': 'Matrix Reloaded', 'genero': 'Ação', 'valor_diaria': 7.25}
    resp = auth.put_json('/api/filmes/1', novo)
    assert resp.status_int == 200 and resp.json == {'id': 1, **novo}
    assert auth.get('/api/filmes/1').json == {'id': 1, **novo}


def test_update_inexistente_404(auth):
    resp = auth.put_json('/api/filmes/42', FILME, expect_errors=True)
    assert resp.status_int == 404 and 'não encontrado' in resp.json['erro']


def test_update_id_gigante_404_sem_erro_500(auth):
    assert auth.put_json('/api/filmes/99999999999999999999999', FILME, expect_errors=True).status_int == 404


def test_update_dados_invalidos_422_e_preserva_o_original(auth):
    post(auth)
    resp = auth.put_json('/api/filmes/1', {**FILME, 'valor_diaria': -3}, expect_errors=True)
    assert resp.status_int == 422
    assert auth.get('/api/filmes/1').json['valor_diaria'] == 5.0


# ---------- DELETE ----------
def test_delete_remove_o_registro(auth):
    post(auth)
    resp = auth.delete('/api/filmes/1')
    assert resp.status_int == 200 and resp.json['id'] == 1
    assert auth.get('/api/filmes/1', expect_errors=True).status_int == 404
    assert auth.get('/api/filmes').json['total'] == 0


def test_delete_inexistente_404(auth):
    assert auth.delete('/api/filmes/7', expect_errors=True).status_int == 404


def test_delete_id_gigante_404_sem_erro_500(auth):
    assert auth.delete('/api/filmes/99999999999999999999999', expect_errors=True).status_int == 404


def test_delete_duas_vezes_segunda_404(auth):
    post(auth); auth.delete('/api/filmes/1')
    assert auth.delete('/api/filmes/1', expect_errors=True).status_int == 404


# ---------- erros genéricos da API em JSON ----------
def test_metodo_nao_permitido_em_json(auth):
    resp = auth.patch('/api/filmes/1', expect_errors=True)
    assert resp.status_int == 405 and resp.content_type == 'application/json'


def test_rota_inexistente_da_api_em_json(auth):
    resp = auth.get('/api/nada', expect_errors=True)
    assert resp.status_int == 404 and resp.json['erro']
