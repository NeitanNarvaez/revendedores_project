from datetime import date
from unittest.mock import Mock
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.security import get_current_user
from backend.services import catalog, auth, reports

ADMIN = {"id_usuario": 1, "nombre": "Admin", "rol": "ADMINISTRADOR"}
SELLER = {"id_usuario": 2, "nombre": "Vendedor", "rol": "VENDEDOR"}


@pytest.fixture
def client():
    app.dependency_overrides.clear()
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
    app.dependency_overrides.clear()


def test_login_json_y_swagger_bearer(client, monkeypatch):
    login = Mock(return_value={"access_token": "test-token", "token_type": "bearer"})
    monkeypatch.setattr(auth, "login", login)
    response = client.post(
        "/api/auth/login", json={"correo": "user@example.com", "contrasena": "12345678"}
    )
    assert response.status_code == 200
    assert response.json()["access_token"] == "test-token"
    assert login.call_args.args[0].correo == "user@example.com"
    schema = client.get("/openapi.json").json()
    assert schema["components"]["securitySchemes"]["HTTPBearer"]["scheme"] == "bearer"


@pytest.mark.parametrize(
    "path",
    [
        "/api/productos",
        "/api/clientes",
        "/api/pedidos",
        "/api/dashboard",
        "/api/auth/usuarios",
    ],
)
def test_sin_token_401(client, path):
    assert client.get(path).status_code == 401


@pytest.mark.parametrize(
    "path,method",
    [
        ("/api/clientes/1", "delete"),
        ("/api/proveedores/1", "delete"),
        ("/api/productos/1", "delete"),
        ("/api/pagos/1", "delete"),
        ("/api/auth/usuarios", "get"),
    ],
)
def test_vendedor_no_puede_administrar(client, path, method):
    app.dependency_overrides[get_current_user] = lambda: SELLER
    assert getattr(client, method)(path).status_code == 403


def test_crud_catalogo_y_filtros(client, monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: ADMIN
    create = Mock(return_value={"id_cliente": 7, "nombre": "Ana"})
    update = Mock(return_value={"id_cliente": 7, "nombre": "Ana María"})
    lookup = Mock(return_value={"id_cliente": 7, "nombre": "Ana"})
    listing = Mock(return_value=[{"id_cliente": 7, "nombre": "Ana"}])
    delete = Mock(return_value={"mensaje": "Registro eliminado"})
    for name, impl in [
        ("_create", create),
        ("_update", update),
        ("_get", lookup),
        ("_list", listing),
        ("_delete", delete),
    ]:
        monkeypatch.setattr(catalog, name, impl)
    assert client.post("/api/clientes", json={"nombre": "Ana"}).status_code == 201
    assert client.get("/api/clientes/7").json()["id_cliente"] == 7
    assert (
        client.put("/api/clientes/7", json={"nombre": "Ana María"}).status_code == 200
    )
    assert client.get("/api/clientes?q=Ana").status_code == 200
    listing.assert_called_once_with("clientes", "Ana", None)
    assert client.delete("/api/clientes/7").status_code == 200


@pytest.mark.parametrize(
    "path,data",
    [
        (
            "/api/productos",
            {"id_proveedor": 1, "nombre": "Producto", "precio_compra": -1},
        ),
        ("/api/clientes", {"nombre": "  "}),
        ("/api/pagos", {"id_pedido": 1, "monto": -1, "metodo": "EFECTIVO"}),
        ("/api/detalle-pedidos", {"id_pedido": 1, "id_producto": 1, "cantidad": 0}),
    ],
)
def test_validaciones_422(client, path, data):
    app.dependency_overrides[get_current_user] = lambda: ADMIN
    assert client.post(path, json=data).status_code == 422


def test_validacion_no_expone_password(client):
    password = "a" * 73
    response = client.post(
        "/api/auth/register",
        json={"nombre": "Ana", "correo": "a@example.com", "contrasena": password},
    )
    assert response.status_code == 422
    assert password not in response.text
    assert "input" not in response.json()["detail"][0]


def test_fecha_invalida_y_periodo_invertido(client, monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: ADMIN
    assert (
        client.get("/api/reportes/ventas-periodo?desde=no&hasta=2026-01-01").status_code
        == 422
    )
    # The actual service validates before opening a connection.
    assert (
        client.get(
            "/api/reportes/ventas-periodo?desde=2026-02-01&hasta=2026-01-01"
        ).status_code
        == 400
    )
    spy = Mock(return_value=[])
    monkeypatch.setattr(reports, "ventas_periodo", spy)
    assert (
        client.get(
            "/api/reportes/ventas-periodo?desde=2026-01-01&hasta=2026-01-31"
        ).status_code
        == 200
    )
    spy.assert_called_once_with(date(2026, 1, 1), date(2026, 1, 31), ADMIN)


def test_error_interno_sin_detalles_y_frontend(client, monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: ADMIN
    monkeypatch.setattr(
        catalog, "_list", Mock(side_effect=RuntimeError("contraseña-secreta"))
    )
    response = client.get("/api/clientes")
    assert response.status_code == 500
    assert response.json() == {"detail": "Error interno del servidor"}
    assert client.get("/app/login.html").status_code == 200
    assert client.get("/app/index.html").status_code == 200
    assert client.get("/app/css/bootstrap.min.css").status_code == 200
