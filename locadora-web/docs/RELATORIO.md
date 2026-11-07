# Relatório de requisitos — Locadora Web (BMVC)

Cada requisito do enunciado, onde foi implementado e **como foi verificado**.

Legenda: ✅ verificado por execução · ⚠️ implementado, **não executado** no ambiente de desenvolvimento (precisa ser conferido na sua máquina).

Ambiente das verificações: Python 3.12, Bottle 0.13.4, Waitress 3.0.2. Suíte automatizada: **174 testes, 174 aprovados**. Verificação ponta a ponta: servidor real + cURL real (`scripts/demo_crud.sh`, `scripts/demo_perfis.sh` e `scripts/demo_locacao.sh`), com o log do servidor inspecionado (0 ocorrências de `ERROR`/`Traceback`).

## 1. Arquitetura BMVC

| Requisito | Implementação | Status |
|---|---|---|
| Usar o BMVC, sem trocar por outro framework | Bottle; `route.py`, `Application`, `DataRecord`, `app/models`, `app/views/html`, `app/static` preservados | ✅ |
| `Application` com `pages` e `render()` do BMVC | `app/controllers/application.py`; rota `/helper` (guia do BMVC) restaurada | ✅ `test_helper_do_bmvc_continua_disponivel`, `test_render_desconhecido_cai_no_helper` |
| Separação Model / View / Controller | Validação nos modelos; regras nos controladores; `route.py` só roteia | ✅ (revisão de código) |
| Não concentrar a lógica em um arquivo | `portal_controller.py`, `banco_controller.py`, `datarecord.py`, `filmes_repository.py`, `database.py` | ✅ |

## 2. Portal

| Requisito | Implementação | Status |
|---|---|---|
| Página de login | `portal.tpl` | ✅ `test_pagina_de_login_tem_formulario` |
| Modelo `User_account` | `UserAccount` (+ alias `User_account`) | ✅ `test_hash_de_senha_e_salgado_e_verificavel` |
| Autenticação por usuário e senha | `DataRecord.check_user` | ✅ `test_login_valido_...`; ponta a ponta com senha acentuada |
| Sessão e logout | Cookie `session_id`; `POST /logout` invalida no servidor | ✅ `test_logout_encerra_a_sessao`, `test_logout_invalida_o_token_no_servidor` |
| Erro para credenciais inválidas | Mensagem "Usuário ou senha incorretos." (HTTP 401) | ✅ `test_credenciais_invalidas_...` |
| Redirecionar para `banco` após login | `303 → /banco` | ✅ |

## 3. Segurança

| Requisito | Implementação | Status |
|---|---|---|
| `banco` bloqueado sem login | `/banco` → redireciona a `/portal` | ✅ `test_banco_exige_autenticacao` |
| Rotas de alteração exigem login | Todos os métodos de `/api/filmes` retornam 401 | ✅ `test_api_exige_autenticacao` (5 rotas) |
| Senhas não ficam em texto puro | PBKDF2-SHA256 + sal; confirmado no arquivo `.db` | ✅ `test_senha_nao_fica_em_texto_puro_no_banco`; `grep` no `.db` = 0 ocorrências |
| Credenciais configuráveis sem alterar o código | `ADMIN_USERNAME` / `ADMIN_PASSWORD` no `.env`; sem senha válida a app **não inicia** | ✅ `test_config_*`; execução sem senha → saída com erro |
| Cookie de sessão protegido | `HttpOnly`, `SameSite=Strict`, `Secure` configurável, TTL no servidor | ✅ `test_login_valido_...`, `test_sessao_expira_no_servidor` |
| Não publicar segredos | `.gitignore` / `.dockerignore`; `.env` removido do pacote | ✅ (revisão) |
| Extras | Bloqueio por tentativas, CSP/X-Frame/nosniff/no-store, escape de HTML, contêiner não-root | ✅ `test_bloqueio_temporario_...`, `test_cabecalhos_de_seguranca`, `test_html_e_escapado_contra_xss` |

## 4–6. Banco (catálogo) e CRUD

| Requisito | Implementação | Status |
|---|---|---|
| Atributos `id`, `titulo`, `genero`, `valor_diaria` | `Filme`; tabela `filmes` | ✅ |
| Persistência em SQLite | `database.py`, `filmes_repository.py` | ✅ |
| **CREATE** via cURL (`POST /api/filmes`, 201) | `BancoController.criar` | ✅ `test_create_*`; demo cURL real |
| Validação dos dados | `Filme.validar` → 422 com detalhe por campo; 400/413/415 para corpo inválido | ✅ 19 casos parametrizados + demo |
| **READ** na interface web (tabela com ID, Título, Gênero, Diária; total; mensagem se vazio) | `banco.tpl`, lido do SQLite | ✅ `test_banco_*` |
| **UPDATE** via cURL (`PUT /api/filmes/<id>`; 404 se não existir) | `BancoController.atualizar` | ✅ `test_update_*` |
| **DELETE** via cURL (`DELETE /api/filmes/<id>`; verifica existência) | `BancoController.excluir` | ✅ `test_delete_*` |
| Tratamento de registros inexistentes | 404 em JSON (inclusive IDs gigantes ou negativos) | ✅ |
| Mesma base para terminal e interface | Fluxo CREATE → página → UPDATE → DELETE | ✅ `test_fluxo_completo_create_read_delete`; demo cURL real |

## 7. Docker

| Requisito | Implementação | Status |
|---|---|---|
| `Dockerfile`, `compose.yaml`, `requirements.txt`, `.dockerignore`, `.env.example`, `.gitignore` | Presentes | ✅ arquivos criados; `compose.yaml` com YAML válido |
| `docker compose up --build -d` em `http://localhost:8080/portal` | Imagem `python:3.12-slim`, usuário não-root, `HEALTHCHECK`, porta 8080 | ⚠️ **não executado** (o ambiente de desenvolvimento não tem Docker) |
| Volume persistente para o SQLite | Volume `locadora_data` montado em `/data`; `DB_PATH=/data/locadora.db` | ⚠️ **não executado** com Docker. A persistência foi verificada reiniciando o processo sobre o mesmo arquivo `.db` (`test_persistencia_apos_reiniciar_a_aplicacao` e reinício real do servidor) |
| Funciona em Linux | Servidor e testes executados em Ubuntu 24 | ✅ |

## 8. Interface

| Requisito | Status |
|---|---|
| Portal: formulário, campos usuário/senha, botão Entrar, mensagens de erro | ✅ |
| Banco: nome do usuário, título "Catálogo de filmes", tabela, total, mensagem sem registros, botão Sair | ✅ |
| Templates com `% if` / `% for` / `% end` em linhas próprias | ✅ renderizados nos testes e no servidor real |
| Aparência no navegador (layout/CSS) | ⚠️ não inspecionada visualmente; só o HTML e o CSS servido foram verificados |

## 9. Testes obrigatórios

| Teste pedido | Resultado |
|---|---|
| Login válido / credenciais inválidas rejeitadas | ✅ |
| Bloqueio do banco sem login | ✅ |
| CREATE / UPDATE / DELETE autenticados via cURL | ✅ (servidor real + cURL) |
| READ na interface web | ✅ |
| Registros inexistentes e validação | ✅ |
| Persistência após reiniciar | ✅ reinício do processo · ⚠️ reinício de contêiner Docker não executado |
| Templates e rotas | ✅ |
| Ausência de erros nos logs | ✅ log do servidor real: 0 `ERROR`/`Traceback` · ⚠️ `docker compose logs` não executado |

## Extensões pedidas depois (perfis, clientes e jogos)

| Funcionalidade | Implementação | Status |
|---|---|---|
| Login define a página: admin → `/banco`, cliente → `/cliente` | `PortalController.destino`, rotas `/portal`, `/cliente` | ✅ `test_admin_e_levado_ao_banco`, `test_cliente_e_levado_a_area_do_cliente`; demo cURL real |
| Página do cliente (somente leitura) | `cliente.tpl` | ✅ `test_pagina_do_cliente_*` |
| Cliente não acessa o painel do admin e vice-versa | Redirecionamentos por perfil | ✅ `test_cliente_nao_acessa_o_painel_do_admin`, `test_admin_nao_usa_a_pagina_do_cliente` |
| Cliente lê, mas não altera (403) | `api(admin=True)` | ✅ `test_cliente_pode_ler_mas_nao_escrever_no_catalogo`; demo cURL real |
| CRUD de clientes pelo admin (cURL) | `/api/clientes`, `ClientesController`; username único (409) | ✅ `test_*cliente*` |
| Trocar senha / excluir cliente derruba as sessões dele | `DataRecord._purge_sessions` | ✅ `test_trocar_senha_do_cliente_derruba_sessoes...`, `test_excluir_cliente_derruba_a_sessao_dele` |
| Recurso Jogos (CRUD via cURL, leitura na interface) | `/api/jogos`, `jogo.py`, `CatalogoController` | ✅ `test_crud_de_jogos`, `test_jogo_validacao_422` |
| Banco criado pela versão anterior continua funcionando | Migração automática em `Database._migrar` | ✅ `test_banco_antigo_sem_perfil_e_migrado` |
| Cliente escolhe e **aluga** itens na página (campo de dias + botão Alugar) | `cliente.tpl`, `POST /cliente/alugar` | ✅ `test_alugar_pela_pagina_*`; demo cURL real (HTTP 303 → `?aviso=alugado`) |
| Cliente vê "Minhas locações", **devolve** e vê o histórico | `locacoes_tabela.tpl`, `POST /cliente/devolver/<id>` | ✅ `test_devolver_pela_pagina_com_e_sem_multa` |
| API de locações (`/api/locacoes`, `/devolucao`) | `LocacoesController` | ✅ `test_cliente_aluga_filme_*`, `test_devolucao_*` |
| Limite de 3 itens por cliente | `LocacoesRepository.criar` (transação `BEGIN IMMEDIATE`) | ✅ `test_limite_de_3_itens_por_cliente`; `test_concorrencia_respeita_limite_e_item_unico` (10 pedidos simultâneos, repetido 8 vezes) |
| Desconto de 10% em jogo a partir de 5 dias | `calcular_valor` | ✅ `test_jogo_ate_4_dias_*` · demo cURL real: 50,00 → 45,00 |
| Multa por atraso (filme R$ 2,00/dia, jogo R$ 4,00/dia) | `calcular_multa`, relógio injetável | ✅ `test_multa_*` (atraso simulado com relógio de teste) · ⚠️ atraso real não foi vivenciado em servidor, pois exigiria dias de espera |
| Um item só tem uma locação em aberto (garantido pelo SQLite) | Índice único parcial | ✅ `test_so_um_aluguel_em_aberto_por_item_no_banco` |
| Não excluir item alugado nem cliente com locação em aberto | `CatalogoController`, `ClientesController` | ✅ `test_nao_exclui_*` |
| Cliente só vê e devolve as próprias locações | `LocacoesController.obter` (404 para as de outros) | ✅ `test_cliente_nao_devolve_nem_ve_locacao_de_outro` |
| Admin vê todas as locações no painel | `banco.tpl` | ✅ `test_painel_do_admin_lista_locacoes_com_cliente` |
| Banco da versão anterior (sem tabela de locações) é migrado | `Database` (`CREATE TABLE IF NOT EXISTS`) | ✅ `test_banco_antigo_sem_tabela_de_locacoes_e_migrado` |
| Troca da senha do admin pelo `.env` | Sincronização na inicialização | ✅ `test_trocar_a_senha_no_ambiente_atualiza_o_hash` · ⚠️ `docker compose up -d` recriando o contêiner não foi executado |

Observação: o título do painel do admin passou a ser "Catálogo de filmes e jogos" (contém o texto "Catálogo de filmes" exigido no enunciado).

## Problemas encontrados no projeto original e corrigidos

| # | Problema | Como foi verificado | Correção |
|---|---|---|---|
| 1 | Senha com acentos nunca autenticava | `curl` com senha acentuada → 401 | `request.forms.getunicode()` |
| 2 | `DELETE/PUT` com ID enorme → erro 500 e traceback no log | Reproduzido (`OverflowError`) | Validação do intervalo do ID no repositório |
| 3 | `"valor_diaria": true` era aceito como preço 1,00 | Reproduzido (HTTP 201) | Validação estrita; valor em `Decimal` com 2 casas |
| 4 | `render()`/`pages` e `/helper` do BMVC haviam sido removidos | `GET /helper` → 404 | Restaurados |
| 5 | Rotas em `/banco/filmes` e validação dentro do `route.py` | Leitura do código | `/api/filmes`; validação no modelo `Filme` |
| 6 | `.env` com senha real dentro do pacote | Listagem do zip | Removido do pacote |
| 7 | Conexões SQLite nunca fechadas (`with sqlite3.connect()` só faz commit) | Leitura do código | `Database.connection()` fecha sempre |
| 8 | Senha padrão insegura se faltasse a variável de ambiente | Leitura do código | A aplicação recusa iniciar sem senha válida |
| 9 | Sessão sem expiração no servidor; sem limite de tentativas de login | Leitura do código | TTL no servidor e bloqueio temporário |
| 10 | Erros da API em HTML; sem cabeçalhos de segurança; contêiner como root | Reproduzido | Erros em JSON, cabeçalhos, usuário `app`, `HEALTHCHECK` |
| 11 | Banco fixo em `/data` (frágil fora do Docker); templates dependiam do diretório de execução | Leitura do código | `DB_PATH` configurável; templates por nome |
| 12 | `helper.tpl` chamava `displayText()` (inexistente) e usava caminhos relativos | Leitura do código | Correção mínima: chamada removida, caminhos absolutos |
| 13 | `pagina.tpl` de exemplo exibia a senha do usuário; `pagina.css/js` vazios | Leitura do código | Arquivos de exemplo removidos |
