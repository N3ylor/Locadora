"""Fixtures dos testes: cada teste usa um SQLite temporário e isolado."""
import os
import sys
import tempfile
from pathlib import Path

# Antes de importar route.py (que cria uma Application a partir do ambiente).
_TMP = tempfile.mkdtemp(prefix='locadora-tests-')
os.environ.update({
    'ADMIN_USERNAME': 'admin',
    'ADMIN_PASSWORD': 'senha-de-teste-123',
    'DB_PATH': str(Path(_TMP) / 'import.db'),
    'PBKDF2_ITERATIONS': '1000',  # hash rápido só nos testes
})
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from webtest import TestApp

from app.config import Config
from app.controllers.application import Application
from route import create_app

USER, PASSWORD = 'admin', 'senha-de-teste-123'


def make_config(tmp_path, **extra):
    base = dict(admin_username=USER, admin_password=PASSWORD, db_path=tmp_path / 'locadora.db',
                pbkdf2_iterations=1000)
    base.update(extra)
    return Config(**base)


@pytest.fixture
def config(tmp_path):
    return make_config(tmp_path)


@pytest.fixture
def ctl(config):
    return Application(config)


@pytest.fixture
def client(ctl):
    """Cliente HTTP anônimo (sem login)."""
    return TestApp(create_app(ctl))


@pytest.fixture
def auth(client):
    """Cliente já autenticado (mantém o cookie de sessão)."""
    resp = client.post('/portal', {'username': USER, 'password': PASSWORD})
    assert resp.status_int == 302
    return client


FILME = {'titulo': 'Matrix', 'genero': 'Ficção científica', 'valor_diaria': 5.00}
