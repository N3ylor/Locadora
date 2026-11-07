"""Configuração da aplicação, lida de variáveis de ambiente (arquivo .env no Docker).

Nenhuma credencial fica no código-fonte: o usuário inicial vem de
ADMIN_USERNAME / ADMIN_PASSWORD.
"""
import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
VIEWS_DIR = BASE_DIR / 'app' / 'views' / 'html'
STATIC_DIR = BASE_DIR / 'app' / 'static'
DEFAULT_DB_PATH = BASE_DIR / 'app' / 'controllers' / 'db' / 'locadora.db'

# Valores de exemplo que nunca devem ser aceitos como senha real.
PLACEHOLDER_PASSWORDS = {'defina-uma-senha-forte-aqui', 'troque-esta-senha', 'changeme', 'password'}


class ConfigError(RuntimeError):
    """Configuração inválida ou ausente (a aplicação se recusa a iniciar)."""


def _env_bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in ('1', 'true', 'yes', 'sim')


def _env_int(name, default):
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        raise ConfigError(f'A variável {name} deve ser um número inteiro.')


@dataclass(frozen=True)
class Config:
    admin_username: str
    admin_password: str
    db_path: Path = DEFAULT_DB_PATH
    cookie_secure: bool = False
    session_ttl: int = 3600            # segundos de validade da sessão (cookie e servidor)
    pbkdf2_iterations: int = 600_000   # custo do hash de senha (OWASP 2023 p/ PBKDF2-SHA256)
    login_max_attempts: int = 5        # falhas consecutivas antes do bloqueio temporário
    login_lockout_seconds: int = 300
    port: int = 8080
    timezone: str = 'America/Sao_Paulo'  # define o "hoje" das locações e da multa

    def __post_init__(self):
        if not self.admin_username or len(self.admin_username) > 64:
            raise ConfigError('ADMIN_USERNAME deve ter de 1 a 64 caracteres.')
        if (len(self.admin_password) < 8
                or self.admin_password.lower() in PLACEHOLDER_PASSWORDS):
            raise ConfigError(
                'ADMIN_PASSWORD ausente, curta (mínimo 8 caracteres) ou igual ao valor de exemplo. '
                'Copie .env.example para .env e defina uma senha própria.')

    @classmethod
    def from_env(cls):
        return cls(
            admin_username=os.environ.get('ADMIN_USERNAME', 'admin').strip(),
            admin_password=os.environ.get('ADMIN_PASSWORD', ''),
            db_path=Path(os.environ.get('DB_PATH') or DEFAULT_DB_PATH),
            cookie_secure=_env_bool('COOKIE_SECURE'),
            session_ttl=_env_int('SESSION_TTL', 3600),
            pbkdf2_iterations=_env_int('PBKDF2_ITERATIONS', 600_000),
            login_max_attempts=_env_int('LOGIN_MAX_ATTEMPTS', 5),
            login_lockout_seconds=_env_int('LOGIN_LOCKOUT_SECONDS', 300),
            port=_env_int('PORT', 8080),
            timezone=os.environ.get('TIMEZONE', 'America/Sao_Paulo').strip(),
        )
