<!doctype html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="icon" href="data:,">
    <title>Locadora | Cliente</title>
    <link rel="stylesheet" href="/static/css/locadora.css">
</head>
<body>
    <header>
        <div>
            <span class="eyebrow">BMVC · ÁREA DO CLIENTE</span>
            <h1>Catálogo da locadora</h1>
            <p>Olá, <strong>{{nome}}</strong>! Escolha um item, informe os dias e clique em Alugar.</p>
        </div>

        <form method="post" action="/logout">
            <button type="submit" class="secondary">Sair</button>
        </form>
    </header>

    <main>
        % if aviso:
            <div class="notice {{aviso[0]}}" role="status">{{aviso[1]}}</div>
        % end

        <section class="panel">
            <h2>
                Minhas locações em aberto
                <small>{{len(abertas)}} de {{limite}} itens</small>
            </h2>
            % include('locacoes_tabela', locacoes=abertas, hoje=hoje, devolver=True, mostrar_cliente=False, vazio='Você não tem itens alugados no momento.')
            <p class="hint">{{regras}}</p>
        </section>

        <section class="panel">
            <h2>
                Filmes
                <small>{{len(filmes)}} {{'título' if len(filmes) == 1 else 'títulos'}}</small>
            </h2>
            % include('catalogo_cliente', itens=filmes, tipo='filme', rotulo='Gênero', indisponiveis=indisponiveis, pode_alugar=pode_alugar, dias_max=dias_max, vazio='Nenhum filme disponível no momento.')
        </section>

        <section class="panel">
            <h2>
                Jogos
                <small>{{len(jogos)}} {{'título' if len(jogos) == 1 else 'títulos'}}</small>
            </h2>
            % include('catalogo_cliente', itens=jogos, tipo='jogo', rotulo='Plataforma', indisponiveis=indisponiveis, pode_alugar=pode_alugar, dias_max=dias_max, vazio='Nenhum jogo disponível no momento.')
        </section>

        <section class="panel">
            <h2>
                Histórico
                <small>{{len(historico)}} {{'devolução' if len(historico) == 1 else 'devoluções'}}</small>
            </h2>
            % include('locacoes_tabela', locacoes=historico, hoje=hoje, devolver=False, mostrar_cliente=False, vazio='Nenhuma locação devolvida ainda.')
        </section>
    </main>
</body>
</html>
