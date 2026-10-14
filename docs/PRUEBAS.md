# Plan de pruebas y evidencias

## 1. Suite automática sin Oracle

Desde `revendedores_project/`:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

- `test_calculos.py`: usa funciones reales de los servicios para precio, fechas, pagos, estados y precio histórico.
- `test_api.py`: peticiones HTTP mediante TestClient, contratos, validación, login JSON, esquema Bearer, CRUD de catálogo con servicios simulados, permisos y mensajes de error.
- `test_seguridad.py`: hash real de contraseñas, emisión de JWT, rechazo de clave incorrecta y cuentas desactivadas.
- `test_transacciones.py`: conexiones simuladas para comprobar reserva condicionada de stock, rollback, bloqueo del pedido y actualización de detalles.
- `test_oracle.py`: integración real, **omitida por defecto**.

Estas pruebas no sustituyen la ejecución de los scripts ni la demostración contra Oracle.

## 2. Prueba automática optativa con Oracle real

**Usar un esquema de pruebas dedicado**, con `01_tables.sql`, `03_data.sql` y un administrador creado. La prueba crea datos con un identificador aleatorio y elimina solamente los registros que ella creó, incluyendo sus pagos de prueba. No habilitarla en un esquema de producción.

Configurar `backend/.env` con el acceso de ese esquema. En PowerShell:

```powershell
$env:RUN_ORACLE_TESTS="1"
$env:TEST_ADMIN_EMAIL=Read-Host "Correo del administrador de pruebas"
$credential=Get-Credential -UserName $env:TEST_ADMIN_EMAIL -Message "Administrador del esquema de pruebas"
$env:TEST_ADMIN_PASSWORD=$credential.GetNetworkCredential().Password
python -m pytest -q -m oracle
Remove-Item Env:TEST_ADMIN_PASSWORD
Remove-Item Env:TEST_ADMIN_EMAIL
Remove-Item Env:RUN_ORACLE_TESTS
```

En bash:

```bash
export RUN_ORACLE_TESTS=1
read -r -p "Correo del administrador de pruebas: " TEST_ADMIN_EMAIL
export TEST_ADMIN_EMAIL
read -r -s -p "Contraseña: " TEST_ADMIN_PASSWORD
export TEST_ADMIN_PASSWORD
python -m pytest -q -m oracle
unset TEST_ADMIN_PASSWORD TEST_ADMIN_EMAIL RUN_ORACLE_TESTS
```

Comprueba login real, CRUD de producto, búsqueda, reserva/stock insuficiente, pago excesivo, bloqueo de detalles pagados, anulación, cancelación y persistencia desde otra conexión Oracle. Guardar la salida sin variables secretas en una evidencia propia.

## 3. Prueba de interfaz opcional

En otra terminal mantener la API ejecutándose en `127.0.0.1:8000`:

```bash
python -m pip install -r requirements-ui.txt
python -m playwright install chromium --only-shell
python tests/ui_smoke.py
```

Esta prueba abre Chromium e intercepta `/api/` con respuestas simuladas. Comprueba navegación, login, CRUD de clientes, edición de productos, filtros, vista de pedido, intervalo inválido, tamaño móvil, salida y permisos visuales. Genera `ui-desktop.png` y `ui-mobile.png`. **Es evidencia de interfaz, no de persistencia ni integración real**. El servidor de producción no tiene un modo demo ni devuelve estos datos: solo el script de prueba los simula en el navegador.

## 4. Casos manuales con Swagger y navegador + Oracle

Completar la columna Resultado al ejecutar cada caso; no dejar valores supuestos.

| Caso | Acción | Resultado esperado | Resultado real / evidencia |
|---|---|---|---|
| M01 | Login correcto desde navegador | Acceso al dashboard y consultas Oracle | Pendiente |
| M02 | Login con contraseña incorrecta | 401 y mensaje claro | Pendiente |
| M03 | Endpoint protegido sin token | 401 | Pendiente |
| M04 | Crear proveedor, producto y cliente | 201 y filas presentes en Oracle | Pendiente |
| M05 | Consultar/editar/eliminar un cliente sin pedidos | 200 y luego 404 | Pendiente |
| M06 | Buscar nombre en productos y clientes | Solo coincidencias | Pendiente |
| M07 | Crear pedido y agregar 2 unidades de producto | Total correcto; existencia baja en 2 | Pendiente |
| M08 | Agregar cantidad mayor al stock | 400; no se inserta detalle ni se descuenta stock | Pendiente |
| M09 | Cambiar precio del catálogo y luego cantidad del detalle | Conserva precio histórico de la línea | Pendiente |
| M10 | Registrar abono permitido | 201 y saldo actualizado | Pendiente |
| M11 | Registrar abono superior al saldo | 400; no aparece en Oracle | Pendiente |
| M12 | Cambiar/eliminar detalle con pagos registrados | 400 sin alterar el total | Pendiente |
| M13 | Administrador anula pago | Estado ANULADO; historial conservado | Pendiente |
| M14 | Cancelar pedido sin pagos registrados | Devuelve stock; no permite reabrir | Pendiente |
| M15 | Vendedor solicita DELETE /api/productos/ID | 403; producto permanece | Pendiente |
| M16 | Vendedor intenta consultar pedido de otro vendedor | 403; no expone sus datos | Pendiente |
| M17 | Enviar precio negativo, correo inválido o cantidad cero | 422 sin cambios en Oracle | Pendiente |
| M18 | Fechas inválidas o intervalo invertido | 422 o 400, sin error técnico expuesto | Pendiente |
| M19 | Dashboard y reportes | Totales coherentes con pedidos no cancelados y rol | Pendiente |
| M20 | Desactivar vendedor y usar su token anterior | 401 | Pendiente |
| M21 | Vista de 390px y teclado | Sin desborde de página; tablas desplazables y campos accesibles | Pendiente |

Para M09 hacerlo antes de M10 o después de anular pagos. Para probar eliminación física, usar registros nuevos sin referencias; los conflictos de FK devuelven 409. Para M16 crear al menos dos vendedores reales.

## 5. Evidencias de persistencia

Después de crear un cliente desde la interfaz, ejecutar en el esquema Oracle:

```sql
SELECT id_cliente,nombre,correo FROM clientes ORDER BY id_cliente DESC;
SELECT id_pedido,id_cliente,id_usuario,estado FROM pedidos ORDER BY id_pedido DESC;
SELECT id_detalle,id_pedido,id_producto,cantidad,precio_unitario FROM detalle_pedido;
SELECT id_producto,nombre,existencia FROM productos;
SELECT id_pago,id_pedido,monto,estado FROM pagos;
```

Tomar una captura del formulario/tabla web, una de la petición en Swagger o Network y otra de la fila en Oracle. Guardarlas en `docs/evidencias/` y anotar fecha, caso y resultado. No incluir claves, tokens, wallet ni información personal real.
