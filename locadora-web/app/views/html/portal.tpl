<!doctype html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="icon" href="data:,">
    <title>Locadora | Portal</title>
    <link rel="stylesheet" href="/static/css/locadora.css">
</head>
<body>
    <main class="login">
        <div class="eyebrow">BMVC · PORTAL</div>

        <h1>Locadora</h1>
        <p>Entre para consultar o catálogo de filmes.</p>

        % if error:
            <div class="error" role="alert">{{error}}</div>
        % end

        <form action="/portal" method="post">
            <label>
                Usuário
                <input name="username" required maxlength="256" autofocus autocomplete="username">
            </label>

            <label>
                Senha
                <input type="password" name="password" required maxlength="1024"
                       autocomplete="current-password">
            </label>

            <button type="submit">Entrar</button>
        </form>
    </main>
</body>
</html>
