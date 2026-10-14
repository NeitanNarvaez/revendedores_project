"""Opt-in test against a dedicated Oracle test schema, never a production schema."""

import os
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database.connection import get_connection

pytestmark = [
    pytest.mark.oracle,
    pytest.mark.skipif(
        os.getenv("RUN_ORACLE_TESTS") != "1",
        reason="Oracle no habilitado; consulta docs/PRUEBAS.md",
    ),
]


def test_flujo_real_oracle():
    email = os.getenv("TEST_ADMIN_EMAIL")
    password = os.getenv("TEST_ADMIN_PASSWORD")
    if not email or not password:
        pytest.fail(
            "Configura TEST_ADMIN_EMAIL y TEST_ADMIN_PASSWORD de tu esquema de pruebas"
        )
    ids = {}
    unique = "Prueba-" + uuid4().hex[:10]
    with TestClient(app, raise_server_exceptions=False) as client:
        login = client.post(
            "/api/auth/login", json={"correo": email, "contrasena": password}
        )
        assert login.status_code == 200, "No se pudo iniciar sesión en Oracle"
        assert login.json()["usuario"]["rol"] == "ADMINISTRADOR"
        client.headers["Authorization"] = "Bearer " + login.json()["access_token"]

        def create(path, body, key):
            response = client.post("/api/" + path, json=body)
            assert response.status_code == 201, response.text
            ids[key] = response.json()[key]
            return ids[key]

        try:
            supplier = create("proveedores", {"nombre": unique}, "id_proveedor")
            customer = create("clientes", {"nombre": unique}, "id_cliente")
            product = create(
                "productos",
                {
                    "id_proveedor": supplier,
                    "nombre": unique,
                    "precio_compra": 80,
                    "margen_porcentaje": 25,
                    "existencia": 2,
                },
                "id_producto",
            )
            response = client.put(
                f"/api/productos/{product}",
                json={
                    "id_proveedor": supplier,
                    "nombre": unique + " editado",
                    "precio_compra": 80,
                    "margen_porcentaje": 25,
                    "existencia": 2,
                },
            )
            assert response.status_code == 200
            assert any(
                row["id_producto"] == product
                for row in client.get("/api/productos", params={"q": unique}).json()
            )
            order = create("pedidos", {"id_cliente": customer}, "id_pedido")
            detail = {"id_pedido": order, "id_producto": product, "cantidad": 3}
            assert client.post("/api/detalle-pedidos", json=detail).status_code == 400
            detail["cantidad"] = 1
            line = create("detalle-pedidos", detail, "id_detalle")
            assert client.get(f"/api/productos/{product}").json()["existencia"] == 1
            assert (
                client.post(
                    "/api/pagos",
                    json={"id_pedido": order, "monto": 101, "metodo": "EFECTIVO"},
                ).status_code
                == 400
            )
            payment = create(
                "pagos",
                {"id_pedido": order, "monto": 50, "metodo": "EFECTIVO"},
                "id_pago",
            )
            detail["cantidad"] = 2
            assert (
                client.put(f"/api/detalle-pedidos/{line}", json=detail).status_code
                == 400
            )
            assert client.delete(f"/api/pagos/{payment}").status_code == 200
            assert (
                client.put(f"/api/detalle-pedidos/{line}", json=detail).status_code
                == 200
            )
            assert client.get(f"/api/productos/{product}").json()["existencia"] == 0
            assert client.get(f"/api/pedidos/{order}").json()["total"] == 200
            assert (
                client.put(
                    f"/api/pedidos/{order}",
                    json={"id_cliente": customer, "estado": "CANCELADO"},
                ).status_code
                == 200
            )
            assert client.get(f"/api/productos/{product}").json()["existencia"] == 2
            # Verify persistence through a separate database connection.
            conn = get_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT estado FROM pedidos WHERE id_pedido=:id", {"id": order}
                    )
                    assert cur.fetchone()[0] == "CANCELADO"
            finally:
                conn.close()
            for path in [
                "/api/dashboard",
                "/api/reportes/ventas-cliente",
                "/api/reportes/ventas-proveedor",
            ]:
                assert client.get(path).status_code == 200
            # An unreferenced temporary customer demonstrates physical CRUD deletion.
            response = client.post(
                "/api/clientes", json={"nombre": unique + " eliminar"}
            )
            assert response.status_code == 201
            ids["delete_customer"] = response.json()["id_cliente"]
            assert (
                client.delete(
                    "/api/clientes/" + str(ids["delete_customer"])
                ).status_code
                == 200
            )
            assert (
                client.get("/api/clientes/" + str(ids["delete_customer"])).status_code
                == 404
            )
        finally:
            # Only delete records whose generated IDs were obtained during this test.
            conn = get_connection()
            try:
                with conn.cursor() as cur:
                    if "id_pedido" in ids:
                        cur.execute(
                            "DELETE FROM pagos WHERE id_pedido=:id",
                            {"id": ids["id_pedido"]},
                        )
                        cur.execute(
                            "DELETE FROM pedidos WHERE id_pedido=:id",
                            {"id": ids["id_pedido"]},
                        )
                    for table, key in [
                        ("productos", "id_producto"),
                        ("clientes", "id_cliente"),
                        ("proveedores", "id_proveedor"),
                    ]:
                        if key in ids:
                            cur.execute(
                                f"DELETE FROM {table} WHERE {key}=:id", {"id": ids[key]}
                            )
                    if "delete_customer" in ids:
                        cur.execute(
                            "DELETE FROM clientes WHERE id_cliente=:id",
                            {"id": ids["delete_customer"]},
                        )
                conn.commit()
            finally:
                conn.close()
