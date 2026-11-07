"""Configuração (fail-fast) e modelos."""
import pytest
from decimal import Decimal

from app.config import Config, ConfigError
from app.models.filme import Filme, ValidationError
from app.models.user_account import UserAccount, User_account


@pytest.mark.parametrize('senha', ['', 'curta', 'defina-uma-senha-forte-aqui', 'troque-esta-senha'])
def test_config_recusa_senha_ausente_fraca_ou_de_exemplo(senha):
    with pytest.raises(ConfigError):
        Config(admin_username='admin', admin_password=senha)


def test_config_from_env_sem_senha_falha(monkeypatch):
    monkeypatch.delenv('ADMIN_PASSWORD', raising=False)
    with pytest.raises(ConfigError):
        Config.from_env()


def test_config_lida_do_ambiente(monkeypatch, tmp_path):
    monkeypatch.setenv('ADMIN_USERNAME', 'prof')
    monkeypatch.setenv('ADMIN_PASSWORD', 'uma-senha-boa-1')
    monkeypatch.setenv('DB_PATH', str(tmp_path / 'x.db'))
    monkeypatch.setenv('COOKIE_SECURE', 'true')
    cfg = Config.from_env()
    assert (cfg.admin_username, cfg.cookie_secure, cfg.db_path.name) == ('prof', True, 'x.db')


def test_hash_de_senha_e_salgado_e_verificavel():
    a = UserAccount.from_plain('u', 'segredo', 1000)
    b = UserAccount.from_plain('u', 'segredo', 1000)
    assert a.password != b.password and 'segredo' not in a.password
    assert a.check_password('segredo') and not a.check_password('outra')
    assert not UserAccount('u', 'lixo').check_password('segredo')
    assert User_account is UserAccount


def test_filme_validar_normaliza_valores():
    assert Filme.validar({'titulo': ' A ', 'genero': 'B', 'valor_diaria': '5'}) == ('A', 'B', Decimal('5.00'))


def test_filme_validar_acumula_erros():
    with pytest.raises(ValidationError) as e:
        Filme.validar({'titulo': '', 'genero': 1, 'valor_diaria': 'x'})
    assert set(e.value.campos) == {'titulo', 'genero', 'valor_diaria'}
