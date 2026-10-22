# Diagrama de classes da locadora

Para ver o desenho, cole o código abaixo (sem as linhas com três crases) em https://mermaid.live. No GitHub ele já aparece desenhado.

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

    Pessoa <|-- Cliente
    Pessoa <|-- Funcionario
    Item <|-- Filme
    Item <|-- Jogo

    Cliente *-- Endereco
    Locacao *-- "1..*" ItemLocacao

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

    Recibo ..> Locacao : usa
    Locadora ..> Recibo : usa
    Locadora ..> Locacao : cria
    LocacaoRepositorio ..> Locacao : reconstrói
    ItemRepositorio ..> Filme : cria
    ItemRepositorio ..> Jogo : cria
```

## Onde cada relação está no código

**Herança.** Cliente e Funcionario herdam de Pessoa (`models/pessoa.py`). Filme e Jogo herdam de Item (`models/item.py`).

**Polimorfismo.** Cada classe filha responde do seu jeito aos mesmos métodos: `descricao()`, `valor_diaria` e `multa_por_dia`. O Jogo ainda reescreve o `calcular_valor` para dar 10% de desconto a partir de 5 dias (`models/item.py`).

**Composição.** O Cliente cria o seu próprio Endereco (`models/pessoa.py`). A Locacao cria os seus ItemLocacao (`models/locacao.py`). Essas partes não fazem sentido sozinhas.

**Associação.** A Locacao guarda um Cliente e um Funcionario, e cada ItemLocacao guarda um Item. Esses objetos existem por conta própria, a locação só se liga a eles (`models/locacao.py`). A classe Locadora também guarda os repositórios (`servicos.py`).

**Dependência.** O Recibo recebe uma Locacao só como parâmetro do método `gerar` e não guarda ela (`models/recibo.py`).
