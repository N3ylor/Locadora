# Locadora — Interface Gráfica

![Plataforma](https://img.shields.io/badge/plataforma-Windows%20%7C%20macOS%20%7C%20Linux-4f7d9c?style=flat-square) ![Linguagem](https://img.shields.io/badge/python-3.9%2B-blue?style=flat-square) ![Interface](https://img.shields.io/badge/interface-Tkinter-orange?style=flat-square) ![Dependências](https://img.shields.io/badge/depend%C3%AAncias-nenhuma-brightgreen?style=flat-square)

Esta é a versão da Locadora com **janelas e botões**, feita com **Tkinter** — que já vem junto com o Python. É a mesma lógica da versão [terminal](../terminal), com uma camada visual por cima: o arquivo `gui.py` conversa com a classe `Locadora` exatamente como o menu de terminal faz.

## Como rodar

Dentro desta pasta:

```
python main_gui.py
```

Precisa do Python 3.9 ou mais novo e nada além disso. No Linux, se o Tkinter não estiver instalado, instale o pacote do sistema (no Ubuntu/Debian: `sudo apt install python3-tk`).

Na primeira vez, cadastre um funcionário, um cliente e alguns filmes ou jogos antes de fazer uma locação. O banco é criado sozinho, no arquivo `locadora.db`, na mesma pasta.

O menu de terminal continua disponível aqui também, e usa o **mesmo banco**:

```
python main.py
```

Para rodar os testes:

```
python -m unittest discover -s tests -t .
```

## Funcionalidades

A tela inicial mostra um resumo (quantidade de clientes, itens e locações em aberto) e abre as quatro áreas do sistema, cada uma em sua própria janela:

- **Clientes, Funcionários e Acervo**: tela com formulário e tabela. Clique numa linha para editar, use **Salvar**, **Limpar** e **Excluir** (com confirmação). No acervo, filmes e jogos são cadastrados e editados na mesma janela — o tipo de um item já cadastrado não pode ser trocado.
- **Locações e devoluções**:
  - monte um **carrinho** com vários itens, cada um com o seu prazo em dias, e registre a locação de uma vez;
  - **devolva** pela tabela, informando a data, e veja a multa calculada;
  - abra o **recibo** de qualquer locação;
  - filtre para mostrar só as locações em aberto.
- Erros de validação e de regra de negócio aparecem em caixas de mensagem, sem fechar o programa.

##  Regras de negócio

| Item | Diária | Multa por dia de atraso |
| --- | --- | --- |
| Filme | R$ 6,00 | R$ 2,00 |
| Filme lançamento | R$ 9,00 | R$ 3,00 |
| Jogo | R$ 10,00 (10% de desconto a partir de 5 dias) | R$ 4,00 |

Cada cliente pode ficar com no máximo 3 itens alugados ao mesmo tempo.

## Design do projeto

A interface não toma nenhuma decisão: valida o que foi digitado, chama a classe `Locadora` e mostra o resultado. Todas as regras ficam em `servicos.py` e nos modelos — por isso as duas interfaces, terminal e gráfica, se comportam do mesmo jeito.

Dentro de `gui.py`, as janelas reaproveitam código por herança: `JanelaCrud` é a base de `JanelaClientes`, `JanelaFuncionarios` e `JanelaAcervo`, e cada uma só declara os seus campos e colunas. As cores e os estilos dos botões ficam centralizados em um único lugar (`aplicar_estilos`).

O diagrama de classes do domínio está em [`UML.md`](UML.md).

##  Estrutura

```
interface-grafica/
├── locadora/
│   ├── models/
│   │   ├── pessoa.py       # Pessoa (abstrata), Cliente e Funcionario
│   │   ├── endereco.py     # Endereco (parte do Cliente)
│   │   ├── item.py         # Item (abstrata), Filme e Jogo
│   │   ├── locacao.py      # Locacao e ItemLocacao
│   │   └── recibo.py       # Recibo: monta o texto da locação
│   ├── database.py         # Conexão e tabelas do SQLite
│   ├── repositorios.py     # Salvar e buscar cada entidade
│   ├── servicos.py         # Regras de negócio (classe Locadora)
│   ├── excecoes.py         # Erros do sistema
│   ├── gui.py              # Janelas, botões e estilos (Tkinter)
│   └── menu.py             # Menu de terminal
├── tests/                  # 44 testes automáticos (unittest)
├── main_gui.py             # Abre a versão com janelas
├── main.py                 # Abre a versão de terminal
└── UML.md                  # Diagrama de classes (Mermaid)
```

##  Diferença para a versão terminal

Além da interface, esta pasta traz uma evolução nas regras: a classe `Locadora` ganhou `atualizar_item`, que permite editar filmes e jogos já cadastrados (mantendo a disponibilidade e bloqueando a troca de tipo) — algo que o formulário do acervo precisa e que o menu de terminal original não tinha. Por isso esta versão tem 2 testes a mais.

## Autor

Neylor Cruz — [@N3ylim](https://github.com/N3ylim)

José Antônio - [https://github.com/ja2462445-bit]
