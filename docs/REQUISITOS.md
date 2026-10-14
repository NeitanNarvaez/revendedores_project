# Análisis y alcance

## Problema
Un pequeño revendedor registra proveedores, productos, clientes, pedidos y abonos en hojas separadas. Esto dificulta conocer existencias, conservar los precios de una venta y evitar pagos superiores al saldo.

## Objetivo
Centralizar esos registros en una aplicación de tres capas con una interfaz web, una API REST de FastAPI y persistencia en Oracle Database.

## Actores y permisos

| Acción | ADMINISTRADOR | VENDEDOR |
|---|---|---|
| Iniciar sesión | Sí | Sí |
| Consultar/crear/editar proveedores, productos y clientes | Sí | Sí |
| Eliminar proveedores, productos y clientes | Sí | No |
| Consultar/crear/modificar pedidos y detalles | Todos | Solo propios |
| Registrar pagos | Todos los pedidos | Solo propios |
| Editar/anular pagos | Sí | No |
| Dashboard y reportes | Todo el negocio | Solo sus pedidos |
| Listar/crear/editar usuarios y asignar roles | Sí | No |

Los catálogos son compartidos por el equipo de un mismo negocio. No se implementa una plataforma de múltiples empresas. Los roles son dos valores fijos; gestionar roles significa asignarlos a usuarios. Las cuentas se desactivan, no se borran, para conservar la relación con las ventas.

## Requisitos funcionales verificables

| ID | Requisito | Implementación |
|---|---|---|
| RF01 | Autenticar y cerrar sesión | Login JSON, JWT Bearer y salida del navegador |
| RF02 | Gestionar usuarios y roles | Crear vendedor; editar nombre, correo, rol y estado |
| RF03 | CRUD proveedores | Catálogo con búsqueda por nombre y filtro de activo |
| RF04 | CRUD productos | Costo, margen, precio calculado y existencia |
| RF05 | CRUD clientes | Datos de contacto y búsqueda por nombre |
| RF06 | CRUD pedidos | Cliente, vendedor autenticado, estado y observaciones |
| RF07 | Gestionar detalle | Agregar/editar/quitar productos y conservar precio histórico |
| RF08 | CRUD pagos | Crear, consultar, editar y anular lógicamente |
| RF09 | Filtrar información | Catálogos por nombre; pedidos por estado/cliente; pagos por estado/pedido |
| RF10 | Mostrar dashboard | Ventas del mes, pendientes y productos más vendidos |
| RF11 | Consultar reportes | Ventas por cliente, proveedor y período |
| RF12 | Validar y comunicar errores | Formularios HTML, esquemas Pydantic, reglas del servicio y restricciones Oracle |

## Reglas del proceso

1. Un pedido nuevo comienza en PENDIENTE. Se agregan sus productos después de crearlo.
2. Agregar una línea reserva existencias: resta la cantidad disponible. No se permite vender por encima del stock.
3. Cambiar cantidades ajusta la reserva; quitar líneas, eliminar pedidos sin pagos o cancelar pedidos devuelve la existencia.
4. CANCELADO y ENTREGADO son estados finales. No se reabren ni se cambian sus productos. Un pedido cancelado no devuelve stock dos veces.
5. Un pedido con pagos REGISTRADOS no admite cambios de productos ni cancelación hasta que un administrador anule esos pagos.
6. Los pagos registrados no superan el total. Editar un pago aplica la misma regla. No se puede mover un pago o una línea a otro pedido.
7. El precio histórico se mantiene al editar solamente la cantidad del mismo producto. Solo el administrador puede aplicar un precio diferente.
8. Un pedido con historial de pagos, incluso anulados, se conserva y se cancela en lugar de eliminarse.
9. El costo y el margen se calculan con Decimal. Los montos se guardan como NUMBER(12,2).
10. La existencia del formulario de productos es la cantidad **disponible**. Su edición manual representa un ajuste físico del inventario; no hay módulo adicional de compras o movimientos.
11. El dashboard mide valor de pedidos no cancelados, no recaudo efectivo. Los reportes mantienen esa misma definición.

## Alcance técnico y límites
HTML, CSS, Bootstrap local y JavaScript con fetch; FastAPI; python-oracledb; Oracle; Swagger; pytest; Git/GitHub. No se requieren microservicios, ORM, Docker, pasarela de pago, facturación electrónica ni notificaciones. Los bloqueos de fila de Oracle mantienen juntas las operaciones de stock y pagos del mismo pedido; todavía no existe una auditoría completa ni un historial de movimientos de inventario.

## Criterios de aceptación
Repetir el flujo de `PRUEBAS.md` con Oracle y adjuntar evidencias propias. La existencia de código o una prueba con conexiones simuladas no demuestra la integración real. El grupo debe registrar sus nombres, contribuciones y resultados de la sustentación.
