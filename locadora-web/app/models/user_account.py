"""Modelo de conta de usuário (recurso Portal).

Mantém a interface do BMVC (``username`` e ``password``), mas o atributo
``password`` guarda **apenas o hash** PBKDF2-SHA256 com sal aleatório, no formato
``pbkdf2_sha256$iteracoes$sal_base64$hash_base64``. A senha em texto puro
nunca é armazenada. ``role`` define o perfil: ``admin`` ou ``cliente``.
"""
import base64
import secrets
from hashlib import pbkdf2_hmac
from hmac import compare_digest

ALGORITHM = 'pbkdf2_sha256'
ADMIN = 'admin'
CLIENTE = 'cliente'


def _b64(data):
    return base64.b64encode(data).decode('ascii')


class UserAccount:
    def __init__(self, username, password, role=CLIENTE, nome=''):
        self.username = username
        self.password = password  # hash, nunca texto puro
        self.role = role          # 'admin' ou 'cliente'
        self.nome = nome or username

    @property
    def is_admin(self):
        return self.role == ADMIN

    def to_dict(self):
        """Dados públicos (nunca inclui o hash)."""
        return {'username': self.username, 'nome': self.nome, 'role': self.role}

    @classmethod
    def from_plain(cls, username, plain_password, iterations, role=CLIENTE, nome=''):
        salt = secrets.token_bytes(16)
        digest = pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt, iterations)
        return cls(username, f'{ALGORITHM}${iterations}${_b64(salt)}${_b64(digest)}', role, nome)

    def check_password(self, plain_password):
        """Compara em tempo constante. Retorna False para hash malformado."""
        try:
            algorithm, iterations, salt_b64, hash_b64 = self.password.split('$')
            if algorithm != ALGORITHM:
                return False
            expected = base64.b64decode(hash_b64)
            digest = pbkdf2_hmac('sha256', plain_password.encode('utf-8'),
                                 base64.b64decode(salt_b64), int(iterations))
        except (ValueError, TypeError):
            return False
        return compare_digest(digest, expected)


# Alias com o nome citado no enunciado ("User_account").
User_account = UserAccount
