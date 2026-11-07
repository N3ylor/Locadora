# Locadora Web — Portal e Catálogo (BMVC)

![Python](https://img.shields.io/badge/python-3.12-blue?style=flat-square) ![Framework](https://img.shields.io/badge/framework-BMVC%20(Bottle)-4f7d9c?style=flat-square) ![Banco](https://img.shields.io/badge/banco-SQLite-003b57?style=flat-square) ![Docker](https://img.shields.io/badge/docker-compose-2496ed?style=flat-square) ![Testes](https://img.shields.io/badge/testes-pytest-brightgreen?style=flat-square)

Versão **web** do sistema [Locadora](../README.md), desenvolvida sobre o framework **BMVC** (Bottle + MVC, nível 3). É a terceira pasta do repositório, ao lado de [`terminal/`](../terminal) e [`interface-grafica/`](../interface-grafica).

> **Escopo desta versão:** autenticação com perfis (administrador e cliente), catálogo de **filmes e jogos**, cadastro de **clientes** e **locação e devolução** (limite de 3 itens por cliente, desconto de 10% em jogos a partir de 5 dias e multa por dia de atraso), com persistência em SQLite e execução por Docker. Diferenças em relação às versões `terminal/` e `interface-grafica/`: aqui a diária é o valor cadastrado em cada item, não há a categoria "filme lançamento" e não há recibo.

- **Portal** (`/portal`): login, sessão e logout. O perfil define a página de destino:
  **administrador → `/banco`** e **cliente → `/cliente`**.
- **Banco** (`/banco`, administrador): painel com **filmes, jogos e clientes** (READ na interface web) e APIs CRUD usadas via **cURL**.
- **Área do cliente** (`/cliente`): consulta do catálogo (filmes e jogos), somente leitura.
- Persistência em **SQLite** num volume Docker (os dados sobrevivem a reinícios).

| Perfil | Como é criado | Pode |
|---|---|---|
| **admin** | Variáveis `ADMIN_USERNAME` / `ADMIN_PASSWORD` do `.env` | Tudo: cadastrar, alterar e excluir filmes, jogos e clientes |
| **cliente** | Cadastrado pelo admin (`POST /api/clientes`) | Entrar em `/cliente`, **alugar e devolver** itens e ver as próprias locações. Pode ler o catálogo (`GET /api/filmes`, `GET /api/jogos`). Alterar o catálogo ou os clientes recebe **403** |

## Comandos rápidos

```bash
# Rodar os testes (macOS/Linux)
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest -v

# Subir com Docker
cp .env.example .env && nano .env        # defina ADMIN_PASSWORD
docker compose up --build -d             # http://localhost:8080/portal
docker compose logs -f                   # logs
docker compose down                      # parar (dados ficam no volume)

# Demonstrações com cURL (com a aplicação no ar)
./scripts/demo_crud.sh                   # CRUD de filmes
./scripts/demo_perfis.sh                 # jogos, clientes e permissões admin x cliente
./scripts/demo_locacao.sh                # cliente aluga e devolve (página e API)
```

## Objetivo acadêmico

Demonstrar a arquitetura MVC do BMVC com dois recursos (`portal` e `banco`), autenticação por sessão com perfis (administrador e cliente), persistência real e operações CRUD mistas: **READ pela interface web; CREATE, UPDATE e DELETE pelo terminal Linux com cURL**. O mapeamento requisito → implementação → teste está em [`docs/RELATORIO.md`](docs/RELATORIO.md).

## Arquitetura BMVC

```text
 Navegador / cURL
        │ HTTP
        ▼
 route.py ─────────► Application (controlador principal, `pages` + `render`)
 (só mapeia URLs)         │
                          ├─ PortalController ──► DataRecord ──► SQLite (users) + sessões
                          ├─ ClientesController ─────────┘
                          └─ BancoController ──► CatalogoController ──► Filmes/JogosRepository ──► SQLite
                                  │
              Models: UserAccount, Filme, Jogo, Cliente      Views: portal, banco, cliente, erro, helper
```

| Camada | Onde | Responsabilidade |
|---|---|---|
| **Model** | `app/models/` | `UserAccount` (hash e perfil), `Filme`, `Jogo`, `Cliente` (dados + validação) |
| **View** | `app/views/html/` | Templates Bottle (`portal`, `banco`, `cliente`, `catalogo_tabela`, `erro`, `helper`) |
| **Controller** | `app/controllers/` | `Application`, `PortalController`, `BancoController`, `CatalogoController`, `ClientesController`, `DataRecord`, repositórios |
| **Rotas** | `route.py` | Apenas liga URLs às ações do controlador |

Como no BMVC original, `Application` mantém o dicionário `pages` e o método `render(page, parameter)`, e a página-guia do framework continua em `/helper`.

## Tecnologias

Python 3.12 · Bottle 0.13 · Waitress (servidor WSGI) · SQLite · Docker / Docker Compose · pytest + WebTest.

## Estrutura de diretórios

```text
locadora-web/
├── route.py                      # rotas (páginas + API)
├── app/
│   ├── config.py                 # configuração por variáveis de ambiente
│   ├── controllers/
│   │   ├── application.py        # controlador principal (pages/render)
│   │   ├── portal_controller.py  # login, logout, perfis, limite de tentativas
│   │   ├── banco_controller.py   # páginas /banco (admin) e /cliente
│   │   ├── catalogo_controller.py# regras do CRUD de filmes e jogos
│   │   ├── clientes_controller.py# regras do CRUD de clientes
│   │   ├── locacoes_controller.py# regras de locação e devolução
│   │   ├── locacoes_repository.py# SQL das locações
│   │   ├── datarecord.py         # usuários (hash, perfil) e sessões
│   │   ├── filmes_repository.py  # SQL de filmes e jogos
│   │   ├── database.py           # conexão SQLite
│   │   ├── errors.py             # ApiError
│   │   └── db/                   # pasta do BMVC (banco local fora do Docker)
│   ├── models/                   # user_account.py, filme.py, jogo.py, cliente.py, locacao.py, validacao.py
│   ├── views/html/               # portal, banco, cliente, catalogo_*, locacoes_tabela, erro, helper (.tpl)
│   └── static/                   # css, js, img
├── tests/                        # testes automatizados (pytest)
├── scripts/                      # demo_crud.sh, demo_perfis.sh (cURL)
├── docs/RELATORIO.md             # requisitos x implementação x testes
├── Dockerfile · compose.yaml · requirements*.txt
└── .env.example · .gitignore · .dockerignore
```

## Executar com Docker

```bash
cp .env.example .env          # 1. crie o arquivo de ambiente
nano .env                     # 2. defina ADMIN_PASSWORD (mín. 8 caracteres; o valor de exemplo é recusado)
docker compose up --build -d  # 3. suba a aplicação
```

Abra **http://localhost:8080/portal**. Para acompanhar os logs: `docker compose logs -f`. Para parar: `docker compose down` (os dados ficam no volume `locadora_data`; `docker compose down -v` apaga tudo).

Execute os comandos de Docker dentro de `locadora-web/`. Se a porta 8080 estiver ocupada, defina `HOST_PORT=8081` no `.env`.

## Login e troca de senha

- **Administrador:** usuário `ADMIN_USERNAME` (padrão `admin`) e senha `ADMIN_PASSWORD` do seu `.env`. Cai em `/banco`.
- **Cliente:** conta criada pelo administrador (veja abaixo). Cai em `/cliente`.

**Trocar a senha do administrador:** edite `ADMIN_PASSWORD` no `.env` e rode `docker compose up -d`. O hash é atualizado na inicialização e os logins antigos do admin caem.

**Trocar a senha de um cliente:** o administrador usa a API (veja "Clientes"). As sessões desse cliente são encerradas.

Senhas ficam no banco apenas como hash PBKDF2-SHA256 com sal.

## READ na interface web

- **Administrador (`/banco`):** usuário autenticado, título **Catálogo de filmes e jogos**, e quatro tabelas (filmes, jogos, clientes e locações) com o total de registros, lidas direto do SQLite. Sem registros, aparece uma mensagem informativa.
- **Cliente (`/cliente`):** saudação com o nome, **Minhas locações em aberto** (com botão **Devolver**), as tabelas de filmes e jogos (cada linha com o campo de dias e o botão **Alugar**) e o histórico de devoluções.
- Qualquer alteração feita por cURL aparece ao atualizar a página. O botão **Sair** encerra a sessão.

## CRUD com cURL (CREATE, UPDATE, DELETE)

A API exige o cookie de sessão. Os exemplos usam a porta 8080 e um arquivo de cookies (`cookies.txt`, já no `.gitignore`).

**1. Login** (guarda o cookie):

```bash
curl -i -c cookies.txt --data-urlencode 'username=admin' --data-urlencode 'password=SUA_SENHA' http://localhost:8080/portal
```

**2. CREATE**:

```bash
curl -i -b cookies.txt -X POST http://localhost:8080/api/filmes \
  -H 'Content-Type: application/json' \
  -d '{"titulo":"Matrix","genero":"Ficção científica","valor_diaria":5.00}'
# → 201 Created  {"id": 1, "titulo": "Matrix", ...}
```

**3. READ**: abra http://localhost:8080/banco e atualize. (Também existe `GET /api/filmes` e `GET /api/filmes/1` em JSON.)

**4. UPDATE**:

```bash
curl -i -b cookies.txt -X PUT http://localhost:8080/api/filmes/1 \
  -H 'Content-Type: application/json' \
  -d '{"titulo":"Matrix Reloaded","genero":"Ficção científica","valor_diaria":7.00}'
```

**5. DELETE**:

```bash
curl -i -b cookies.txt -X DELETE http://localhost:8080/api/filmes/1
```

### Jogos

Mesmo contrato dos filmes, trocando `genero` por `plataforma` (até 50 caracteres). Os exemplos usam o `cookies.txt` do **administrador**.

```bash
curl -i -b cookies.txt -X POST http://localhost:8080/api/jogos -H 'Content-Type: application/json' \
  -d '{"titulo":"Zelda","plataforma":"Nintendo Switch","valor_diaria":8.50}'
curl -i -b cookies.txt -X PUT http://localhost:8080/api/jogos/1 -H 'Content-Type: application/json' \
  -d '{"titulo":"Zelda TOTK","plataforma":"Nintendo Switch","valor_diaria":9.00}'
curl -i -b cookies.txt -X DELETE http://localhost:8080/api/jogos/1
```

### Clientes (somente administrador)

`username`: 3 a 32 caracteres (minúsculas, números, `.`, `-`, `_`); `nome`: 1 a 100; `senha`: 8 a 128.

```bash
# Cadastrar
curl -i -b cookies.txt -X POST http://localhost:8080/api/clientes -H 'Content-Type: application/json' \
  -d '{"username":"maria","nome":"Maria Silva","senha":"senha-da-maria"}'
# Listar / consultar
curl -b cookies.txt http://localhost:8080/api/clientes
curl -b cookies.txt http://localhost:8080/api/clientes/maria
# Trocar nome e/ou senha (envie só o que mudar)
curl -i -b cookies.txt -X PUT http://localhost:8080/api/clientes/maria -H 'Content-Type: application/json' \
  -d '{"senha":"nova-senha-123"}'
# Excluir
curl -i -b cookies.txt -X DELETE http://localhost:8080/api/clientes/maria
```

O cliente entra em http://localhost:8080/portal com o `username` e a senha cadastrados.

### Locação e devolução

**Pela página:** em `/cliente`, informe os dias (1 a 30) ao lado do item e clique em **Alugar**. Para devolver, clique em **Devolver** em "Minhas locações em aberto".

**Pelo cURL** (cookie do **cliente**, obtido com o login dele):

```bash
curl -c cookies-cliente.txt --data-urlencode 'username=maria' --data-urlencode 'password=senha-da-maria' http://localhost:8080/portal
curl -b cookies-cliente.txt -X POST http://localhost:8080/api/locacoes -H 'Content-Type: application/json' -d '{"tipo":"filme","item_id":1,"dias":3}'
curl -b cookies-cliente.txt http://localhost:8080/api/locacoes
curl -b cookies-cliente.txt -X POST http://localhost:8080/api/locacoes/1/devolucao
```

`tipo` é `filme` ou `jogo`, e `item_id` é o `id` do item no catálogo. O administrador vê todas as locações (`GET /api/locacoes`) e pode registrar qualquer devolução; ele não aluga itens.

**Regras:**

| Regra | Valor |
|---|---|
| Itens alugados ao mesmo tempo, por cliente | no máximo 3 (o 4º recebe **409**) |
| Prazo | de 1 a 30 dias |
| Valor | diária do item × dias (valor congelado no momento da locação) |
| Desconto | jogo alugado por 5 dias ou mais: 10% |
| Multa por dia de atraso | filme R$ 2,00 · jogo R$ 4,00 (fixada na devolução) |
| Disponibilidade | cada item cadastrado é uma cópia: enquanto estiver alugado, ninguém mais o aluga (**409**). Para ter duas cópias, cadastre o título duas vezes |
| Exclusões | não é possível excluir um item alugado nem um cliente com locação em aberto (**409**) |

A data de "hoje" segue o fuso `TIMEZONE` do `.env` (padrão `America/Sao_Paulo`). Se o prazo previsto já passou, o atraso é contado em dias corridos até a data da devolução.

### Quem pode o quê

| Rota | Anônimo | Cliente | Admin |
|---|---|---|---|
| `GET /api/filmes`, `GET /api/jogos` (e `/<id>`) | 401 | 200 | 200 |
| `POST/PUT/DELETE` em `/api/filmes` e `/api/jogos` | 401 | **403** | 200/201 |
| Qualquer rota de `/api/clientes` | 401 | **403** | 200/201 |
| `GET /api/locacoes` | 401 | só as dele | todas |
| `POST /api/locacoes` (alugar) | 401 | 201 | **403** |
| `POST /api/locacoes/<id>/devolucao` | 401 | só as dele (senão 404) | qualquer uma |
| Página `/banco` | → `/portal` | → `/cliente` | 200 |
| Página `/cliente` | → `/portal` | 200 | → `/banco` |

**Respostas de erro (sempre JSON em `/api/*`):** `401` sem login · `403` sem permissão · `409` conflito (username em uso, item já alugado, limite de itens, locação já devolvida) · `404` registro inexistente · `415` faltou `Content-Type: application/json` · `400` JSON malformado · `413` corpo grande · `422` dados inválidos, com o detalhe por campo.

**Regras de validação:** `titulo` (1–200 caracteres) e `genero` (1–100) são textos sem caracteres de controle; `valor_diaria` é número de 0 a 9999,99 com no máximo 2 casas decimais (booleanos são recusados).

**Demonstração automática** (executa todo o fluxo acima e mostra cada resposta):

```bash
./scripts/demo_crud.sh            # CRUD de filmes
./scripts/demo_perfis.sh          # jogos, clientes e permissões (admin x cliente)
./scripts/demo_locacao.sh         # locação e devolução (página e API)
```
(ambos leem `ADMIN_USERNAME`/`ADMIN_PASSWORD` do `.env`)

## Testes

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest -v
```

Os testes usam um SQLite temporário e cobrem: perfis admin/cliente e redirecionamentos, permissões (403), CRUD de clientes e jogos, locação, devolução, desconto, multa, limite de itens e concorrência, migração de bancos antigos, login válido/inválido, bloqueio do `/banco` e da API sem login, CREATE/READ/UPDATE/DELETE, validação, registros inexistentes, templates, escape de HTML (XSS), expiração de sessão, bloqueio por tentativas e persistência após "reiniciar" a aplicação. A mesma suíte roda no GitHub Actions (workflow `.github/workflows/locadora-web.yml`, na **raiz** do repositório, executado quando algo em `locadora-web/` muda).

Rodar sem Docker: `pip install -r requirements.txt && ADMIN_PASSWORD='sua-senha-aqui' python route.py` (banco em `app/controllers/db/locadora.db`).

## Segurança

- Senhas apenas como hash PBKDF2-SHA256 (600 mil iterações, sal por usuário); credenciais vindas do ambiente; a aplicação **não inicia** sem senha válida.
- Cookie de sessão `HttpOnly` + `SameSite=Strict` (+ `Secure` com `COOKIE_SECURE=true` atrás de HTTPS); sessões expiram no servidor em 1 h e são invalidadas no logout.
- Bloqueio temporário após 5 logins falhos (por IP + usuário); mensagens e tempo de resposta não revelam se o usuário existe.
- Toda a API exige autenticação; escrita e gestão de clientes só para administrador (403 para cliente); excluir cliente ou trocar sua senha derruba as sessões dele; HTML escapado nos templates; cabeçalhos CSP, `X-Frame-Options`, `nosniff` e `no-store`.
- Contêiner roda sem privilégios (usuário `app`), com `HEALTHCHECK`.
- `.env`, `cookies.txt` e arquivos `.db` estão no `.gitignore` e no `.dockerignore`. **Nunca publique o `.env`.**

Limitações conhecidas (projeto acadêmico, uso local): não há categoria "filme lançamento", recibo nem renovação de locação; não há autocadastro (clientes são criados pelo administrador) nem troca de senha pelo próprio cliente; as sessões ficam em memória (um reinício do contêiner exige novo login); para internet pública, coloque HTTPS na frente e use `COOKIE_SECURE=true`.

## Obter o código e publicar no GitHub

Esta versão vive na pasta `locadora-web/` do repositório [N3ylor/Locadora](https://github.com/N3ylor/Locadora):

```bash
git clone https://github.com/N3ylor/Locadora.git
cd Locadora/locadora-web
```

Para publicar alterações, a partir da raiz do repositório:

```bash
git add -A
git status
git commit -m "Atualiza locadora-web"
git push
```

Antes de confirmar, confira no `git status`: o `.env`, o `cookies.txt` e arquivos `.db` **não** podem aparecer (o `.gitignore` desta pasta já os ignora).

## Texto explicativo para entrega

> O projeto Locadora Web (BMVC) foi desenvolvido sobre o framework BMVC (nível 3), mantendo Bottle, a separação Model/View/Controller, o controlador `Application` com `pages`/`render`, o `DataRecord` e o arquivo `route.py`. O recurso **portal** autentica usuários pelo modelo `UserAccount`, com senha em hash, sessão por cookie e logout. O recurso **banco** exibe, somente a usuários autenticados, o catálogo de filmes (id, título, gênero e valor da diária) lido do SQLite — operação **READ** na interface web. As operações **CREATE**, **UPDATE** e **DELETE** são feitas no terminal Linux com cURL, na API `/api/filmes`, usando o cookie de sessão, com validação de dados e tratamento de registros inexistentes. Os dados persistem em volume Docker, e a aplicação sobe com `docker compose up --build -d`.
