"""Interface de terminal (menu). Depende de Locadora (serviço) para tudo."""
from datetime import date, datetime

from .excecoes import LocadoraError
from .servicos import Locadora


# ---------- entrada de dados ----------
def ler_texto(msg, obrigatorio=True, padrao=None):
    while True:
        sufixo = f" [{padrao}]" if padrao else ""
        valor = input(f"{msg}{sufixo}: ").strip()
        if not valor and padrao is not None:
            return padrao
        if valor or not obrigatorio:
            return valor
        print("  Campo obrigatório.")


def ler_int(msg, minimo=None):
    while True:
        try:
            valor = int(input(f"{msg}: ").strip())
        except ValueError:
            print("  Digite um número inteiro.")
            continue
        if minimo is not None and valor < minimo:
            print(f"  O valor deve ser pelo menos {minimo}.")
            continue
        return valor


def ler_sim_nao(msg):
    return input(f"{msg} (s/n): ").strip().lower() in ("s", "sim")


def ler_data(msg):
    """Aceita dd/mm/aaaa; Enter = hoje."""
    while True:
        texto = input(f"{msg} (dd/mm/aaaa, Enter = hoje): ").strip()
        if not texto:
            return date.today()
        try:
            return datetime.strptime(texto, "%d/%m/%Y").date()
        except ValueError:
            print("  Data inválida.")


def mostrar(titulo, itens):
    print(f"\n--- {titulo} ---")
    if not itens:
        print("  (nenhum registro)")
    for i in itens:
        print(" ", i)


def executar(acao):
    """Executa uma ação mostrando erros de negócio sem derrubar o programa."""
    try:
        acao()
    except LocadoraError as e:
        print(f"\n  ERRO: {e}")


# ---------- telas ----------
class Menu:
    def __init__(self, locadora: Locadora):
        self.loc = locadora

    def _opcao(self, titulo, opcoes):
        print(f"\n===== {titulo} =====")
        for chave, (texto, _) in opcoes.items():
            print(f" {chave} - {texto}")
        return input("Escolha: ").strip()

    def _submenu(self, titulo, opcoes):
        while True:
            escolha = self._opcao(titulo, opcoes)
            if escolha == "0":
                return
            if escolha in opcoes:
                executar(opcoes[escolha][1])
            else:
                print("  Opção inválida.")

    def principal(self):
        opcoes = {
            "1": ("Clientes", self.menu_clientes),
            "2": ("Funcionários", self.menu_funcionarios),
            "3": ("Acervo (filmes e jogos)", self.menu_acervo),
            "4": ("Locações e devoluções", self.menu_locacoes),
            "0": ("Sair", None),
        }
        while True:
            escolha = self._opcao("LOCADORA - MENU PRINCIPAL", opcoes)
            if escolha == "0":
                print("Até logo!")
                return
            if escolha in opcoes:
                opcoes[escolha][1]()
            else:
                print("  Opção inválida.")

    # ----- clientes -----
    def menu_clientes(self):
        self._submenu("CLIENTES", {
            "1": ("Cadastrar", self.cadastrar_cliente),
            "2": ("Listar", lambda: mostrar("Clientes", self.loc.listar_clientes())),
            "3": ("Atualizar", self.atualizar_cliente),
            "4": ("Remover", lambda: self.loc.remover_cliente(ler_int("ID do cliente", 1)) or print("  Removido.")),
            "0": ("Voltar", None),
        })

    def _dados_cliente(self, atual=None):
        return (ler_texto("Nome", padrao=atual.nome if atual else None),
                ler_texto("CPF", padrao=atual.cpf if atual else None),
                ler_texto("Rua", padrao=atual.endereco.rua if atual else None),
                ler_texto("Número", obrigatorio=False, padrao=atual.endereco.numero if atual else None),
                ler_texto("Cidade", padrao=atual.endereco.cidade if atual else None),
                ler_texto("UF", padrao=atual.endereco.uf if atual else None))

    def cadastrar_cliente(self):
        c = self.loc.cadastrar_cliente(*self._dados_cliente())
        print(f"  Cliente cadastrado: {c}")

    def atualizar_cliente(self):
        id = ler_int("ID do cliente", 1)
        atual = self.loc.clientes.buscar(id)
        if atual is None:
            print("  Cliente não encontrado.")
            return
        c = self.loc.atualizar_cliente(id, *self._dados_cliente(atual))
        print(f"  Atualizado: {c}")

    # ----- funcionários -----
    def menu_funcionarios(self):
        self._submenu("FUNCIONÁRIOS", {
            "1": ("Cadastrar", self.cadastrar_funcionario),
            "2": ("Listar", lambda: mostrar("Funcionários", self.loc.listar_funcionarios())),
            "3": ("Atualizar", self.atualizar_funcionario),
            "4": ("Remover", lambda: self.loc.remover_funcionario(ler_int("ID do funcionário", 1)) or print("  Removido.")),
            "0": ("Voltar", None),
        })

    def cadastrar_funcionario(self):
        f = self.loc.cadastrar_funcionario(ler_texto("Nome"), ler_texto("CPF"),
                                           ler_texto("Cargo", obrigatorio=False, padrao="Atendente"))
        print(f"  Funcionário cadastrado: {f}")

    def atualizar_funcionario(self):
        id = ler_int("ID do funcionário", 1)
        atual = self.loc.funcionarios.buscar(id)
        if atual is None:
            print("  Funcionário não encontrado.")
            return
        f = self.loc.atualizar_funcionario(id, ler_texto("Nome", padrao=atual.nome),
                                           ler_texto("CPF", padrao=atual.cpf),
                                           ler_texto("Cargo", padrao=atual.cargo))
        print(f"  Atualizado: {f}")

    # ----- acervo -----
    def menu_acervo(self):
        self._submenu("ACERVO", {
            "1": ("Cadastrar filme", self.cadastrar_filme),
            "2": ("Cadastrar jogo", self.cadastrar_jogo),
            "3": ("Listar todos", lambda: mostrar("Acervo", self.loc.listar_itens())),
            "4": ("Listar disponíveis", lambda: mostrar("Disponíveis", self.loc.listar_itens(True))),
            "5": ("Remover item", lambda: self.loc.remover_item(ler_int("ID do item", 1)) or print("  Removido.")),
            "0": ("Voltar", None),
        })

    def cadastrar_filme(self):
        f = self.loc.cadastrar_filme(ler_texto("Título"), ler_int("Ano", 1888), ler_texto("Gênero", obrigatorio=False),
                                     ler_int("Duração (min)", 1), ler_sim_nao("É lançamento?"))
        print(f"  Filme cadastrado: {f}")

    def cadastrar_jogo(self):
        j = self.loc.cadastrar_jogo(ler_texto("Título"), ler_int("Ano", 1950), ler_texto("Plataforma"))
        print(f"  Jogo cadastrado: {j}")

    # ----- locações -----
    def menu_locacoes(self):
        self._submenu("LOCAÇÕES", {
            "1": ("Nova locação", self.nova_locacao),
            "2": ("Devolver", self.devolver),
            "3": ("Locações em aberto", lambda: mostrar("Em aberto", self.loc.listar_locacoes(True))),
            "4": ("Histórico completo", lambda: mostrar("Histórico", self.loc.listar_locacoes())),
            "5": ("Ver recibo", lambda: print(self.loc.recibo(ler_int("ID da locação", 1)))),
            "0": ("Voltar", None),
        })

    def nova_locacao(self):
        mostrar("Clientes", self.loc.listar_clientes())
        cliente_id = ler_int("ID do cliente", 1)
        mostrar("Funcionários", self.loc.listar_funcionarios())
        func_id = ler_int("ID do funcionário", 1)
        mostrar("Itens disponíveis", self.loc.listar_itens(True))
        pedidos = []
        while True:
            item_id = ler_int("ID do item", 1)
            dias = ler_int("Quantidade de dias", 1)
            pedidos.append((item_id, dias))
            if not ler_sim_nao("Adicionar outro item?"):
                break
        locacao = self.loc.alugar(cliente_id, func_id, pedidos, ler_data("Data da locação"))
        print("\n  Locação registrada!\n")
        print(self.loc.recibo(locacao.id))

    def devolver(self):
        mostrar("Em aberto", self.loc.listar_locacoes(True))
        id = ler_int("ID da locação", 1)
        print(self.loc.devolver(id, ler_data("Data da devolução")))
