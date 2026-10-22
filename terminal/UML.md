# Diagrama UML - Locadora

Cole o bloco abaixo em https://mermaid.live (ou no GitHub, que renderiza Mermaid automaticamente) para gerar a imagem.

```mermaid
classDiagram
    direction TB

    class Pessoa {
        <<abstract>>
        +int id
        +str nome
        +str cpf
        +descricao()* str
    }
    class Cliente {
        +int LIMITE_ITENS = 3
        +Endereco endereco
        +descricao() str
    }
    class Funcionario {
        +str cargo
        +descricao() str
    }
    class Endereco {
        +str rua
        +str numero
        +str cidade
        +str uf
    }

    class Item {
        <<abstract>>
        +int id
        +str titulo
        +int ano
        +bool disponivel
        +valor_diaria()* float
        +multa_por_dia()* float
        +descricao()* str
        +calcular_valor(dias) float
        +calcular_multa(dias_atraso) float
        +emprestar()
        +devolver()
    }
    class Filme {
        +str genero
        +int duracao_min
        +bool lancamento
        +valor_diaria float
        +multa_por_dia float
    }
    class Jogo {
        +str plataforma
        +valor_diaria float
        +multa_por_dia float
        +calcular_valor(dias) float
    }

    class Locacao {
        +int id
        +date data_locacao
        +date data_devolucao
        +float multa
        +total float
        +adicionar_item(item, dias)
        +devolver(data)
    }
    class ItemLocacao {
        +int dias
        +date data_prevista
        +valor float
        +multa(data) float
    }
    class Recibo {
        +gerar(locacao)$ str
    }

    class Locadora {
        +cadastrar_cliente()
        +alugar()
        +devolver()
        +listar_locacoes()
    }
    class Database
    class ClienteRepositorio
    class FuncionarioRepositorio
    class ItemRepositorio
    class LocacaoRepositorio

    %% HERANÇA
    Pessoa <|-- Cliente
    Pessoa <|-- Funcionario
    Item <|-- Filme
    Item <|-- Jogo

    %% COMPOSIÇÃO (parte não existe sem o todo)
    Cliente *-- Endereco
    Locacao *-- "1..*" ItemLocacao

    %% ASSOCIAÇÃO
    Locacao --> Cliente : cliente
    Locacao --> Funcionario : atendente
    ItemLocacao --> Item : item
    Locadora --> ClienteRepositorio
    Locadora --> FuncionarioRepositorio
    Locadora --> ItemRepositorio
    Locadora --> LocacaoRepositorio
    ClienteRepositorio --> Database
    FuncionarioRepositorio --> Database
    ItemRepositorio --> Database
    LocacaoRepositorio --> Database

    %% DEPENDÊNCIA (usa apenas como parâmetro / criação local)
    Recibo ..> Locacao : usa
    Locadora ..> Recibo : usa
    Locadora ..> Locacao : cria
    LocacaoRepositorio ..> Locacao : reconstrói
    ItemRepositorio ..> Filme : cria
    ItemRepositorio ..> Jogo : cria
```

## Onde cada relação aparece no código

| Relação | Onde | Arquivo |
|---|---|---|
| Herança | `Cliente`/`Funcionario` -> `Pessoa`; `Filme`/`Jogo` -> `Item` | `models/pessoa.py`, `models/item.py` |
| Polimorfismo | `descricao()`, `valor_diaria`, `multa_por_dia`; `Jogo.calcular_valor` sobrescrito (10% de desconto a partir de 5 dias) | `models/item.py`, `models/pessoa.py` |
| Composição | `Cliente` cria seu `Endereco`; `Locacao` cria seus `ItemLocacao` | `models/pessoa.py`, `models/locacao.py` |
| Associação | `Locacao` -> `Cliente`/`Funcionario`; `ItemLocacao` -> `Item`; `Locadora` -> repositórios | `models/locacao.py`, `servicos.py` |
| Dependência | `Recibo.gerar(locacao)` recebe a locação só como parâmetro | `models/recibo.py` |
