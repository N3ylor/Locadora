"""Erros de domínio da API, convertidos em respostas JSON pelo route.py."""


class ApiError(Exception):
    def __init__(self, status, mensagem, campos=None, codigo=None):
        super().__init__(mensagem)
        self.status = status
        self.mensagem = mensagem
        self.campos = campos
        self.codigo = codigo  # usado pela interface web para escolher o aviso

    def to_dict(self):
        corpo = {'erro': self.mensagem}
        if self.campos:
            corpo['campos'] = self.campos
        return corpo
