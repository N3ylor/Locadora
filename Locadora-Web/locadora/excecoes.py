class LocadoraError(Exception):
    pass


class ValidacaoError(LocadoraError):
    pass


class NaoEncontradoError(LocadoraError):
    pass


class RegraNegocioError(LocadoraError):
    pass
