"""Optional browser checks with explicitly simulated API responses; no Oracle claim.
Start uvicorn on port 8000, install playwright and its chromium, then run this file.
"""

import json
import os
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import sync_playwright

BASE = os.getenv("UI_BASE_URL", "http://127.0.0.1:8000")
ROOT = Path(__file__).resolve().parents[1]


def run():
    clients = [
        {
            "id_cliente": 1,
            "nombre": "Cliente de prueba",
            "correo": "cliente@example.com",
            "telefono": "3001234567",
            "direccion": "Cali",
        }
    ]
    user = {
        "id_usuario": 1,
        "nombre": "Equipo Reventa",
        "rol": "ADMINISTRADOR",
        "correo": "admin@example.com",
    }
    suppliers = [
        {
            "id_proveedor": 1,
            "nombre": "Proveedor de prueba",
            "contacto": "María",
            "telefono": "3001234567",
            "correo": "proveedor@example.com",
            "activo": 1,
        }
    ]
    products = [
        {
            "id_producto": 1,
            "id_proveedor": 1,
            "nombre": "Camiseta deportiva",
            "precio_compra": 40000,
            "margen_porcentaje": 25,
            "precio_venta": 50000,
            "existencia": 12,
            "activo": 1,
            "descripcion": "Talla M",
        }
    ]
    orders = [
        {
            "id_pedido": 1,
            "id_cliente": 1,
            "id_usuario": 1,
            "cliente": "Cliente de prueba",
            "vendedor": "Equipo Reventa",
            "estado": "PENDIENTE",
            "fecha_pedido": "2026-10-14T12:00:00",
            "total": 100000,
            "observaciones": None,
        }
    ]
    payments = [
        {
            "id_pago": 1,
            "id_pedido": 1,
            "monto": 25000,
            "metodo": "EFECTIVO",
            "estado": "REGISTRADO",
            "fecha_pago": "2026-10-14T12:00:00",
            "referencia": None,
        }
    ]
    details = [
        {
            "id_detalle": 1,
            "id_pedido": 1,
            "id_producto": 1,
            "producto": "Camiseta deportiva",
            "cantidad": 2,
            "precio_unitario": 50000,
            "subtotal": 100000,
        }
    ]
    data = {
        "clientes": clients,
        "proveedores": suppliers,
        "productos": products,
        "pedidos": orders,
        "pagos": payments,
        "auth/usuarios": [dict(user, activo=1)],
        "detalle-pedidos": details,
    }

    def route_api(route):
        request = route.request
        url = urlparse(request.url)
        path = url.path.removeprefix("/api/")
        status = 200
        if path == "auth/login":
            result = {"access_token": "token-solo-prueba-ui", "token_type": "bearer"}
        elif path == "auth/me":
            result = user
        elif path == "dashboard":
            result = {
                "ventas_mes": 100000,
                "pedidos_pendientes": 1,
                "productos_mas_vendidos": [
                    {"producto": "Camiseta deportiva", "unidades": 2}
                ],
            }
        elif path.startswith("reportes/"):
            result = [
                {
                    "nombre": "Cliente de prueba",
                    "proveedor": "Proveedor de prueba",
                    "periodo": "2026-10",
                    "pedidos": 1,
                    "ventas": 100000,
                }
            ]
        else:
            resource = (
                path.rsplit("/", 1)[0] if path.rsplit("/", 1)[-1].isdigit() else path
            )
            rows = data.get(resource, [])
            pk = {
                "clientes": "id_cliente",
                "proveedores": "id_proveedor",
                "productos": "id_producto",
                "pedidos": "id_pedido",
                "pagos": "id_pago",
                "detalle-pedidos": "id_detalle",
                "auth/usuarios": "id_usuario",
            }.get(resource)
            item_id = (
                int(path.rsplit("/", 1)[-1])
                if path.rsplit("/", 1)[-1].isdigit()
                else None
            )
            if request.method == "POST":
                result = dict(request.post_data_json)
                result[pk] = max([r[pk] for r in rows] + [0]) + 1
                rows.append(result)
                status = 201
            elif request.method == "PUT":
                result = next(r for r in rows if r[pk] == item_id)
                result.update(request.post_data_json)
            elif request.method == "DELETE":
                rows[:] = [r for r in rows if r[pk] != item_id]
                result = {"mensaje": "Eliminado"}
            elif item_id is not None:
                result = next(r for r in rows if r[pk] == item_id)
                if resource == "pedidos":
                    result = dict(
                        result,
                        detalles=details,
                        pagos=payments,
                        pagado=25000,
                        saldo=75000,
                    )
            else:
                query = parse_qs(url.query).get("q", [""])[0].lower()
                result = [r for r in rows if query in r.get("nombre", "").lower()]
        route.fulfill(
            status=status, content_type="application/json", body=json.dumps(result)
        )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.route("**/api/**", route_api)
        page.goto(BASE + "/app/login.html")
        page.locator("#correo").fill("admin@example.com")
        page.locator("#contrasena").fill("password-test")
        page.get_by_role("button", name="Iniciar sesión").click()
        page.get_by_role("heading", name="Resumen de tu negocio").wait_for()
        page.screenshot(
            path=str(ROOT / "docs/evidencias/ui-desktop.png"), full_page=True
        )
        for module in [
            "proveedores",
            "productos",
            "clientes",
            "pedidos",
            "pagos",
            "reportes",
            "usuarios",
        ]:
            page.locator(f'[data-nav="{module}"]').click()
            page.get_by_role(
                "heading", name=resources_title(module), exact=True
            ).wait_for()
        page.locator('[data-nav="productos"]').click()
        page.get_by_role("heading", name="Productos", exact=True).wait_for()
        page.get_by_role("button", name="Editar", exact=True).first.click()
        page.locator("#field-nombre").fill("Camiseta editada")
        page.get_by_role("button", name="Guardar", exact=True).click()
        page.get_by_text("Registro guardado correctamente.", exact=True).wait_for()
        assert products[0]["nombre"] == "Camiseta editada"
        page.locator('[data-nav="clientes"]').click()
        page.get_by_role("heading", name="Clientes", exact=True).wait_for()
        page.get_by_role("button", name="+ Nuevo cliente", exact=True).click()
        page.locator("#field-nombre").fill("Ana Prueba")
        page.locator("#field-correo").fill("ana@example.com")
        page.get_by_role("button", name="Guardar", exact=True).click()
        page.get_by_text("Ana Prueba", exact=True).wait_for()
        page.locator("#q").fill("Ana")
        page.get_by_role("button", name="Aplicar filtros").click()
        page.get_by_text("Ana Prueba", exact=True).wait_for()
        assert page.locator("tbody tr").count() == 1
        page.get_by_role("button", name="Editar", exact=True).click()
        page.locator("#field-nombre").fill("Ana Editada")
        page.get_by_role("button", name="Guardar", exact=True).click()
        page.get_by_text("Ana Editada", exact=True).wait_for()
        page.on("dialog", lambda dialog: dialog.accept())
        page.get_by_text("Ana Editada", exact=True).locator("..").get_by_role(
            "button", name="Eliminar"
        ).click()
        page.get_by_text("Registro eliminado correctamente.", exact=True).wait_for()
        assert len(clients) == 1
        page.locator('[data-nav="pedidos"]').click()
        page.get_by_role("link", name="Ver detalle").click()
        page.get_by_role("heading", name="Pedido #1", exact=True).wait_for()
        page.get_by_role("button", name="+ Registrar pago").click()
        assert page.locator("#field-id_pedido").is_disabled()
        page.get_by_role("button", name="Cancelar", exact=True).click()
        page.locator('[data-nav="reportes"]').click()
        page.locator("#report-kind").select_option("ventas-periodo")
        page.locator("#desde").fill("2026-02-01")
        page.locator("#hasta").fill("2026-01-01")
        page.get_by_role("button", name="Consultar", exact=True).click()
        page.get_by_text(
            "Selecciona un intervalo de fechas válido.", exact=True
        ).wait_for()
        page.locator('[data-nav="dashboard"]').click()
        page.get_by_role("heading", name="Resumen de tu negocio").wait_for()
        page.set_viewport_size({"width": 390, "height": 844})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.screenshot(
            path=str(ROOT / "docs/evidencias/ui-mobile.png"), full_page=True
        )
        page.get_by_role("button", name="Salir", exact=True).click()
        page.wait_for_url("**/login.html")
        # Verify seller navigation hides administrator-only user management.
        user["rol"] = "VENDEDOR"
        page.locator("#correo").fill("vendedor@example.com")
        page.locator("#contrasena").fill("password-test")
        page.get_by_role("button", name="Iniciar sesión").click()
        page.get_by_role("heading", name="Resumen de tu negocio").wait_for()
        assert page.locator('[data-nav="usuarios"]').count() == 0
        page.locator('[data-nav="pagos"]').click()
        page.get_by_role("heading", name="Pagos", exact=True).wait_for()
        assert page.get_by_role("button", name="Anular", exact=True).count() == 0
        assert not errors, errors
        browser.close()
    print(
        "UI OK: login, navegación, CRUD clientes, edición productos, filtros, detalle, fechas, móvil, salida y permisos visuales. API simulada; Oracle no probado."
    )


def resources_title(module):
    return {
        "proveedores": "Proveedores",
        "productos": "Productos",
        "clientes": "Clientes",
        "pedidos": "Pedidos",
        "pagos": "Pagos",
        "reportes": "Reportes",
        "usuarios": "Usuarios",
    }[module]


if __name__ == "__main__":
    run()
