import unittest
from datetime import date

from locadora.database import Database
from locadora.excecoes import NaoEncontradoError, RegraNegocioError, ValidacaoError
from locadora.models import Filme, Jogo
from locadora.servicos import Locadora


class BaseTeste(unittest.TestCase):
    def setUp(self):
        self.db = Database(":memory:")
        self.s = Locadora(self.db)
        self.cli = self.s.cadastrar_cliente("Ana", "123.456.789-01", "Rua A", "10", "Brasília", "df")
        self.fun = self.s.cadastrar_funcionario("Bruno", "98765432100")
        self.filme = self.s.cadastrar_filme("Matrix", 1999, "Ficção", 136)
        self.jogo = self.s.cadastrar_jogo("Zelda", 2023, "Switch")

    def tearDown(self):
        self.db.fechar()


class TestClientes(BaseTeste):
    def test_cadastrar_e_buscar(self):
        c = self.s.clientes.buscar(self.cli.id)
        self.assertEqual((c.nome, c.cpf, c.endereco.uf), ("Ana", "12345678901", "DF"))

    def test_listar(self):
        self.s.cadastrar_cliente("Zeca", "11122233344", "Rua B", "2", "Gama", "DF")
        self.assertEqual([c.nome for c in self.s.listar_clientes()], ["Ana", "Zeca"])

    def test_cpf_duplicado(self):
        with self.assertRaises(RegraNegocioError):
            self.s.cadastrar_cliente("Outra", "12345678901", "Rua", "1", "Cidade", "DF")

    def test_cadastro_invalido_nao_grava(self):
        with self.assertRaises(ValidacaoError):
            self.s.cadastrar_cliente("", "12345678901", "Rua", "1", "Cidade", "DF")
        self.assertEqual(len(self.s.listar_clientes()), 1)

    def test_atualizar(self):
        self.s.atualizar_cliente(self.cli.id, "Ana Maria", "12345678901", "Rua Z", "5", "Gama", "GO")
        c = self.s.clientes.buscar(self.cli.id)
        self.assertEqual((c.nome, c.endereco.cidade, c.endereco.uf), ("Ana Maria", "Gama", "GO"))

    def test_atualizar_inexistente(self):
        with self.assertRaises(NaoEncontradoError):
            self.s.atualizar_cliente(999, "X", "12345678901", "R", "1", "C", "DF")

    def test_remover(self):
        self.s.remover_cliente(self.cli.id)
        self.assertIsNone(self.s.clientes.buscar(self.cli.id))
        with self.assertRaises(NaoEncontradoError):
            self.s.remover_cliente(self.cli.id)

    def test_remover_com_locacao_bloqueado(self):
        self.s.alugar(self.cli.id, self.fun.id, [(self.filme.id, 1)])
        with self.assertRaises(RegraNegocioError):
            self.s.remover_cliente(self.cli.id)


class TestFuncionarios(BaseTeste):
    def test_crud(self):
        f2 = self.s.cadastrar_funcionario("Carla", "55566677788", "Gerente")
        self.assertEqual(self.s.funcionarios.buscar(f2.id).cargo, "Gerente")
        self.s.atualizar_funcionario(f2.id, "Carla S.", "55566677788", "Diretora")
        self.assertEqual(self.s.funcionarios.buscar(f2.id).cargo, "Diretora")
        self.assertEqual(len(self.s.listar_funcionarios()), 2)
        self.s.remover_funcionario(f2.id)
        self.assertEqual(len(self.s.listar_funcionarios()), 1)

    def test_cpf_duplicado(self):
        with self.assertRaises(RegraNegocioError):
            self.s.cadastrar_funcionario("Outro", "98765432100")

    def test_remover_inexistente(self):
        with self.assertRaises(NaoEncontradoError):
            self.s.remover_funcionario(999)


class TestAcervo(BaseTeste):
    def test_persistencia_polimorfica(self):
        self.assertIsInstance(self.s.itens.buscar(self.filme.id), Filme)
        self.assertIsInstance(self.s.itens.buscar(self.jogo.id), Jogo)
        self.assertEqual(self.s.itens.buscar(self.jogo.id).plataforma, "Switch")

    def test_listar_disponiveis(self):
        self.assertEqual(len(self.s.listar_itens()), 2)
        self.s.alugar(self.cli.id, self.fun.id, [(self.filme.id, 1)])
        self.assertEqual([i.titulo for i in self.s.listar_itens(True)], ["Zelda"])

    def test_remover_item(self):
        self.s.remover_item(self.jogo.id)
        self.assertIsNone(self.s.itens.buscar(self.jogo.id))

    def test_remover_item_alugado_bloqueado(self):
        self.s.alugar(self.cli.id, self.fun.id, [(self.filme.id, 1)])
        with self.assertRaises(RegraNegocioError):
            self.s.remover_item(self.filme.id)

    def test_atualizar_item(self):
        f = self.s.itens.buscar(self.filme.id)
        f.titulo = "Matrix Reloaded"
        self.s.itens.atualizar(f)
        self.assertEqual(self.s.itens.buscar(f.id).titulo, "Matrix Reloaded")

    def test_atualizar_item_pelo_servico(self):
        self.s.atualizar_item(self.jogo.id, Jogo("Zelda 2", 2024, "PC"))
        salvo = self.s.itens.buscar(self.jogo.id)
        self.assertEqual((salvo.titulo, salvo.plataforma), ("Zelda 2", "PC"))

    def test_atualizar_item_mantem_disponibilidade_e_barra_troca_de_tipo(self):
        self.s.alugar(self.cli.id, self.fun.id, [(self.filme.id, 1)])
        self.s.atualizar_item(self.filme.id, Filme("Matrix 2", 2003, "Ficção", 138))
        self.assertFalse(self.s.itens.buscar(self.filme.id).disponivel)
        with self.assertRaises(RegraNegocioError):
            self.s.atualizar_item(self.filme.id, Jogo("X", 2020, "PC"))
        with self.assertRaises(NaoEncontradoError):
            self.s.atualizar_item(999, Jogo("X", 2020, "PC"))


class TestLocacoes(BaseTeste):
    def test_alugar_persiste_e_indisponibiliza(self):
        loc = self.s.alugar(self.cli.id, self.fun.id, [(self.filme.id, 2), (self.jogo.id, 5)], date(2026, 10, 1))
        salva = self.s.locacoes.buscar(loc.id)
        self.assertEqual(salva.total, 57.0)
        self.assertEqual(len(salva.itens), 2)
        self.assertEqual(salva.cliente.nome, "Ana")
        self.assertFalse(self.s.itens.buscar(self.filme.id).disponivel)

    def test_item_ja_alugado(self):
        self.s.alugar(self.cli.id, self.fun.id, [(self.filme.id, 1)])
        with self.assertRaises(RegraNegocioError):
            self.s.alugar(self.cli.id, self.fun.id, [(self.filme.id, 1)])

    def test_falha_nao_deixa_item_preso(self):
        with self.assertRaises(NaoEncontradoError):
            self.s.alugar(self.cli.id, self.fun.id, [(self.filme.id, 1), (999, 1)])
        self.assertTrue(self.s.itens.buscar(self.filme.id).disponivel)
        self.assertEqual(self.s.listar_locacoes(), [])

    def test_limite_de_itens(self):
        extras = [self.s.cadastrar_jogo(f"J{i}", 2020, "PC") for i in range(3)]
        self.s.alugar(self.cli.id, self.fun.id, [(self.filme.id, 1), (self.jogo.id, 1)])
        with self.assertRaises(RegraNegocioError):
            self.s.alugar(self.cli.id, self.fun.id, [(extras[0].id, 1), (extras[1].id, 1)])
        self.s.alugar(self.cli.id, self.fun.id, [(extras[0].id, 1)])

    def test_pedido_vazio_cliente_e_funcionario_inexistentes(self):
        with self.assertRaises(ValidacaoError):
            self.s.alugar(self.cli.id, self.fun.id, [])
        with self.assertRaises(NaoEncontradoError):
            self.s.alugar(999, self.fun.id, [(self.filme.id, 1)])
        with self.assertRaises(NaoEncontradoError):
            self.s.alugar(self.cli.id, 999, [(self.filme.id, 1)])

    def test_devolver_com_multa_e_liberar_itens(self):
        loc = self.s.alugar(self.cli.id, self.fun.id, [(self.filme.id, 2), (self.jogo.id, 5)], date(2026, 10, 1))
        recibo = self.s.devolver(loc.id, date(2026, 10, 10))
        self.assertIn("Multa      : R$ 30.00", recibo)
        self.assertIn("TOTAL      : R$ 87.00", recibo)
        self.assertTrue(self.s.itens.buscar(self.filme.id).disponivel)
        self.assertTrue(self.s.itens.buscar(self.jogo.id).disponivel)
        self.assertTrue(self.s.locacoes.buscar(loc.id).devolvida)
        self.assertEqual(self.s.locacoes.buscar(loc.id).multa, 30.0)

    def test_devolver_duas_vezes(self):
        loc = self.s.alugar(self.cli.id, self.fun.id, [(self.filme.id, 2)], date(2026, 10, 1))
        self.s.devolver(loc.id, date(2026, 10, 2))
        with self.assertRaises(RegraNegocioError):
            self.s.devolver(loc.id, date(2026, 10, 3))

    def test_devolver_inexistente(self):
        with self.assertRaises(NaoEncontradoError):
            self.s.devolver(999)

    def test_listagens_e_recibo(self):
        l1 = self.s.alugar(self.cli.id, self.fun.id, [(self.filme.id, 1)], date(2026, 10, 1))
        self.s.alugar(self.cli.id, self.fun.id, [(self.jogo.id, 1)], date(2026, 10, 1))
        self.s.devolver(l1.id, date(2026, 10, 2))
        self.assertEqual(len(self.s.listar_locacoes()), 2)
        self.assertEqual(len(self.s.listar_locacoes(apenas_abertas=True)), 1)
        self.assertIn("RECIBO DE LOCAÇÃO Nº", self.s.recibo(l1.id))
        with self.assertRaises(NaoEncontradoError):
            self.s.recibo(999)


if __name__ == "__main__":
    unittest.main()
