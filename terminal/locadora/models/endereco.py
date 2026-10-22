from ..excecoes import ValidacaoError


class Endereco:
    """Parte de um Cliente (COMPOSIÇÃO): só existe dentro de um cliente."""

    def __init__(self, rua, numero, cidade, uf):
        rua, numero, cidade, uf = (str(x or "").strip() for x in (rua, numero, cidade, uf))
        if not rua or not cidade:
            raise ValidacaoError("Rua e cidade são obrigatórias.")
        if len(uf) != 2 or not uf.isalpha():
            raise ValidacaoError("UF deve ter 2 letras.")
        self.rua = rua
        self.numero = numero or "S/N"
        self.cidade = cidade
        self.uf = uf.upper()

    def __str__(self):
        return f"{self.rua}, {self.numero} - {self.cidade}/{self.uf}"
