# Locadora Web — Etapa 1

1. Abra o terminal dentro da pasta `Locadora-Web`.
2. Execute `docker compose up --build -d`.
3. Abra http://localhost:8000.
4. Para ver logs: `docker compose logs -f`.
5. Para parar: `docker compose down`.

O banco original foi copiado para `dados/locadora.db`. Não apague essa pasta.

**Estado atual:** painel inicial web somente leitura, com Flask e Docker. CRUD, locações, devoluções e recibos ainda usam a interface antiga e serão migrados em etapas posteriores.

A porta está vinculada ao endereço local 127.0.0.1 por segurança. Para publicar na internet será necessário configurar hospedagem, HTTPS e autenticação.
