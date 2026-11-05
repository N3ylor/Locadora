import os
import sqlite3
from contextlib import contextmanager
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from locadora.database import Database
from locadora.servicos import Locadora
from locadora.models import Filme, Jogo
from locadora.excecoes import ValidacaoError, RegraNegocioError, NaoEncontradoError

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'locadora-local-altere-esta-chave')

@contextmanager
def sistema():
    db = Database(os.environ.get('DATABASE_PATH', 'locadora.db'))
    try:
        yield Locadora(db)
    finally:
        db.fechar()

def executar(funcao, destino):
    try:
        with sistema() as s:
            funcao(s)
        flash('Operação realizada com sucesso.', 'success')
    except (ValueError, TypeError, sqlite3.IntegrityError, ValidacaoError, RegraNegocioError, NaoEncontradoError) as e:
        flash(f'Não foi possível concluir: {e}', 'error')
    return redirect(url_for(destino))

@app.route('/')
def inicio():
    with sistema() as s:
        return render_template('index.html', clientes=len(s.listar_clientes()), funcionarios=len(s.listar_funcionarios()), itens=len(s.listar_itens()), locacoes=len(s.listar_locacoes()), abertas=len(s.listar_locacoes(True)))

@app.route('/clientes')
def clientes():
    with sistema() as s:
        return render_template('cadastros.html', titulo='Clientes', tipo='clientes', registros=s.listar_clientes())

@app.post('/clientes/salvar')
def salvar_cliente():
    f=request.form
    def acao(s):
        args=(f['nome'],f['cpf'],f['rua'],f['numero'],f['cidade'],f['uf'])
        if f.get('id'): s.atualizar_cliente(int(f['id']),*args)
        else: s.cadastrar_cliente(*args)
    return executar(acao,'clientes')

@app.post('/clientes/<int:id>/excluir')
def excluir_cliente(id):
    return executar(lambda s:s.remover_cliente(id),'clientes')

@app.route('/funcionarios')
def funcionarios():
    with sistema() as s:
        return render_template('cadastros.html', titulo='Funcionários', tipo='funcionarios', registros=s.listar_funcionarios())

@app.post('/funcionarios/salvar')
def salvar_funcionario():
    f=request.form
    def acao(s):
        args=(f['nome'],f['cpf'],f['cargo'])
        if f.get('id'): s.atualizar_funcionario(int(f['id']),*args)
        else: s.cadastrar_funcionario(*args)
    return executar(acao,'funcionarios')

@app.post('/funcionarios/<int:id>/excluir')
def excluir_funcionario(id):
    return executar(lambda s:s.remover_funcionario(id),'funcionarios')

@app.route('/acervo')
def acervo():
    with sistema() as s:
        return render_template('acervo.html', registros=s.listar_itens())

@app.post('/acervo/salvar')
def salvar_item():
    f=request.form
    def acao(s):
        tipo=f['tipo']
        if tipo=='filme':
            obj=Filme(f['titulo'],int(f['ano']),f['genero'],int(f['duracao_min']),f.get('lancamento')=='on')
        elif tipo=='jogo':
            obj=Jogo(f['titulo'],int(f['ano']),f['plataforma'])
        else: raise ValidacaoError('Tipo de item inválido')
        if f.get('id'): s.atualizar_item(int(f['id']),obj)
        elif tipo=='filme': s.cadastrar_filme(obj.titulo,obj.ano,obj.genero,obj.duracao_min,obj.lancamento)
        else: s.cadastrar_jogo(obj.titulo,obj.ano,obj.plataforma)
    return executar(acao,'acervo')

@app.post('/acervo/<int:id>/excluir')
def excluir_item(id):
    return executar(lambda s:s.remover_item(id),'acervo')

@app.route('/locacoes')
def locacoes():
    with sistema() as s:
        return render_template('locacoes.html', registros=s.listar_locacoes(request.args.get('abertas')=='1'), clientes=s.listar_clientes(), funcionarios=s.listar_funcionarios(), itens=s.listar_itens(True), apenas_abertas=request.args.get('abertas')=='1')

@app.post('/locacoes/criar')
def criar_locacao():
    f=request.form
    def acao(s):
        ids=f.getlist('item_id')
        dias=f.getlist('dias')
        pedidos=[(int(i),int(d)) for i,d in zip(ids,dias) if i.strip()]
        s.alugar(int(f['cliente_id']),int(f['funcionario_id']),pedidos)
    return executar(acao,'locacoes')

@app.post('/locacoes/<int:id>/devolver')
def devolver_locacao(id):
    return executar(lambda s:s.devolver(id),'locacoes')

@app.route('/locacoes/<int:id>/recibo')
def recibo(id):
    with sistema() as s:
        try: conteudo=s.recibo(id)
        except NaoEncontradoError: abort(404)
        return render_template('recibo.html', conteudo=conteudo, id=id)

@app.route('/health')
def health(): return {'status':'ok'}
