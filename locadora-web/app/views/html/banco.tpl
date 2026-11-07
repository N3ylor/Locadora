<!doctype html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="icon" href="data:,">
    <title>Locadora | Banco</title>
    <link rel="stylesheet" href="/static/css/locadora.css">
</head>
<body>
    <header>
        <div>
            <span class="eyebrow">BMVC · BANCO · ADMINISTRADOR</span>
            <h1>Catálogo de filmes e jogos</h1>
            <p>Usuário autenticado: <strong>{{user}}</strong></p>
        </div>

        <form method="post" action="/logout">
            <button type="submit" class="secondary">Sair</button>
        </form>
    </header>

    <main>
        <section class="panel">
            <h2>
                Filmes cadastrados
                <small>Total: {{len(filmes)}} {{'registro' if len(filmes) == 1 else 'registros'}}</small>
            </h2>
            % include('catalogo_tabela', itens=filmes, rotulo='Gênero', vazio='Nenhum filme cadastrado ainda. Use o comando cURL (CREATE) do README para adicionar o primeiro e atualize esta página.')
        </section>

        <section class="panel">
            <h2>
                Jogos cadastrados
                <small>Total: {{len(jogos)}} {{'registro' if len(jogos) == 1 else 'registros'}}</small>
            </h2>
            % include('catalogo_tabela', itens=jogos, rotulo='Plataforma', vazio='Nenhum jogo cadastrado ainda.')
        </section>

        <section class="panel">
            <h2>
                Clientes cadastrados
                <small>Total: {{len(clientes)}} {{'registro' if len(clientes) == 1 else 'registros'}}</small>
            </h2>
            % if clientes:
                <div class="scroll">
                    <table>
                        <thead>
                            <tr>
                                <th>Usuário</th>
                                <th>Nome</th>
                            </tr>
                        </thead>
                        <tbody>
                            % for cliente in clientes:
                            <tr>
                                <td>{{cliente.username}}</td>
                                <td>{{cliente.nome}}</td>
                            </tr>
                            % end
                        </tbody>
                    </table>
                </div>
            % else:
                <p class="empty">Nenhum cliente cadastrado ainda.</p>
            % end

        </section>

        <section class="panel">
            <h2>
                Locações
                <small>Total: {{len(locacoes)}} {{'registro' if len(locacoes) == 1 else 'registros'}}</small>
            </h2>
            % include('locacoes_tabela', locacoes=locacoes, hoje=hoje, devolver=False, mostrar_cliente=True, vazio='Nenhuma locação registrada ainda.')

            <p class="hint">
                Esta página realiza o READ. CREATE, UPDATE e DELETE são feitos via cURL nas APIs
                <code>/api/filmes</code>, <code>/api/jogos</code>, <code>/api/clientes</code> e <code>/api/locacoes</code>,
                com o cookie de sessão do administrador.
            </p>
        </section>
    </main>
</body>
</html>
