"""Locação, devolução, limites, desconto e multa (com relógio controlável)."""
from datetime import date, timedelta

import pytest
from conftest import FILME, PASSWORD, USER, make_config
from webtest import TestApp

from app.controllers.application import Application
from route import create_app

JOGO = {'titulo': 'The Witcher 3', 'plataforma': 'PC', 'valor_diaria': 10.0}
INICIO = date(2026, 11, 5)


class Mundo:
    """Aplicação com relógio manual e helpers para logar admin/clientes."""

    def __init__(self, tmp_path):
        self.hoje = INICIO
        self.ctl = Application(make_config(tmp_path), relogio=lambda: self.hoje)
        self.wsgi = create_app(self.ctl)
        self.admin = self.entrar(USER, PASSWORD)

    def entrar(self, usuario, senha):
        c = TestApp(self.wsgi)
        assert c.post('/portal', {'username': usuario, 'password': senha}).status_int in (302, 303)
        return c

    def cliente(self, username='neylor'):
        self.admin.post_json('/api/clientes', {'username': username, 'nome': username.title(), 'senha': 'senha-12345'})
        return self.entrar(username, 'senha-12345')

    def avancar(self, dias):
        self.hoje += timedelta(days=dias)


@pytest.fixture
def mundo(tmp_path):
    m = Mundo(tmp_path)
    m.admin.post_json('/api/filmes', FILME)    # filme 1: R$ 5,00/dia
    m.admin.post_json('/api/jogos', JOGO)      # jogo 1: R$ 10,00/dia
    return m


def alugar(c, tipo='filme', item_id=1, dias=3, **kw):
    return c.post_json('/api/locacoes', {'tipo': tipo, 'item_id': item_id, 'dias': dias}, expect_errors=True, **kw)


# ---------- alugar ----------
def test_cliente_aluga_filme_e_valor_e_prazo_corretos(mundo):
    resp = alugar(mundo.cliente(), 'filme', 1, 3)
    assert resp.status_int == 201 and resp.headers['Location'] == '/api/locacoes/1'
    d = resp.json
    assert (d['status'], d['dias'], d['valor_total'], d['multa'], d['total']) == ('aberta', 3, 15.0, 0.0, 15.0)
    assert d['data_locacao'] == '2026-11-05' and d['data_prevista'] == '2026-11-08' and d['titulo'] == 'Matrix'


def test_jogo_ate_4_dias_sem_desconto_e_a_partir_de_5_com_10_por_cento(mundo):
    c = mundo.cliente()
    assert alugar(c, 'jogo', 1, 4).json['valor_total'] == 40.0
    c.post('/api/locacoes/1/devolucao')
    assert alugar(c, 'jogo', 1, 5).json['valor_total'] == 45.0   # 50 - 10%


def test_filme_nao_tem_desconto_em_prazo_longo(mundo):
    assert alugar(mundo.cliente(), 'filme', 1, 10).json['valor_total'] == 50.0


def test_item_alugado_fica_indisponivel_para_outro_cliente(mundo):
    alugar(mundo.cliente('ana'), 'filme', 1, 2)
    resp = alugar(mundo.cliente('bia'), 'filme', 1, 2)
    assert resp.status_int == 409 and 'já está alugado' in resp.json['erro']


def test_limite_de_3_itens_por_cliente(mundo):
    for i in range(2, 4):
        mundo.admin.post_json('/api/filmes', {**FILME, 'titulo': f'Filme {i}'})
    c = mundo.cliente()
    for i in (1, 2, 3):
        assert alugar(c, 'filme', i).status_int == 201
    resp = alugar(c, 'jogo', 1)
    assert resp.status_int == 409 and 'Limite de 3' in resp.json['erro']
    c.post('/api/locacoes/1/devolucao')            # devolver libera uma vaga
    assert alugar(c, 'jogo', 1).status_int == 201


def test_limite_vale_por_cliente_nao_global(mundo):
    for i in range(2, 5):
        mundo.admin.post_json('/api/filmes', {**FILME, 'titulo': f'Filme {i}'})
    a, b = mundo.cliente('ana'), mundo.cliente('bia')
    for i in (1, 2, 3):
        alugar(a, 'filme', i)
    assert alugar(b, 'filme', 4).status_int == 201


@pytest.mark.parametrize('corpo', [
    {'tipo': 'livro', 'item_id': 1, 'dias': 3}, {'item_id': 1, 'dias': 3}, {'tipo': 'filme', 'dias': 3},
    {'tipo': 'filme', 'item_id': 1, 'dias': 0}, {'tipo': 'filme', 'item_id': 1, 'dias': 31},
    {'tipo': 'filme', 'item_id': 1, 'dias': -2}, {'tipo': 'filme', 'item_id': 1, 'dias': 2.5},
    {'tipo': 'filme', 'item_id': 1, 'dias': True}, {'tipo': 'filme', 'item_id': 'x', 'dias': 3},
    {'tipo': 'filme', 'item_id': 0, 'dias': 3}, {}])
def test_pedido_invalido_422(mundo, corpo):
    assert mundo.cliente().post_json('/api/locacoes', corpo, expect_errors=True).status_int == 422


def test_item_inexistente_404(mundo):
    c = mundo.cliente()
    assert alugar(c, 'filme', 99).status_int == 404
    assert alugar(c, 'jogo', 99999999999999999999999).status_int == 422   # fora do intervalo válido: nunca vira erro 500


def test_admin_nao_aluga_e_anonimo_nao_acessa(mundo):
    assert alugar(mundo.admin).status_int == 403
    anon = TestApp(mundo.wsgi)
    assert alugar(anon).status_int == 401
    assert anon.get('/api/locacoes', expect_errors=True).status_int == 401
    assert anon.post('/api/locacoes/1/devolucao', expect_errors=True).status_int == 401


# ---------- devolver e multa ----------
def test_devolucao_no_prazo_sem_multa(mundo):
    c = mundo.cliente()
    alugar(c, 'filme', 1, 3)
    mundo.avancar(3)                                # devolve no último dia: sem atraso
    d = c.post('/api/locacoes/1/devolucao').json
    assert (d['status'], d['dias_atraso'], d['multa'], d['total']) == ('devolvida', 0, 0.0, 15.0)
    assert d['data_devolucao'] == '2026-11-08'


def test_multa_de_filme_2_reais_por_dia_de_atraso(mundo):
    c = mundo.cliente()
    alugar(c, 'filme', 1, 2)
    mundo.avancar(5)                                # prazo 2 -> 3 dias de atraso
    d = c.post('/api/locacoes/1/devolucao').json
    assert (d['dias_atraso'], d['multa'], d['total']) == (3, 6.0, 16.0)   # 10 + 3*2


def test_multa_de_jogo_4_reais_por_dia_de_atraso(mundo):
    c = mundo.cliente()
    alugar(c, 'jogo', 1, 1)
    mundo.avancar(3)                                # 2 dias de atraso
    assert c.post('/api/locacoes/1/devolucao').json['multa'] == 8.0


def test_multa_em_aberto_cresce_e_congela_na_devolucao(mundo):
    c = mundo.cliente()
    alugar(c, 'filme', 1, 1)
    mundo.avancar(3)
    assert c.get('/api/locacoes/1').json['multa'] == 4.0     # 2 dias de atraso até hoje
    c.post('/api/locacoes/1/devolucao')
    mundo.avancar(10)
    assert c.get('/api/locacoes/1').json['multa'] == 4.0     # não muda depois de devolvida


def test_devolver_duas_vezes_409(mundo):
    c = mundo.cliente()
    alugar(c)
    c.post('/api/locacoes/1/devolucao')
    assert c.post('/api/locacoes/1/devolucao', expect_errors=True).status_int == 409


def test_item_volta_a_ficar_disponivel_apos_devolucao(mundo):
    ana = mundo.cliente('ana')
    alugar(ana)
    ana.post('/api/locacoes/1/devolucao')
    assert alugar(mundo.cliente('bia')).status_int == 201


def test_cliente_nao_devolve_nem_ve_locacao_de_outro(mundo):
    alugar(mundo.cliente('ana'))
    bia = mundo.cliente('bia')
    assert bia.post('/api/locacoes/1/devolucao', expect_errors=True).status_int == 404
    assert bia.get('/api/locacoes/1', expect_errors=True).status_int == 404
    assert bia.get('/api/locacoes').json['total'] == 0


def test_admin_ve_todas_e_pode_registrar_devolucao(mundo):
    alugar(mundo.cliente('ana'))
    assert mundo.admin.get('/api/locacoes').json['locacoes'][0]['username'] == 'ana'
    assert mundo.admin.post('/api/locacoes/1/devolucao').json['status'] == 'devolvida'


def test_locacao_inexistente_404(mundo):
    assert mundo.cliente().post('/api/locacoes/77/devolucao', expect_errors=True).status_int == 404


# ---------- integridade ----------
def test_nao_exclui_item_alugado_mas_exclui_apos_devolver(mundo):
    c = mundo.cliente()
    alugar(c, 'filme', 1)
    resp = mundo.admin.delete('/api/filmes/1', expect_errors=True)
    assert resp.status_int == 409 and 'alugado' in resp.json['erro']
    c.post('/api/locacoes/1/devolucao')
    assert mundo.admin.delete('/api/filmes/1').status_int == 200
    assert c.get('/api/locacoes/1').json['titulo'] == 'Matrix'   # histórico mantém o título


def test_preco_novo_nao_altera_locacao_existente(mundo):
    c = mundo.cliente()
    alugar(c, 'filme', 1, 2)
    mundo.admin.put_json('/api/filmes/1', {**FILME, 'valor_diaria': 50})
    assert c.get('/api/locacoes/1').json['valor_total'] == 10.0


def test_nao_exclui_cliente_com_locacao_em_aberto(mundo):
    c = mundo.cliente('ana')
    alugar(c)
    assert mundo.admin.delete('/api/clientes/ana', expect_errors=True).status_int == 409
    c.post('/api/locacoes/1/devolucao')
    assert mundo.admin.delete('/api/clientes/ana').status_int == 200


def test_locacoes_persistem_apos_reiniciar(tmp_path):
    m = Mundo(tmp_path)
    m.admin.post_json('/api/filmes', FILME)
    alugar(m.cliente(), 'filme', 1)
    m2 = Application(make_config(tmp_path), relogio=lambda: INICIO)
    assert [l.titulo for l in m2.locacoes_controller.repo.listar()] == ['Matrix']


def test_so_um_aluguel_em_aberto_por_item_no_banco(mundo):
    """A regra é garantida pelo próprio SQLite (índice único parcial), não só pelo código."""
    import sqlite3
    alugar(mundo.cliente())
    with mundo.ctl.database.connection() as db:
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("INSERT INTO locacoes(username,tipo,item_id,titulo,valor_diaria,dias,valor_total,"
                       "data_locacao,data_prevista) VALUES ('x','filme',1,'t',1,1,1,'2026-01-01','2026-01-02')")


# ---------- interface web ----------
def test_pagina_do_cliente_mostra_botao_alugar_e_regras(mundo):
    html = mundo.cliente().get('/cliente').text
    for trecho in ('Alugar', 'name="dias"', 'action="/cliente/alugar"', 'Matrix', 'The Witcher 3',
                   'Você não tem itens alugados', 'Máximo de 3 itens', '10% de desconto', 'R$ 2,00/dia', 'R$ 4,00/dia'):
        assert trecho in html


def test_alugar_pela_pagina_mostra_aviso_e_locacao_em_aberto(mundo):
    c = mundo.cliente()
    resp = c.post('/cliente/alugar', {'tipo': 'filme', 'item_id': '1', 'dias': '3'})
    assert resp.headers['Location'].endswith('/cliente?aviso=alugado')
    html = resp.follow().text
    assert 'Item alugado com sucesso' in html and 'Devolver' in html and '08/11/2026' in html
    assert '15,00' in html and '1 de 3 itens' in html and 'Alugado</span>' in html and 'Nenhum filme disponível' not in html


def test_item_alugado_nao_oferece_botao_para_outro_cliente(mundo):
    alugar(mundo.cliente('ana'))
    html = mundo.cliente('bia').get('/cliente').text
    assert 'Alugado</span>' in html and html.count('action="/cliente/alugar"') == 1   # só o jogo


def test_avisos_de_erro_na_pagina(mundo):
    for i in range(2, 4):
        mundo.admin.post_json('/api/filmes', {**FILME, 'titulo': f'F{i}'})
    c = mundo.cliente()
    for i in (1, 2, 3):
        c.post('/cliente/alugar', {'tipo': 'filme', 'item_id': str(i), 'dias': '2'})
    resp = c.post('/cliente/alugar', {'tipo': 'jogo', 'item_id': '1', 'dias': '2'})
    assert resp.headers['Location'].endswith('aviso=limite')
    html = resp.follow().text
    assert 'já está com 3 itens' in html and 'Limite atingido' in html and 'action="/cliente/alugar"' not in html
    bad = c.post('/cliente/alugar', {'tipo': 'jogo', 'item_id': '1', 'dias': '99'})
    assert bad.headers['Location'].endswith('aviso=invalido')


def test_aviso_desconhecido_na_url_e_ignorado_sem_refletir_texto(mundo):
    html = mundo.cliente().get('/cliente?aviso=<script>alert(1)</script>').text
    assert '<script>alert(1)' not in html and 'notice' not in html.split('<main>')[1].split('</main>')[0]


def test_devolver_pela_pagina_com_e_sem_multa(mundo):
    c = mundo.cliente()
    c.post('/cliente/alugar', {'tipo': 'filme', 'item_id': '1', 'dias': '1'})
    mundo.avancar(3)
    resp = c.post('/cliente/devolver/1')
    assert resp.headers['Location'].endswith('aviso=devolvido_multa')
    html = resp.follow().text
    assert 'com atraso' in html and 'Devolvida em 08/11/2026' in html and '4,00' in html and '9,00' in html
    c.post('/cliente/alugar', {'tipo': 'jogo', 'item_id': '1', 'dias': '2'})
    assert c.post('/cliente/devolver/2').headers['Location'].endswith('aviso=devolvido')


def test_devolver_locacao_de_outro_pela_pagina_e_negado(mundo):
    alugar(mundo.cliente('ana'))
    resp = mundo.cliente('bia').post('/cliente/devolver/1')
    assert resp.headers['Location'].endswith('aviso=nao_encontrado')
    assert mundo.admin.get('/api/locacoes/1').json['status'] == 'aberta'


def test_formularios_exigem_login(mundo):
    anon = TestApp(mundo.wsgi)
    assert anon.post('/cliente/alugar', {'tipo': 'filme', 'item_id': '1', 'dias': '1'}).headers['Location'].endswith('/portal')
    assert anon.post('/cliente/devolver/1').headers['Location'].endswith('/portal')


def test_painel_do_admin_lista_locacoes_com_cliente(mundo):
    html0 = mundo.admin.get('/banco').text
    assert 'Nenhuma locação registrada' in html0
    alugar(mundo.cliente('ana'), 'filme', 1, 2)
    html = mundo.admin.get('/banco').text
    assert '<th>Cliente</th>' in html and 'ana' in html and 'Matrix' in html and 'No prazo' in html
    assert 'Devolver' not in html            # admin devolve por cURL, o painel é de leitura
    mundo.avancar(5)
    assert 'Atrasada 3 dia(s)' in mundo.admin.get('/banco').text


def test_fuso_horario_invalido_cai_em_utc(tmp_path):
    ctl = Application(make_config(tmp_path, timezone='Nao/Existe'))
    assert isinstance(ctl.locacoes_controller.hoje(), date)


def test_banco_antigo_sem_tabela_de_locacoes_e_migrado(tmp_path):
    import sqlite3
    caminho = tmp_path / 'v2.db'
    con = sqlite3.connect(caminho)
    con.executescript("CREATE TABLE users (username TEXT PRIMARY KEY, password TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'cliente', nome TEXT NOT NULL DEFAULT '');"
                      "CREATE TABLE filmes (id INTEGER PRIMARY KEY AUTOINCREMENT, titulo TEXT, genero TEXT, valor_diaria REAL);"
                      "CREATE TABLE jogos (id INTEGER PRIMARY KEY AUTOINCREMENT, titulo TEXT, plataforma TEXT, valor_diaria REAL);"
                      "INSERT INTO filmes(titulo, genero, valor_diaria) VALUES ('Antigo','Drama',3);")
    con.commit(); con.close()
    ctl = Application(make_config(tmp_path, db_path=caminho))
    assert ctl.locacoes_controller.repo.listar() == []


def test_concorrencia_respeita_limite_e_item_unico(tmp_path):
    """Muitos pedidos simultâneos: no máximo 3 itens por cliente e 1 locação aberta por item."""
    import threading
    from app.controllers.errors import ApiError
    m = Mundo(tmp_path)
    for i in range(1, 11):
        m.admin.post_json('/api/filmes', {**FILME, 'titulo': f'Filme {i}'})   # filmes 1..10
    m.cliente('neylor')
    conta = m.ctl.models.find_user('neylor')
    resultados, trava = [], threading.Lock()

    def pedir(item_id):
        try:
            m.ctl.locacoes_controller.alugar(conta, {'tipo': 'filme', 'item_id': item_id, 'dias': 2})
            r = 'ok'
        except ApiError as e:
            r = e.codigo
        with trava:
            resultados.append(r)

    threads = [threading.Thread(target=pedir, args=(i,)) for i in range(1, 11)]
    [t.start() for t in threads]; [t.join() for t in threads]
    assert resultados.count('ok') == 3 and resultados.count('limite') == 7
    assert m.ctl.locacoes_controller.repo.contar_abertas('neylor') == 3

    # dois clientes disputando o mesmo item: só um vence
    m.cliente('ana'); m.cliente('bia')
    ana, bia = m.ctl.models.find_user('ana'), m.ctl.models.find_user('bia')
    disputa = []

    def disputar(c):
        try:
            m.ctl.locacoes_controller.alugar(c, {'tipo': 'filme', 'item_id': 10, 'dias': 1}); disputa.append('ok')
        except ApiError as e:
            disputa.append(e.codigo)
    ts = [threading.Thread(target=disputar, args=(c,)) for c in (ana, bia, ana, bia)]
    [t.start() for t in ts]; [t.join() for t in ts]
    assert disputa.count('ok') == 1
