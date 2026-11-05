# Locadora Web — Flask + Docker

![Python](https://img.shields.io/badge/Python-3-blue) ![Flask](https://img.shields.io/badge/Backend-Flask-black) ![Docker](https://img.shields.io/badge/Container-Docker-2496ED) ![SQLite](https://img.shields.io/badge/Banco-SQLite-003b57)

Versão web do projeto [Locadora](../README.md), desenvolvida com **Flask** para disponibilizar as operações da locadora no navegador, preservando os modelos, repositórios, serviços e regras de negócio da aplicação original em Python.

## Funcionalidades

- **Painel inicial:** resumo de clientes, funcionários, itens e locações.
- **Clientes:** cadastro, listagem, edição e exclusão.
- **Funcionários:** cadastro, listagem, edição e exclusão.
- **Acervo:** gerenciamento de filmes e jogos.
- **Locações:** registro com vários itens e prazos individuais, respeitando o limite de três itens por cliente.
- **Devoluções:** processamento e cálculo de multas por atraso.
- **Consultas:** filtro de locações em aberto.
- **Recibos:** visualização e impressão.

## Tecnologias

| Tecnologia | Utilização |
| --- | --- |
| Python 3.12 | Linguagem da aplicação no contêiner |
| Flask | Rotas e interface web |
| HTML e CSS | Páginas e estilos |
| SQLite | Banco de dados local |
| Gunicorn | Servidor HTTP da aplicação |
| Docker e Docker Compose | Construção e execução do contêiner |

## Estrutura do projeto

```text
Locadora-Web/
├── app.py                 # Rotas Flask
├── locadora/              # Modelos, serviços e persistência
│   ├── models/
│   ├── database.py
│   ├── repositorios.py
│   └── servicos.py
├── templates/             # Páginas HTML
├── static/                # CSS
├── tests/                 # Testes automatizados
├── Dockerfile
├── compose.yaml
├── requirements.txt
└── README.md
```

## Pré-requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado e em execução.
- Terminal (Terminal do macOS, VS Code ou equivalente).

Não é necessário instalar Flask ou Gunicorn diretamente no computador para executar com Docker.

## Instalação e execução

### 1. Clonar o repositório

```bash
git clone https://github.com/N3ylor/Locadora.git
cd Locadora/Locadora-Web
```

Se já tiver o repositório clonado, abra um terminal diretamente na pasta `Locadora-Web`.

### 2. Construir e iniciar

```bash
docker compose up --build -d
```

### 3. Abrir no navegador

Acesse **http://localhost:8000**.

A configuração atual publica a porta somente no computador local (`127.0.0.1`). **Publicar o código no GitHub não coloca o site automaticamente na internet.**

### 4. Comandos úteis

```bash
# Conferir o estado do contêiner
docker compose ps

# Acompanhar os logs
docker compose logs -f

# Parar e remover o contêiner (preservando os dados locais)
docker compose down

# Reconstruir após mudanças
docker compose up --build -d
```

## Banco de dados e persistência

O banco utiliza **SQLite**. No `compose.yaml`, a pasta local `./dados` é montada no diretório `/data` do contêiner, e o arquivo usado pela aplicação é `/data/locadora.db`.

Isso permite manter os dados ao recriar o contêiner. **Não exclua a pasta `dados/` se quiser preservar os registros.** Faça backups antes de mudanças importantes e não publique bancos com dados pessoais no GitHub.

## Regras de negócio

| Item | Valor diário | Multa diária por atraso |
| --- | --- | --- |
| Filme | R$ 6,00 | R$ 2,00 |
| Filme lançamento | R$ 9,00 | R$ 3,00 |
| Jogo | R$ 10,00, com 10% de desconto a partir de 5 dias | R$ 4,00 |

A lógica permanece centralizada em `locadora/servicos.py`, em vez de ficar espalhada pelas rotas Flask.

## Testes

Para executar os testes automatizados localmente, com Python configurado:

```bash
python -m unittest discover -s tests -t .
```

O projeto inclui testes para modelos e regras de negócio. A presença dos testes não significa que todos os fluxos web tenham sido validados.

## Segurança e publicação

Esta configuração é voltada ao **uso local e desenvolvimento**. Antes de expor o sistema publicamente, implemente autenticação, uma chave `SECRET_KEY` segura, proteção de formulários contra CSRF, HTTPS e uma estratégia adequada de hospedagem e backup.

## Repositório

[Voltar ao projeto principal](https://github.com/N3ylor/Locadora)
