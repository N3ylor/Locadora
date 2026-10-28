# Locadora — Terminal

![Plataforma](https://img.shields.io/badge/plataforma-universal-4f7d9c?style=flat-square) ![Linguagem](https://img.shields.io/badge/python-3.9%2B-blue?style=flat-square) ![Dependências](https://img.shields.io/badge/depend%C3%AAncias-nenhuma-brightgreen?style=flat-square)

Esta é a **base de tudo**: a versão em terminal da Locadora, sem interface gráfica e sem dependências externas — só Python puro e SQLite. É o coração do projeto, de onde nasceu a versão com [interface gráfica](../interface-grafica).

## Como rodar

Dentro desta pasta:

```
python3 main.py
```

O programa abre um menu interativo no terminal e continua rodando até você escolher sair. Funciona em qualquer sistema com Python 3.9 ou mais novo — Windows, macOS ou Linux — sem precisar instalar nada.

Na primeira vez, cadastre um funcionário, um cliente e alguns filmes ou jogos antes de fazer uma locação. O banco é criado sozinho, no arquivo `locadora.db`, na mesma pasta.

Para rodar os testes:

```
python3 -m unittest discover -s tests -t .
```

## Funcionalidades

- **Clientes** (com endereço) e **funcionários**: cadastrar, listar, atualizar e remover
- **Acervo** de filmes e jogos: cadastrar, listar (todos ou só os disponíveis) e remover
- **Nova locação** com vários itens de uma vez, cada um com o seu prazo
- **Devolução** com cálculo automático de multa por atraso e emissão de recibo
- Consulta de locações em aberto, histórico completo e recibos
- Datas no formato `dd/mm/aaaa` (Enter usa o dia de hoje)
- Erros de regra de negócio aparecem como mensagem, sem derrubar o programa

##  Regras de negócio

| Item | Diária | Multa por dia de atraso |
| --- | --- | --- |
| Filme | R$ 6,00 | R$ 2,00 |
| Filme lançamento | R$ 9,00 | R$ 3,00 |
| Jogo | R$ 10,00 (10% de desconto a partir de 5 dias) | R$ 4,00 |

Cada cliente pode ficar com no máximo 3 itens alugados ao mesmo tempo.

## Design do projeto

O projeto é dividido em camadas, e cada uma só conhece a de baixo:

- **`menu.py`** pergunta e mostra. Depende apenas da classe `Locadora`.
- **`servicos.py`** guarda as regras de negócio na classe `Locadora`, que se associa aos repositórios.
- **`repositorios.py`** salva e busca no SQLite, transformando linhas do banco em objetos do domínio.
- **`models/`** tem as classes da POO: herança (`Pessoa` → `Cliente`/`Funcionario`, `Item` → `Filme`/`Jogo`), polimorfismo (diária, multa e descrição de cada item), composição (`Cliente` com `Endereco`, `Locacao` com `ItemLocacao`), associação e dependência (`Recibo`).

O diagrama completo, com o mapa de onde cada relação está no código, fica em [`UML.md`](UML.md).

##  Estrutura

```
terminal/
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
│   └── menu.py             # Menu interativo do terminal
├── tests/                  # 42 testes automáticos (unittest)
├── main.py                 # Ponto de entrada
└── UML.md                  # Diagrama de classes (Mermaid)
```

##  Por que essa pasta importa

A versão com interface gráfica é construída em cima dessa lógica — a diferença é só a camada visual por cima. Se você quer entender **como a locadora realmente funciona por dentro**, sem se preocupar com botões e janelas, é aqui que a resposta está.

## Autor

Neylor Cruz — [@N3ylim](https://github.com/N3ylim)

José Antônio - [https://github.com/ja2462445-bit]
