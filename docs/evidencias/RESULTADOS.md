# Verificación realizada — 14 de octubre de 2026

| Comprobación | Resultado | Alcance |
|---|---|---|
| `python -m pytest -q` | 42 aprobadas, 1 omitida | HTTP con TestClient, reglas reales y conexiones Oracle simuladas |
| Prueba real Oracle | No ejecutada | Requiere esquema y credenciales del equipo; `tests/test_oracle.py` queda omitida por defecto |
| `node --check` de api.js, app.js y login.js | Aprobado | Sintaxis de JavaScript |
| `tests/ui_smoke.py` con Chromium | Aprobado | Login, módulos, CRUD clientes, edición de productos, filtros, detalle, fechas, salida y permisos visuales; API simulada |
| Vista escritorio 1440×1000 | Revisada | Captura interna con datos simulados |
| Vista móvil 390×844 | Revisada | Sin desborde de página; captura interna con datos simulados |
| `git diff --check` | Aprobado | Espacios y formato del parche |

Las capturas se inspeccionaron visualmente y no se incluyen como evidencia de Oracle. El script de UI permite regenerarlas. Las tablas permiten desplazamiento horizontal cuando es necesario. La comprobación de interfaz no es prueba de que Oracle esté conectado.

Entorno de comprobación: Python 3.12, FastAPI 0.143.1, Pydantic 2.14.1, python-oracledb 3.4.2, pytest 8.4.2 y Playwright 1.51.0. La ejecución de pytest emite advertencias de deprecación de dependencias (TestClient/httpx y crypt/Passlib), sin fallos.

Pendiente del equipo: conexión Oracle real, casos manuales M01–M21, datos de integrantes, contribuciones identificables y entorno final de presentación/despliegue.
