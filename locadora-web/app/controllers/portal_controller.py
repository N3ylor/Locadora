"""Controlador do recurso Portal: login, logout e consulta do usuário autenticado."""
import threading
import time

from bottle import redirect, request, template

from app.controllers.errors import ApiError

USERNAME_MAX = 256
PASSWORD_MAX = 1024


class LoginThrottle:
    """Bloqueio temporário após falhas consecutivas (proteção contra força bruta).

    A chave combina IP de origem e nome de usuário.
    """

    def __init__(self, max_attempts, lockout_seconds, clock=time.monotonic):
        self._max = max_attempts
        self._lockout = lockout_seconds
        self._clock = clock
        self._lock = threading.Lock()
        self._state = {}  # chave -> [falhas, bloqueado_ate]

    def remaining(self, key):
        """Segundos restantes de bloqueio (0 se liberado)."""
        with self._lock:
            item = self._state.get(key)
            if not item or not item[1]:
                return 0
            falta = item[1] - self._clock()
            if falta <= 0:
                del self._state[key]  # bloqueio expirou
                return 0
            return int(falta) + 1

    def failure(self, key):
        with self._lock:
            if len(self._state) > 10_000:  # limite de memória
                self._state.clear()
            item = self._state.setdefault(key, [0, 0.0])
            item[0] += 1
            if item[0] >= self._max:
                item[1] = self._clock() + self._lockout
                item[0] = 0

    def success(self, key):
        with self._lock:
            self._state.pop(key, None)


class PortalController:
    def __init__(self, models, config):
        self.models = models  # DataRecord
        self.config = config
        self.throttle = LoginThrottle(config.login_max_attempts, config.login_lockout_seconds)

    # ---------- sessão ----------
    def get_session_id(self):
        return request.get_cookie('session_id')

    def current_account(self):
        """Conta (com perfil) da sessão atual, ou None."""
        return self.models.get_user_by_session_id(self.get_session_id())

    def current_user(self):
        conta = self.current_account()
        return conta.username if conta else None

    @staticmethod
    def destino(conta):
        """Página inicial de cada perfil."""
        return '/banco' if conta.is_admin else '/cliente'

    # ---------- controle de acesso da API ----------
    def require_user(self):
        conta = self.current_account()
        if not conta:
            raise ApiError(401, 'Autenticação necessária. Faça login em /portal e envie o cookie de sessão.')
        return conta

    def require_admin(self):
        conta = self.require_user()
        if not conta.is_admin:
            raise ApiError(403, 'Acesso restrito a administradores.')
        return conta

    # ---------- páginas ----------
    def portal(self, error=None):
        conta = self.current_account()
        if conta and not error:
            redirect(self.destino(conta))
        return template('portal', error=error)

    # ---------- ações ----------
    def authenticate_user(self, username, password, client_ip):
        """Retorna ``(session_id, mensagem_de_erro, status_http, destino)``."""
        username = (username or '').strip()
        password = password or ''
        if not username or not password or len(username) > USERNAME_MAX or len(password) > PASSWORD_MAX:
            return None, 'Informe usuário e senha.', 400, None
        key = (client_ip, username.lower())
        espera = self.throttle.remaining(key)
        if espera:
            return None, f'Muitas tentativas. Tente novamente em {espera} s.', 429, None
        session_id = self.models.check_user(username, password)
        if session_id is None:
            self.throttle.failure(key)
            return None, 'Usuário ou senha incorretos.', 401, None
        self.throttle.success(key)
        return session_id, None, 200, self.destino(self.models.get_user_by_session_id(session_id))

    def logout_user(self):
        session_id = self.get_session_id()
        if session_id:
            self.models.logout(session_id)
