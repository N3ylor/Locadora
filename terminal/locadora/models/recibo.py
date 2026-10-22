from .locacao import Locacao


class Recibo:
    """DEPENDÊNCIA: usa uma Locacao apenas como parâmetro de método,
    sem guardá-la como atributo."""

    @staticmethod
    def gerar(locacao: Locacao) -> str:
        linhas = [
            "=" * 46,
            f"RECIBO DE LOCAÇÃO Nº {locacao.id}",
            "=" * 46,
            f"Cliente    : {locacao.cliente.nome}",
            f"Atendente  : {locacao.funcionario.nome}",
            f"Data       : {locacao.data_locacao:%d/%m/%Y}",
            "-" * 46,
        ]
        for il in locacao.itens:
            linhas.append(f"{il.item.titulo[:24]:<24} {il.dias:>2}d  R$ {il.valor:>7.2f}")
            linhas.append(f"   devolver até {il.data_prevista:%d/%m/%Y}")
        linhas.append("-" * 46)
        linhas.append(f"Subtotal   : R$ {locacao.total:.2f}")
        if locacao.devolvida:
            linhas.append(f"Devolvido  : {locacao.data_devolucao:%d/%m/%Y}")
            linhas.append(f"Multa      : R$ {locacao.multa:.2f}")
        linhas.append(f"TOTAL      : R$ {locacao.total + locacao.multa:.2f}")
        linhas.append("=" * 46)
        return "\n".join(linhas)
