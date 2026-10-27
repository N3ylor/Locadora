import functools
import math
import tkinter as tk
import tkinter.font as tkfont
from datetime import date, datetime
from tkinter import messagebox, simpledialog, ttk

from .excecoes import LocadoraError, ValidacaoError
from .models import Filme, Jogo

CORES = {
    "fundo": "#14161b",
    "painel": "#1e2128",
    "campo": "#2a2e38",
    "borda": "#3a3f4c",
    "texto": "#e6e8ee",
    "sub": "#9aa1b0",
    "destaque": "#8ea2ff",
    "primaria": "#5b7cfa",
    "primaria_escura": "#4766e0",
    "sucesso": "#2f9e5b",
    "sucesso_escura": "#278a4e",
    "perigo": "#e5484d",
    "perigo_escura": "#c93a3f",
    "neutro": "#3a3f4c",
    "neutro_escura": "#4a5060",
}
FONTE = "Segoe UI"


def aplicar_estilos(raiz):
    estilo = ttk.Style(raiz)
    estilo.theme_use("clam")
    c = CORES
    raiz.configure(bg=c["fundo"])
    estilo.configure(".", font=(FONTE, 10), foreground=c["texto"], background=c["fundo"])
    estilo.configure("TFrame", background=c["fundo"])
    estilo.configure("TLabel", background=c["fundo"])
    estilo.configure("Painel.TFrame", background=c["painel"])
    estilo.configure("Campo.TFrame", background=c["campo"])
    estilo.configure("Painel.TLabel", background=c["painel"])
    for nome, fundo in (("TCheckbutton", c["fundo"]), ("Painel.TCheckbutton", c["painel"])):
        estilo.configure(nome, background=fundo, foreground=c["texto"], focuscolor=fundo,
                         indicatorbackground=c["campo"], indicatorforeground=c["texto"],
                         bordercolor=c["borda"], lightcolor=c["campo"], darkcolor=c["campo"])
        estilo.map(nome, background=[("active", fundo)],
                   indicatorbackground=[("selected", c["primaria"]), ("active", c["borda"])])
    estilo.configure("PainelSecao.TLabel", background=c["painel"],
                     font=(FONTE, 13, "bold"), foreground=c["destaque"])
    estilo.configure("Titulo.TLabel", font=(FONTE, 24, "bold"), foreground=c["destaque"])
    estilo.configure("Sub.TLabel", font=(FONTE, 11), foreground=c["sub"])
    estilo.configure("Resumo.TLabel", background=c["painel"], foreground=c["destaque"],
                     font=(FONTE, 10, "bold"), anchor="center")

    estilo.configure("Treeview", rowheight=28, background=c["campo"], fieldbackground=c["campo"],
                     foreground=c["texto"], borderwidth=0, font=(FONTE, 10),
                     bordercolor=c["campo"], lightcolor=c["campo"], darkcolor=c["campo"])
    estilo.configure("Treeview.Heading", background=c["borda"], foreground=c["texto"],
                     font=(FONTE, 10, "bold"), padding=7, relief="flat", borderwidth=0)
    estilo.map("Treeview", background=[("selected", c["primaria"])],
               foreground=[("selected", "white")])
    estilo.map("Treeview.Heading", background=[("active", c["neutro_escura"])])

    campo = dict(fieldbackground=c["campo"], foreground=c["texto"], bordercolor=c["borda"],
                 lightcolor=c["campo"], darkcolor=c["campo"], padding=6)
    estilo.configure("TEntry", insertcolor=c["texto"], **campo)
    estilo.map("TEntry", bordercolor=[("focus", c["primaria"])],
               lightcolor=[("focus", c["primaria"])], darkcolor=[("focus", c["primaria"])])
    estilo.configure("TCombobox", background=c["campo"], arrowcolor=c["texto"],
                     selectbackground=c["campo"], selectforeground=c["texto"], **campo)
    estilo.map("TCombobox", fieldbackground=[("readonly", c["campo"])],
               foreground=[("readonly", c["texto"])],
               selectbackground=[("readonly", c["campo"])],
               selectforeground=[("readonly", c["texto"])],
               background=[("active", c["borda"]), ("readonly", c["campo"])],
               bordercolor=[("focus", c["primaria"])])
    raiz.option_add("*TCombobox*Listbox.background", c["campo"])
    raiz.option_add("*TCombobox*Listbox.foreground", c["texto"])
    raiz.option_add("*TCombobox*Listbox.selectBackground", c["primaria"])
    raiz.option_add("*TCombobox*Listbox.selectForeground", "white")
    raiz.option_add("*TCombobox*Listbox.font", (FONTE, 10))

    estilo.configure("TScrollbar", background=c["borda"], troughcolor=c["painel"],
                     bordercolor=c["painel"], arrowcolor=c["texto"], lightcolor=c["borda"],
                     darkcolor=c["borda"], relief="flat", gripcount=0)
    estilo.map("TScrollbar", background=[("active", c["neutro_escura"])])


def cor_fundo(pai):
    """Descobre a cor de fundo de um widget para os cantos arredondados combinarem."""
    try:
        nome = pai.cget("style") or pai.winfo_class()
        return ttk.Style().lookup(nome, "background") or CORES["fundo"]
    except tk.TclError:
        try:
            return pai.cget("bg")
        except tk.TclError:
            return CORES["fundo"]


def retangulo_redondo(canvas, x1, y1, x2, y2, raio, **opcoes):
    raio = max(0, min(raio, (x2 - x1) / 2, (y2 - y1) / 2))
    pontos = []
    # (centro x, centro y, ângulo inicial) de cada canto, no sentido horário
    for cx, cy, inicio in ((x2 - raio, y1 + raio, -90), (x2 - raio, y2 - raio, 0),
                           (x1 + raio, y2 - raio, 90), (x1 + raio, y1 + raio, 180)):
        for passo in range(0, 91, 10):
            angulo = math.radians(inicio + passo)
            pontos += [cx + raio * math.cos(angulo), cy + raio * math.sin(angulo)]
    return canvas.create_polygon(pontos, **opcoes)


class Painel(tk.Frame):
    """Cartão com cantos arredondados. Coloque os widgets dentro de `.conteudo`."""

    def __init__(self, pai, padding=16, raio=16, tom="painel"):
        super().__init__(pai, bg=cor_fundo(pai), bd=0, highlightthickness=0)
        self.raio = raio
        self.tom = CORES[tom]
        self.desenho = tk.Canvas(self, bg=cor_fundo(pai), highlightthickness=0, bd=0)
        self.desenho.place(x=0, y=0, relwidth=1, relheight=1)
        self.conteudo = ttk.Frame(self, style=f"{tom.capitalize()}.TFrame")
        self.conteudo.pack(fill="both", expand=True, padx=padding, pady=padding)
        self.desenho.bind("<Configure>", self.redesenhar)

    def redesenhar(self, evento):
        self.desenho.delete("all")
        retangulo_redondo(self.desenho, 1, 1, evento.width - 1, evento.height - 1, self.raio,
                          fill=self.tom, outline=CORES["borda"])


class Botao(tk.Canvas):
    """Botão com cantos arredondados (mesmos parâmetros do ttk.Button usado antes)."""
    TONS = {"Primario": ("primaria", "primaria_escura"), "Sucesso": ("sucesso", "sucesso_escura"),
            "Perigo": ("perigo", "perigo_escura"), "Neutro": ("neutro", "neutro_escura")}

    def __init__(self, pai, text="", style="Primario.TButton", command=None):
        self.fonte = tkfont.Font(family=FONTE, size=10, weight="bold")
        super().__init__(pai, height=38, width=self.fonte.measure(text) + 40, bg=cor_fundo(pai),
                         highlightthickness=0, bd=0, cursor="hand2", takefocus=1)
        normal, destaque = self.TONS[style.split(".")[0]]
        self.cor_normal, self.cor_destaque = CORES[normal], CORES[destaque]
        self.cor_atual = self.cor_normal
        self.rotulo = text
        self.comando = command
        self.bind("<Configure>", lambda _e: self.desenhar())
        self.bind("<Enter>", lambda _e: self.pintar(self.cor_destaque))
        self.bind("<Leave>", lambda _e: self.pintar(self.cor_normal))
        self.bind("<ButtonPress-1>", lambda _e: self.pintar(self.cor_destaque))
        self.bind("<ButtonRelease-1>", self.soltar)
        self.bind("<Return>", lambda _e: self.disparar())
        self.bind("<space>", lambda _e: self.disparar())

    def pintar(self, cor):
        self.cor_atual = cor
        self.desenhar()

    def desenhar(self):
        self.delete("all")
        larg, alt = self.winfo_width(), self.winfo_height()
        retangulo_redondo(self, 1, 1, larg - 1, alt - 1, 14, fill=self.cor_atual, outline=self.cor_atual)
        self.create_text(larg / 2, alt / 2, text=self.rotulo, fill="white", font=self.fonte)

    def soltar(self, evento):
        self.pintar(self.cor_normal)
        if 0 <= evento.x <= self.winfo_width() and 0 <= evento.y <= self.winfo_height():
            self.disparar()

    def disparar(self):
        if self.comando:
            self.comando()


def com_tratamento_de_erro(funcao):
    @functools.wraps(funcao)
    def interna(*args, **kwargs):
        try:
            return funcao(*args, **kwargs)
        except LocadoraError as erro:
            messagebox.showerror("Atenção", str(erro))
        except ValueError:
            messagebox.showerror("Atenção", "Confira os números digitados.")
    return interna


def hoje_texto():
    return date.today().strftime("%d/%m/%Y")


def ler_data(texto):
    try:
        return datetime.strptime(texto.strip(), "%d/%m/%Y").date()
    except ValueError:
        raise ValidacaoError("Data inválida. Use o formato dd/mm/aaaa.")


def criar_tabela(pai, colunas, altura=14):
    quadro = Painel(pai, padding=8, raio=14, tom="campo")
    interior = quadro.conteudo
    tabela = ttk.Treeview(interior, columns=[c[0] for c in colunas], show="headings",
                          selectmode="browse", height=altura)
    for id_coluna, titulo, largura in colunas:
        tabela.heading(id_coluna, text=titulo, anchor="w")
        tabela.column(id_coluna, width=largura, anchor="w")
    barra = ttk.Scrollbar(interior, orient="vertical", command=tabela.yview)
    tabela.configure(yscrollcommand=barra.set)
    tabela.pack(side="left", fill="both", expand=True)
    barra.pack(side="right", fill="y")
    return quadro, tabela


def mostrar_recibo(mestre, texto):
    janela = tk.Toplevel(mestre)
    janela.title("Recibo")
    janela.configure(bg=CORES["fundo"])
    cartao = Painel(janela, padding=14)
    cartao.pack(padx=16, pady=(16, 8))
    caixa = tk.Text(cartao.conteudo, font=("Consolas", 11), width=50, height=22, bg=CORES["painel"],
                    fg=CORES["texto"], insertbackground=CORES["texto"], relief="flat", bd=0,
                    highlightthickness=0)
    caixa.insert("1.0", texto)
    caixa.configure(state="disabled")
    caixa.pack()
    Botao(janela, text="Fechar", style="Primario.TButton", command=janela.destroy).pack(pady=(0, 16))


class JanelaBase(tk.Toplevel):
    def __init__(self, mestre, titulo, locadora, tamanho):
        super().__init__(mestre)
        self.loc = locadora
        self.title(titulo)
        self.geometry(tamanho)
        self.minsize(700, 460)
        self.configure(bg=CORES["fundo"])
        ttk.Label(self, text=titulo, style="Titulo.TLabel").pack(anchor="w", padx=20, pady=(16, 8))


class JanelaCrud(JanelaBase):
    titulo = ""
    campos = []
    colunas = []

    def __init__(self, mestre, locadora):
        super().__init__(mestre, self.titulo, locadora, "900x560")
        self.geometry(f"900x{min(680, self.winfo_screenheight() - 120)}")
        self.id_atual = None
        self.vars = {}
        self.padroes = {}
        corpo = ttk.Frame(self)
        corpo.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        painel_form = Painel(corpo, padding=16)
        painel_form.pack(side="left", fill="y", padx=(0, 16))
        formulario = painel_form.conteudo
        botoes = ttk.Frame(formulario, style="Painel.TFrame")   # rodapé fixo, sempre visível
        botoes.pack(side="bottom", fill="x", pady=(12, 0))
        for chave, rotulo, tipo in self.campos:
            ttk.Label(formulario, text=rotulo, style="Painel.TLabel").pack(anchor="w", pady=(4, 0))
            if tipo == "check":
                self.padroes[chave] = False
                self.vars[chave] = tk.BooleanVar(value=False)
                ttk.Checkbutton(formulario, text="Sim", variable=self.vars[chave],
                                style="Painel.TCheckbutton").pack(anchor="w")
            elif tipo:
                self.padroes[chave] = tipo[0]
                self.vars[chave] = tk.StringVar(value=tipo[0])
                ttk.Combobox(formulario, textvariable=self.vars[chave], values=tipo,
                             state="readonly", width=26).pack(anchor="w")
            else:
                self.padroes[chave] = ""
                self.vars[chave] = tk.StringVar(value="")
                ttk.Entry(formulario, textvariable=self.vars[chave], width=28).pack(anchor="w")
        Botao(botoes, text="Salvar", style="Primario.TButton", command=self.salvar).pack(fill="x", pady=3)
        Botao(botoes, text="Limpar", style="Neutro.TButton", command=self.limpar).pack(fill="x", pady=3)
        Botao(botoes, text="Excluir", style="Perigo.TButton", command=self.excluir).pack(fill="x", pady=3)
        quadro, self.tabela = criar_tabela(corpo, self.colunas)
        quadro.pack(side="left", fill="both", expand=True)
        self.tabela.bind("<<TreeviewSelect>>", self.ao_selecionar)
        self.atualizar_tabela()

    def valores(self):
        return {chave: var.get() for chave, var in self.vars.items()}

    def atualizar_tabela(self):
        self.tabela.delete(*self.tabela.get_children())
        for objeto in self.listar():
            self.tabela.insert("", "end", iid=str(objeto.id), values=self.linha(objeto))

    def ao_selecionar(self, _evento=None):
        selecionado = self.tabela.selection()
        if not selecionado:
            return
        self.id_atual = int(selecionado[0])
        for chave, valor in self.para_dict(self.buscar(self.id_atual)).items():
            self.vars[chave].set(valor)

    def limpar(self):
        self.id_atual = None
        for chave, var in self.vars.items():
            var.set(self.padroes[chave])
        self.tabela.selection_remove(*self.tabela.selection())

    @com_tratamento_de_erro
    def salvar(self):
        dados = self.valores()
        if self.id_atual is None:
            self.cadastrar(dados)
        else:
            self.atualizar(self.id_atual, dados)
        self.limpar()
        self.atualizar_tabela()
        messagebox.showinfo("Pronto", "Salvo com sucesso.")

    @com_tratamento_de_erro
    def excluir(self):
        if self.id_atual is None:
            messagebox.showinfo("Excluir", "Clique em uma linha da tabela primeiro.")
            return
        if not messagebox.askyesno("Excluir", "Deseja mesmo excluir o registro selecionado?"):
            return
        self.remover(self.id_atual)
        self.limpar()
        self.atualizar_tabela()


class JanelaClientes(JanelaCrud):
    titulo = "Clientes"
    campos = [("nome", "Nome", None), ("cpf", "CPF", None), ("rua", "Rua", None),
              ("numero", "Número", None), ("cidade", "Cidade", None), ("uf", "UF", None)]
    colunas = [("id", "ID", 50), ("nome", "Nome", 180), ("cpf", "CPF", 110), ("cidade", "Cidade", 120)]

    def listar(self):
        return self.loc.listar_clientes()

    def buscar(self, id):
        return self.loc.clientes.buscar(id)

    def linha(self, c):
        return (c.id, c.nome, c.cpf, f"{c.endereco.cidade}/{c.endereco.uf}")

    def para_dict(self, c):
        return {"nome": c.nome, "cpf": c.cpf, "rua": c.endereco.rua, "numero": c.endereco.numero,
                "cidade": c.endereco.cidade, "uf": c.endereco.uf}

    def cadastrar(self, d):
        self.loc.cadastrar_cliente(d["nome"], d["cpf"], d["rua"], d["numero"], d["cidade"], d["uf"])

    def atualizar(self, id, d):
        self.loc.atualizar_cliente(id, d["nome"], d["cpf"], d["rua"], d["numero"], d["cidade"], d["uf"])

    def remover(self, id):
        self.loc.remover_cliente(id)


class JanelaFuncionarios(JanelaCrud):
    titulo = "Funcionários"
    campos = [("nome", "Nome", None), ("cpf", "CPF", None), ("cargo", "Cargo", None)]
    colunas = [("id", "ID", 50), ("nome", "Nome", 200), ("cpf", "CPF", 110), ("cargo", "Cargo", 130)]

    def listar(self):
        return self.loc.listar_funcionarios()

    def buscar(self, id):
        return self.loc.funcionarios.buscar(id)

    def linha(self, f):
        return (f.id, f.nome, f.cpf, f.cargo)

    def para_dict(self, f):
        return {"nome": f.nome, "cpf": f.cpf, "cargo": f.cargo}

    def cadastrar(self, d):
        self.loc.cadastrar_funcionario(d["nome"], d["cpf"], d["cargo"])

    def atualizar(self, id, d):
        self.loc.atualizar_funcionario(id, d["nome"], d["cpf"], d["cargo"])

    def remover(self, id):
        self.loc.remover_funcionario(id)


class JanelaAcervo(JanelaCrud):
    titulo = "Acervo"
    campos = [("tipo", "Tipo", ["Filme", "Jogo"]), ("titulo", "Título", None), ("ano", "Ano", None),
              ("genero", "Gênero (só filme)", None), ("duracao", "Duração em minutos (só filme)", None),
              ("lancamento", "Lançamento (só filme)", "check"), ("plataforma", "Plataforma (só jogo)", None)]
    colunas = [("id", "ID", 45), ("tipo", "Tipo", 60), ("titulo", "Título", 170), ("ano", "Ano", 50),
               ("detalhe", "Detalhe", 150), ("situacao", "Situação", 85)]

    def listar(self):
        return self.loc.listar_itens()

    def buscar(self, id):
        return self.loc.itens.buscar(id)

    def linha(self, item):
        if isinstance(item, Filme):
            tipo, detalhe = "Filme", f"{item.genero} - {item.duracao_min} min"
        else:
            tipo, detalhe = "Jogo", item.plataforma
        situacao = "Disponível" if item.disponivel else "Alugado"
        return (item.id, tipo, item.titulo, item.ano, detalhe, situacao)

    def para_dict(self, item):
        if isinstance(item, Filme):
            return {"tipo": "Filme", "titulo": item.titulo, "ano": item.ano, "genero": item.genero,
                    "duracao": item.duracao_min, "lancamento": item.lancamento, "plataforma": ""}
        return {"tipo": "Jogo", "titulo": item.titulo, "ano": item.ano, "genero": "",
                "duracao": "", "lancamento": False, "plataforma": item.plataforma}

    def montar(self, d):
        if d["tipo"] == "Filme":
            return Filme(d["titulo"], int(d["ano"]), d["genero"], int(d["duracao"]), d["lancamento"])
        return Jogo(d["titulo"], int(d["ano"]), d["plataforma"])

    def cadastrar(self, d):
        if d["tipo"] == "Filme":
            self.loc.cadastrar_filme(d["titulo"], int(d["ano"]), d["genero"], int(d["duracao"]), d["lancamento"])
        else:
            self.loc.cadastrar_jogo(d["titulo"], int(d["ano"]), d["plataforma"])

    def atualizar(self, id, d):
        self.loc.atualizar_item(id, self.montar(d))

    def remover(self, id):
        self.loc.remover_item(id)


class JanelaLocacoes(JanelaBase):
    def __init__(self, mestre, locadora):
        super().__init__(mestre, "Locações e devoluções", locadora, "1150x660")
        altura = min(660, self.winfo_screenheight() - 120)
        self.geometry(f"1150x{altura}")
        self.minsize(900, 420)
        self.carrinho = []
        corpo = ttk.Frame(self)
        corpo.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        painel_lateral = Painel(corpo, padding=8)
        painel_lateral.pack(side="left", fill="y", padx=(0, 16))
        lateral = painel_lateral.conteudo

        # rodapé fixo: sempre visível, mesmo com a janela pequena
        rodape = ttk.Frame(lateral, style="Painel.TFrame", padding=(16, 8, 16, 16))
        rodape.pack(side="bottom", fill="x")

        # parte de cima com rolagem
        canvas = tk.Canvas(lateral, bg=CORES["painel"], highlightthickness=0)
        barra_lateral = ttk.Scrollbar(lateral, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=barra_lateral.set)
        barra_lateral.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        esquerda = ttk.Frame(canvas, style="Painel.TFrame", padding=16)
        canvas.create_window((0, 0), window=esquerda, anchor="nw")
        esquerda.bind("<Configure>", lambda _e: canvas.configure(
            scrollregion=canvas.bbox("all"), width=esquerda.winfo_reqwidth()))

        def rolar(evento):
            canvas.yview_scroll(int(-evento.delta / 120), "units")
        canvas.bind("<Enter>", lambda _e: canvas.bind_all("<MouseWheel>", rolar))
        canvas.bind("<Leave>", lambda _e: canvas.unbind_all("<MouseWheel>"))
        ttk.Label(esquerda, text="Nova locação", style="PainelSecao.TLabel").pack(anchor="w")
        self.var_cliente, self.cb_cliente = self.criar_combo(esquerda, "Cliente")
        self.var_funcionario, self.cb_funcionario = self.criar_combo(esquerda, "Funcionário")
        self.var_item, self.cb_item = self.criar_combo(esquerda, "Item disponível")
        ttk.Label(esquerda, text="Dias", style="Painel.TLabel").pack(anchor="w", pady=(6, 0))
        self.var_dias = tk.StringVar(value="1")
        ttk.Entry(esquerda, textvariable=self.var_dias, width=8).pack(anchor="w")
        Botao(esquerda, text="Adicionar ao carrinho", style="Neutro.TButton",
                   command=self.adicionar_ao_carrinho).pack(fill="x", pady=(10, 4))
        quadro, self.tabela_carrinho = criar_tabela(esquerda, [("item", "Item", 230), ("dias", "Dias", 50)], altura=4)
        quadro.pack(fill="x", pady=4)
        Botao(esquerda, text="Esvaziar carrinho", style="Neutro.TButton",
                   command=self.limpar_carrinho).pack(fill="x", pady=(2, 8))
        ttk.Label(rodape, text="Data da locação (dd/mm/aaaa)", style="Painel.TLabel").pack(anchor="w")
        self.var_data = tk.StringVar(value=hoje_texto())
        ttk.Entry(rodape, textvariable=self.var_data, width=14).pack(anchor="w")
        Botao(rodape, text="Registrar locação", style="Sucesso.TButton",
                   command=self.registrar).pack(fill="x", pady=(10, 4))
        Botao(rodape, text="Voltar ao início", style="Neutro.TButton",
                   command=self.destroy).pack(fill="x")

        direita = ttk.Frame(corpo)
        direita.pack(side="left", fill="both", expand=True)
        self.so_abertas = tk.BooleanVar(value=True)
        ttk.Checkbutton(direita, text="Mostrar só as locações em aberto", variable=self.so_abertas,
                        command=self.atualizar_tabela).pack(anchor="w", pady=(0, 8))
        colunas = [("id", "ID", 45), ("data", "Data", 90), ("cliente", "Cliente", 130),
                   ("itens", "Itens", 190), ("total", "Total", 80), ("situacao", "Situação", 130)]
        quadro, self.tabela = criar_tabela(direita, colunas, altura=15)
        quadro.pack(fill="both", expand=True)
        botoes = ttk.Frame(direita)
        botoes.pack(fill="x", pady=(10, 0))
        Botao(botoes, text="Devolver", style="Sucesso.TButton", command=self.devolver).pack(side="left")
        Botao(botoes, text="Ver recibo", style="Primario.TButton", command=self.ver_recibo).pack(side="left", padx=8)

        self.carregar_opcoes()
        self.atualizar_tabela()

    @staticmethod
    def criar_combo(pai, rotulo):
        ttk.Label(pai, text=rotulo, style="Painel.TLabel").pack(anchor="w", pady=(6, 0))
        var = tk.StringVar(value="")
        combo = ttk.Combobox(pai, textvariable=var, state="readonly", width=34)
        combo.pack(anchor="w")
        return var, combo

    @staticmethod
    def pegar_id(texto, nome):
        if not texto:
            raise ValidacaoError(f"Escolha o {nome}.")
        return int(texto.split(" - ")[0])

    def carregar_opcoes(self):
        self.cb_cliente["values"] = [f"{c.id} - {c.nome}" for c in self.loc.listar_clientes()]
        self.cb_funcionario["values"] = [f"{f.id} - {f.nome}" for f in self.loc.listar_funcionarios()]
        self.cb_item["values"] = [f"{i.id} - {i.titulo} (R$ {i.valor_diaria:.2f}/dia)"
                                  for i in self.loc.listar_itens(True)]
        self.var_item.set("")

    def desenhar_carrinho(self):
        self.tabela_carrinho.delete(*self.tabela_carrinho.get_children())
        for posicao, (_, dias, texto) in enumerate(self.carrinho):
            self.tabela_carrinho.insert("", "end", iid=str(posicao), values=(texto, dias))

    @com_tratamento_de_erro
    def adicionar_ao_carrinho(self):
        item_id = self.pegar_id(self.var_item.get(), "item")
        dias = int(self.var_dias.get())
        if dias <= 0:
            raise ValidacaoError("Os dias devem ser maiores que zero.")
        if any(i == item_id for i, _, _ in self.carrinho):
            raise ValidacaoError("Esse item já está no carrinho.")
        self.carrinho.append((item_id, dias, self.var_item.get()))
        self.var_item.set("")
        self.desenhar_carrinho()

    def limpar_carrinho(self):
        self.carrinho = []
        self.desenhar_carrinho()

    @com_tratamento_de_erro
    def registrar(self):
        cliente_id = self.pegar_id(self.var_cliente.get(), "cliente")
        funcionario_id = self.pegar_id(self.var_funcionario.get(), "funcionário")
        pedidos = [(item_id, dias) for item_id, dias, _ in self.carrinho]
        locacao = self.loc.alugar(cliente_id, funcionario_id, pedidos, ler_data(self.var_data.get()))
        self.limpar_carrinho()
        self.carregar_opcoes()
        self.atualizar_tabela()
        mostrar_recibo(self, self.loc.recibo(locacao.id))

    def atualizar_tabela(self):
        self.tabela.delete(*self.tabela.get_children())
        for l in self.loc.listar_locacoes(self.so_abertas.get()):
            situacao = f"Devolvida em {l.data_devolucao:%d/%m/%Y}" if l.devolvida else "Em aberto"
            itens = ", ".join(il.item.titulo for il in l.itens)
            self.tabela.insert("", "end", iid=str(l.id), values=(
                l.id, f"{l.data_locacao:%d/%m/%Y}", l.cliente.nome, itens, f"R$ {l.total:.2f}", situacao))

    def locacao_selecionada(self):
        selecionado = self.tabela.selection()
        if not selecionado:
            raise ValidacaoError("Clique em uma locação da tabela primeiro.")
        return int(selecionado[0])

    @com_tratamento_de_erro
    def devolver(self):
        id = self.locacao_selecionada()
        texto = simpledialog.askstring("Devolução", "Data da devolução (dd/mm/aaaa):",
                                       initialvalue=hoje_texto(), parent=self)
        if texto is None:
            return
        recibo = self.loc.devolver(id, ler_data(texto))
        self.carregar_opcoes()
        self.atualizar_tabela()
        mostrar_recibo(self, recibo)

    @com_tratamento_de_erro
    def ver_recibo(self):
        mostrar_recibo(self, self.loc.recibo(self.locacao_selecionada()))


class App(tk.Tk):
    def __init__(self, locadora):
        super().__init__()
        self.loc = locadora
        self.janelas = {}
        self.title("Locadora")
        self.geometry("520x580")
        self.resizable(False, False)
        aplicar_estilos(self)
        ttk.Label(self, text="Locadora", style="Titulo.TLabel").pack(pady=(28, 0))
        ttk.Label(self, text="Filmes e jogos", style="Sub.TLabel").pack(pady=(0, 18))
        caixa_resumo = Painel(self, padding=8)
        caixa_resumo.pack(fill="x", padx=40, pady=(0, 18))
        self.resumo = ttk.Label(caixa_resumo.conteudo, text="", style="Resumo.TLabel", padding=6,
                                anchor="center")
        self.resumo.pack(fill="x")
        menu = ttk.Frame(self)
        menu.pack(fill="x", padx=40)
        telas = (("Clientes", JanelaClientes), ("Funcionários", JanelaFuncionarios),
                 ("Acervo", JanelaAcervo), ("Locações e devoluções", JanelaLocacoes))
        for texto, classe in telas:
            Botao(menu, text=texto, style="Primario.TButton",
                       command=lambda c=classe: self.abrir(c)).pack(fill="x", pady=5)
        Botao(menu, text="Sair", style="Perigo.TButton", command=self.destroy).pack(fill="x", pady=(14, 0))
        self.atualizar_resumo()
        self.bind("<FocusIn>", lambda _evento: self.atualizar_resumo())

    def atualizar_resumo(self):
        clientes = len(self.loc.listar_clientes())
        itens = len(self.loc.listar_itens())
        abertas = len(self.loc.listar_locacoes(True))
        self.resumo.configure(text=f"{clientes} clientes   |   {itens} itens   |   {abertas} locações em aberto")

    def abrir(self, classe):
        janela = self.janelas.get(classe)
        if janela is not None and janela.winfo_exists():
            janela.lift()
            janela.focus_force()
            return
        self.janelas[classe] = classe(self, self.loc)
