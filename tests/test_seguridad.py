from unittest.mock import MagicMock
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from backend import security
from backend.services import auth
from backend.schemas.common import LoginIn


@pytest.fixture
def account(monkeypatch):
    monkeypatch.setattr(
        security.settings, "jwt_secret", "test-secret-for-unit-tests-only-1234567890"
    )
    conn = MagicMock()
    cur = conn.cursor.return_value
    password = "Prueba-Segura-123"
    hashed = security.hash_password(password)
    cur.fetchone.return_value = (2, "Ana", "ana@example.com", hashed, 1, "VENDEDOR")
    monkeypatch.setattr(auth, "get_connection", lambda: conn)
    return cur, password, hashed


def test_login_verifica_hash_y_emite_jwt(account):
    cur, password, hashed = account
    assert hashed != password
    assert security.verify_password(password, hashed)
    result = auth.login(LoginIn(correo="ana@example.com", contrasena=password))
    payload = security.jwt.decode(
        result["access_token"], security.settings.jwt_secret, algorithms=["HS256"]
    )
    assert payload["sub"] == "2"
    assert payload["role"] == "VENDEDOR"
    assert result["usuario"]["rol"] == "VENDEDOR"
    assert "hash_contrasena" not in result["usuario"]


@pytest.mark.parametrize(
    "active,password", [(1, "Incorrecta-123"), (0, "Prueba-Segura-123")]
)
def test_login_rechaza_clave_o_cuenta_inactiva(account, active, password):
    cur, _, hashed = account
    cur.fetchone.return_value = (
        2,
        "Ana",
        "ana@example.com",
        hashed,
        active,
        "VENDEDOR",
    )
    with pytest.raises(HTTPException) as error:
        auth.login(LoginIn(correo="ana@example.com", contrasena=password))
    assert error.value.status_code == 401


def test_token_no_permita_usuario_desactivado(account, monkeypatch):
    conn = MagicMock()
    cur = conn.cursor.return_value
    cur.fetchone.return_value = (2, "Ana", "ana@example.com", 2, "VENDEDOR", 0)
    monkeypatch.setattr(security, "get_connection", lambda: conn)
    token = security.create_access_token(2, "VENDEDOR")
    with pytest.raises(HTTPException) as error:
        security.get_current_user(
            HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        )
    assert error.value.status_code == 401
