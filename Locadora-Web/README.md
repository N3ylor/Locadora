# Locadora Web — Flask + Docker

Migração da interface gráfica original para navegador, reutilizando os modelos, repositórios, serviços e SQLite.

## Rodar

1. Instale e inicie o Docker Desktop.
2. Extraia o ZIP e abra um terminal **na pasta `Locadora-Web`**.
3. Execute `docker compose up --build -d`.
4. Acesse http://localhost:8000.
5. Para ver logs: `docker compose logs -f`.
6. Para parar: `docker compose down`.

## Dados

O SQLite fica em `dados/locadora.db` no computador, montado em `/data/locadora.db` no contêiner. A pasta `dados` já contém uma cópia do banco original da versão gráfica. Não apague essa pasta se quiser manter os dados. Faça backup antes de alterações importantes.

## Funcionalidades

Painel, clientes, funcionários, filmes, jogos, cadastro/edição/exclusão, locações com até 3 itens por cliente e prazos individuais, devolução, multas, filtro de locações abertas e recibo imprimível. As validações e regras continuam nos serviços originais.

## Observações

A porta 8000 está exposta somente em localhost, não na internet. Para publicar na internet é necessário autenticação, configuração de segredo e HTTPS. Não use este protótipo como serviço público sem esses controles.
