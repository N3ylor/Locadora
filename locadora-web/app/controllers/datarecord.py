"""DataRecord: persistência de contas de usuário e sessões do Portal (BMVC).

* As contas ficam no SQLite (tabela ``users``) com a senha em hash PBKDF2.
* O administrador é sincronizado a partir das variáveis de ambiente
  ADMIN_USERNAME / ADMIN_PASSWORD a cada inicialização.
* Os clientes são cadastrados pelo administrador (API ``/api/clientes``).
* As sessões ficam em memória, com validade (TTL) controlada pelo servidor.
"""
import secrets
import sqlite3
import threading
import time

from app.models.user_account import ADMIN, CLIENTE, UserAccount


def _conta(row):
    return UserAccount(row['username'], row['password'], row['role'], row['nome'])


class DataRecord:
    def __init__(self, database, config, clock=time.monotonic):
        self._db = database
        self._config = config
        self._clock = clock
        self._lock = threading.Lock()
        self._sessions = {}  # session_id -> (username, expira_em)
        # Conta "fantasma" usada para gastar o mesmo tempo quando o usuário não existe
        # (evita descobrir nomes de usuário válidos pelo tempo de resposta).
        self._dummy = UserAccount.from_plain('-', secrets.token_hex(8), config.pbkdf2_iterations)
        self._sync_admin()

    # ---------- administrador (vem do ambiente) ----------
    def _sync_admin(self):
        cfg = self._config
        atual = self.find_user(cfg.admin_username)
        if atual is None:
            conta = UserAccount.from_plain(cfg.admin_username, cfg.admin_password,
                                           cfg.pbkdf2_iterations, ADMIN, cfg.admin_username)
            with self._db.connection() as db:
                db.execute('INSERT INTO users(username, password, role, nome) VALUES (?, ?, ?, ?)',
                           (conta.username, conta.password, ADMIN, conta.nome))
        elif not atual.check_password(cfg.admin_password) or atual.role != ADMIN:
            conta = UserAccount.from_plain(cfg.admin_username, cfg.admin_password,
                                           cfg.pbkdf2_iterations, ADMIN)
            with self._db.connection() as db:
                db.execute('UPDATE users SET password = ?, role = ? WHERE username = ?',
                           (conta.password, ADMIN, conta.username))
            self._purge_sessions(cfg.admin_username)

    def find_user(self, username):
        with self._db.connection() as db:
            row = db.execute('SELECT username, password, role, nome FROM users WHERE username = ?',
                             (username,)).fetchone()
        return _conta(row) if row else None

    # ---------- clientes (CRUD feito pelo administrador) ----------
    def listar_clientes(self):
        with self._db.connection() as db:
            rows = db.execute("SELECT username, password, role, nome FROM users "
                              "WHERE role = ? ORDER BY username", (CLIENTE,)).fetchall()
        return [_conta(r) for r in rows]

    def obter_cliente(self, username):
        conta = self.find_user(username)
        return conta if conta and conta.role == CLIENTE else None

    def criar_cliente(self, username, nome, senha):
        """Retorna a conta criada ou None se o username já estiver em uso (sem distinguir maiúsculas)."""
        conta = UserAccount.from_plain(username, senha, self._config.pbkdf2_iterations, CLIENTE, nome)
        try:
            with self._db.connection() as db:
                if db.execute('SELECT 1 FROM users WHERE lower(username) = ?', (username,)).fetchone():
                    return None
                db.execute('INSERT INTO users(username, password, role, nome) VALUES (?, ?, ?, ?)',
                           (username, conta.password, CLIENTE, nome))
        except sqlite3.IntegrityError:
            return None
        return conta

    def atualizar_cliente(self, username, nome=None, senha=None):
        atual = self.obter_cliente(username)
        if atual is None:
            return None
        if nome is not None:
            with self._db.connection() as db:
                db.execute('UPDATE users SET nome = ? WHERE username = ?', (nome, username))
        if senha is not None:
            nova = UserAccount.from_plain(username, senha, self._config.pbkdf2_iterations)
            with self._db.connection() as db:
                db.execute('UPDATE users SET password = ? WHERE username = ?', (nova.password, username))
            self._purge_sessions(username)  # a senha mudou: derruba os logins existentes
        return self.obter_cliente(username)

    def excluir_cliente(self, username):
        if self.obter_cliente(username) is None:
            return False
        with self._db.connection() as db:
            db.execute('DELETE FROM users WHERE username = ? AND role = ?', (username, CLIENTE))
        self._purge_sessions(username)
        return True

    # ---------- autenticação / sessões ----------
    def check_user(self, username, password):
        """Valida as credenciais. Retorna um novo session_id ou None."""
        conta = self.find_user(username)
        if conta is None:
            self._dummy.check_password(password)
            return None
        if not conta.check_password(password):
            return None
        session_id = secrets.token_urlsafe(32)  # novo a cada login (evita fixação de sessão)
        with self._lock:
            self._prune()
            self._sessions[session_id] = (conta.username, self._clock() + self._config.session_ttl)
        return session_id

    def get_user_by_session_id(self, session_id):
        """Conta (com perfil) dona da sessão, ou None se inválida, expirada ou conta removida."""
        if not session_id:
            return None
        with self._lock:
            item = self._sessions.get(session_id)
            if item is None:
                return None
            username, expira_em = item
            if expira_em <= self._clock():
                del self._sessions[session_id]
                return None
        conta = self.find_user(username)
        if conta is None:
            self.logout(session_id)
        return conta

    def get_username_by_session_id(self, session_id):
        conta = self.get_user_by_session_id(session_id)
        return conta.username if conta else None

    def logout(self, session_id):
        with self._lock:
            self._sessions.pop(session_id, None)

    def _purge_sessions(self, username):
        with self._lock:
            for sid in [s for s, (u, _) in self._sessions.items() if u == username]:
                del self._sessions[sid]

    def _prune(self):
        agora = self._clock()
        for sid in [s for s, (_, exp) in self._sessions.items() if exp <= agora]:
            del self._sessions[sid]
