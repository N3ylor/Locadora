"""Controlador do recurso Banco: páginas do catálogo (administrador e cliente)."""
from bottle import redirect, request, template

from app.models.locacao import DIAS_MAX, JOGO_DESCONTO, JOGO_DIAS_DESCONTO, LIMITE_ITENS, MULTA_DIA, formatar_valor

# Avisos da página do cliente. Textos fixos escolhidos por código (nunca refletem texto da URL).
AVISOS = {
    'alugado': ('ok', 'Item alugado com sucesso! Ele aparece em "Minhas locações".'),
    'devolvido': ('ok', 'Devolução registrada. Obrigado!'),
    'devolvido_multa': ('error', 'Devolução registrada com atraso: a multa foi somada ao total da locação.'),
    'limite': ('error', f'Você já está com {LIMITE_ITENS} itens alugados. Devolva um para alugar outro.'),
    'indisponivel': ('error', 'Este item já está alugado por outra pessoa.'),
    'invalido': ('error', f'Pedido inválido. Escolha de 1 a {DIAS_MAX} dias.'),
    'nao_encontrado': ('error', 'Item ou locação não encontrados.'),
    'ja_devolvida': ('error', 'Esta locação já foi devolvida.'),
    'somente_cliente': ('error', 'Apenas clientes podem alugar itens.'),
    'erro': ('error', 'Não foi possível concluir a operação.'),
}


class BancoController:
    def __init__(self, portal, filmes, jogos, clientes, locacoes):
        self.portal = portal        # PortalController (autenticação e perfis)
        self.filmes = filmes        # CatalogoController de filmes
        self.jogos = jogos          # CatalogoController de jogos
        self.clientes = clientes    # ClientesController
        self.locacoes = locacoes    # LocacoesController

    def banco(self):
        """Painel do administrador: filmes, jogos, clientes e locações (READ na interface web)."""
        conta = self.portal.current_account()
        if not conta:
            redirect('/portal')
        if not conta.is_admin:
            redirect('/cliente')
        return template('banco', user=conta.username, filmes=self.filmes.listar(),
                        jogos=self.jogos.listar(), clientes=self.clientes.listar(),
                        locacoes=self.locacoes.listar(conta), hoje=self.locacoes.hoje())

    def cliente(self):
        """Página do cliente: escolher itens, alugar, ver e devolver as próprias locações."""
        conta = self.portal.current_account()
        if not conta:
            redirect('/portal')
        if conta.is_admin:
            redirect('/banco')
        todas = self.locacoes.listar(conta)
        abertas = [l for l in todas if l.aberta]
        multas = ' · '.join(f'{t} R$ {formatar_valor(v)}/dia' for t, v in
                            (('filme', MULTA_DIA['filme']), ('jogo', MULTA_DIA['jogo'])))
        regras = (f'Máximo de {LIMITE_ITENS} itens ao mesmo tempo, por até {DIAS_MAX} dias. '
                  f'Jogos alugados por {JOGO_DIAS_DESCONTO} dias ou mais têm {int(JOGO_DESCONTO * 100)}% de desconto. '
                  f'Multa por dia de atraso: {multas}.')
        return template('cliente', nome=conta.nome, filmes=self.filmes.listar(),
                        jogos=self.jogos.listar(), abertas=abertas,
                        historico=[l for l in todas if not l.aberta],
                        indisponiveis=self.locacoes.repo.itens_abertos(),
                        pode_alugar=len(abertas) < LIMITE_ITENS, limite=LIMITE_ITENS, dias_max=DIAS_MAX,
                        hoje=self.locacoes.hoje(), regras=regras,
                        aviso=AVISOS.get(request.query.get('aviso')))
