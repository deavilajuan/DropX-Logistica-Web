import pytest

from app import create_app


@pytest.fixture()
def app(tmp_path, monkeypatch):
    """App con una base de datos SQLite temporal y aislada por prueba."""
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setenv('SECRET_KEY', 'clave-de-prueba')
    monkeypatch.setenv('WHATSAPP_ADVISOR_NUMBER', '573001112233')
    flask_app = create_app()
    flask_app.config.update(TESTING=True)
    return flask_app


@pytest.fixture()
def client(app):
    return app.test_client()


def _login(client, email, password):
    return client.post('/suite/login', data={'email': email, 'password': password})


@pytest.fixture()
def admin(client):
    _login(client, 'admin@dropx.com', 'admin123')
    return client


@pytest.fixture()
def logistico(client):
    _login(client, 'logistica@dropx.com', 'logistica123')
    return client
