import unittest
from datetime import date

from locadora.excecoes import RegraNegocioError, ValidacaoError
from locadora.models import (Cliente, Endereco, Filme, Funcionario, Item, Jogo,
                             Locacao, Pessoa, Recibo)


class TestHerancaEPolimorfismo(unittest.TestCase):
    def test_heranca(self):
        self.assertTrue(issubclass(Cliente, Pessoa))
        self.assertTrue(issubclass(Funcionario, Pessoa))
        self.assertTrue(issubclass(Filme, Item))
        self.assertTrue(issubclass(Jogo, Item))

    def test_classes_abstratas_nao_instanciam(self):
        with self.assertRaises(TypeError):
            Pessoa("Ana", "12345678901")
        with self.assertRaises(TypeError):
            Item("X", 2000)

    def test_polimorfismo_de_preco_e_multa(self):
        itens = [Filme("A", 2000, "Drama", 100), Filme("B", 2026, "Ação", 90, lancamento=True),
                 Jogo("C", 2020, "PC")]
        self.assertEqual([i.calcular_valor(2) for i in itens], [12.0, 18.0, 20.0])
        self.assertEqual([i.calcular_multa(2) for i in itens], [4.0, 6.0, 8.0])

    def test_jogo_desconto_5_dias(self):
        self.assertEqual(Jogo("C", 2020, "PC").calcular_valor(5), 45.0)
        self.assertEqual(Jogo("C", 2020, "PC").calcular_valor(4), 40.0)

    def test_polimorfismo_descricao(self):
        c = Cliente("Ana", "123.456.789-01", "Rua A", "1", "Brasília", "DF", id=1)
        f = Funcionario("Bia", "98765432100", id=2)
        self.assertIn("Cliente", str(c))
        self.assertIn("Funcionário", str(f))


class TestComposicao(unittest.TestCase):
    def test_cliente_cria_endereco(self):
        c = Cliente("Ana", "12345678901", "Rua A", "", "Brasília", "df")
        self.assertIsInstance(c.endereco, Endereco)
        self.assertEqual(c.endereco.uf, "DF")
        self.assertEqual(c.endereco.numero, "S/N")


class TestValidacoes(unittest.TestCase):
    def test_pessoa_invalida(self):
        with self.assertRaises(ValidacaoError):
            Funcionario("", "12345678901")
        with self.assertRaises(ValidacaoError):
            Funcionario("Ana", "123")

    def test_endereco_invalido(self):
        with self.assertRaises(ValidacaoError):
            Cliente("Ana", "12345678901", "", "1", "Cidade", "DF")
        with self.assertRaises(ValidacaoError):
            Cliente("Ana", "12345678901", "Rua", "1", "Cidade", "DFX")

    def test_item_invalido(self):
        with self.assertRaises(ValidacaoError):
            Filme("", 2000, "Drama", 90)
        with self.assertRaises(ValidacaoError):
            Filme("A", 1500, "Drama", 90)
        with self.assertRaises(ValidacaoError):
            Filme("A", 2000, "Drama", 0)
        with self.assertRaises(ValidacaoError):
            Jogo("A", 2000, " ")


class TestLocacao(unittest.TestCase):
    def setUp(self):
        self.cli = Cliente("Ana", "12345678901", "Rua A", "1", "Brasília", "DF", id=1)
        self.fun = Funcionario("Bia", "98765432100", id=1)
        self.filme = Filme("Matrix", 1999, "Ficção", 136, id=1)
        self.jogo = Jogo("Zelda", 2023, "Switch", id=2)
        self.loc = Locacao(self.cli, self.fun, date(2026, 10, 1))

    def test_total_e_data_prevista(self):
        self.loc.adicionar_item(self.filme, 2)
        self.loc.adicionar_item(self.jogo, 5)
        self.assertEqual(self.loc.total, 57.0)
        self.assertEqual(self.loc.itens[0].data_prevista, date(2026, 10, 3))
        self.assertFalse(self.filme.disponivel)

    def test_item_indisponivel(self):
        self.filme.emprestar()
        with self.assertRaises(RegraNegocioError):
            self.loc.adicionar_item(self.filme, 1)

    def test_item_duplicado(self):
        self.loc.adicionar_item(self.filme, 1)
        with self.assertRaises(RegraNegocioError):
            self.loc.adicionar_item(self.filme, 1)

    def test_dias_invalidos_nao_prende_item(self):
        with self.assertRaises(ValidacaoError):
            self.loc.adicionar_item(self.filme, 0)
        self.assertTrue(self.filme.disponivel)

    def test_devolucao_no_prazo_sem_multa(self):
        self.loc.adicionar_item(self.filme, 3)
        self.loc.devolver(date(2026, 10, 4))
        self.assertEqual(self.loc.multa, 0.0)
        self.assertTrue(self.loc.devolvida)
        self.assertTrue(self.filme.disponivel)

    def test_devolucao_atrasada_com_multa(self):
        self.loc.adicionar_item(self.filme, 2)   # prazo 03/10, 7 dias de atraso * 2,00
        self.loc.adicionar_item(self.jogo, 5)    # prazo 06/10, 4 dias de atraso * 4,00
        self.loc.devolver(date(2026, 10, 10))
        self.assertEqual(self.loc.multa, 30.0)

    def test_devolucao_invalida(self):
        self.loc.adicionar_item(self.filme, 2)
        with self.assertRaises(ValidacaoError):
            self.loc.devolver(date(2026, 9, 1))
        self.loc.devolver(date(2026, 10, 2))
        with self.assertRaises(RegraNegocioError):
            self.loc.devolver(date(2026, 10, 3))
        with self.assertRaises(RegraNegocioError):
            self.loc.adicionar_item(self.jogo, 1)


class TestRecibo(unittest.TestCase):
    def test_recibo_com_devolucao(self):
        cli = Cliente("Ana", "12345678901", "Rua A", "1", "Brasília", "DF", id=1)
        fun = Funcionario("Bia", "98765432100", id=1)
        loc = Locacao(cli, fun, date(2026, 10, 1), id=7)
        loc.adicionar_item(Filme("Matrix", 1999, "Ficção", 136, id=1), 2)
        texto = Recibo.gerar(loc)
        self.assertIn("RECIBO DE LOCAÇÃO Nº 7", texto)
        self.assertIn("TOTAL      : R$ 12.00", texto)
        loc.devolver(date(2026, 10, 5))
        texto = Recibo.gerar(loc)
        self.assertIn("Multa      : R$ 4.00", texto)
        self.assertIn("TOTAL      : R$ 16.00", texto)


if __name__ == "__main__":
    unittest.main()
