# Reventa — Sistema de gestión para revendedores

Proyecto académico Full Stack: **HTML + CSS + Bootstrap + JavaScript → API REST FastAPI → Oracle Database**. Permite gestionar proveedores, productos, clientes, pedidos y pagos, con usuarios, dos roles, dashboard y reportes.

## Inicio rápido

Requisitos: Python 3.11 o 3.12, acceso a un esquema de Oracle Database 12c o superior y Git. Bootstrap está incluido en el repositorio; el frontend no requiere npm.

### 1. Base de datos

En Oracle APEX, abrir **SQL Workshop → SQL Scripts**, o utilizar SQL Developer:

1. Ejecutar `database/01_tables.sql` una sola vez en un esquema vacío.
2. Ejecutar `database/03_data.sql` una sola vez para roles y catálogos demo.
3. `02_constraints.sql` explica las reglas adicionales; las restricciones DDL ya están en `01_tables.sql`.
4. `04_queries.sql` contiene consultas de reportes.

Si ya ejecutaste la versión inicial del proyecto, **no vuelvas a crear las tablas ni a insertar los roles**. Esta actualización conserva las ocho tablas y no necesita migración. Puedes crear productos de prueba desde la interfaz. Antes de activar las nuevas reservas de stock con pedidos anteriores, revisa manualmente la existencia disponible: los detalles antiguos no reservaron stock. Para la primera demostración se recomienda un esquema de pruebas nuevo.

APEX administra la base, pero su URL no es el DSN de conexión. Solicita/revisa el usuario de base de datos, host, puerto y servicio reales. En Autonomous Database utiliza la configuración de conexión de tu instancia; si requiere wallet, establece TNS_ADMIN y WALLET_PASSWORD de forma privada.

### 2. Instalar Python

Desde la carpeta `revendedores_project/`:

**Windows PowerShell**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
Copy-Item backend/.env.example backend/.env
```

**Linux/macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
```

Editar `backend/.env` localmente:

```dotenv
ORACLE_USER=TU_USUARIO
ORACLE_PASSWORD=TU_CLAVE
ORACLE_DSN=host:1521/servicio
TNS_ADMIN=
WALLET_PASSWORD=
JWT_SECRET=REEMPLAZAR_CON_UN_SECRETO_LARGO_ALEATORIO
```

Generar una clave con `python -c "import secrets; print(secrets.token_urlsafe(48))"` y guardarla como JWT_SECRET. No subir `.env`, tokens, contraseñas ni wallet al repositorio. bcrypt se mantiene en la versión 4.0.x compatible con Passlib; las contraseñas tienen al menos 8 caracteres y máximo 72 bytes UTF-8.

### 3. Crear el administrador

```bash
python -m backend.create_admin
```

Escribir nombre, correo y contraseña cuando se soliciten. La contraseña se guarda como hash. No hay credenciales predeterminadas. El administrador puede crear vendedores desde Usuarios y luego editar sus roles.

### 4. Ejecutar todo el proyecto

```bash
uvicorn backend.main:app --reload
```

- **Aplicación:** <http://127.0.0.1:8000/app/login.html>
- **Swagger:** <http://127.0.0.1:8000/docs>
- **Estado del proceso:** <http://127.0.0.1:8000/health>

FastAPI sirve también el frontend. No abrir los HTML haciendo doble clic: deben cargarse desde `/app/`. `/health` no comprueba Oracle; el login y las consultas de módulos sí necesitan conexión real.

## Uso básico

1. Iniciar sesión con el administrador creado.
2. Crear proveedor, producto y cliente, o utilizar los catálogos demo de un esquema nuevo.
3. Crear un pedido PENDIENTE y abrir **Ver detalle**.
4. Agregar productos: su existencia disponible disminuye.
5. Registrar un abono menor o igual al saldo.
6. Consultar dashboard y reportes.
7. Crear una cuenta VENDEDOR en Usuarios y comprobar sus permisos en otra sesión del navegador.

Los cinco módulos principales ofrecen CRUD. Los pagos se eliminan mediante anulación lógica para conservar el historial. Los pedidos con historial de pagos se cancelan, en lugar de borrarse. Los catálogos son compartidos; los pedidos, pagos y reportes se limitan al vendedor autenticado salvo que sea administrador.

## Swagger

1. Ejecutar `POST /api/auth/login` con JSON de correo y contraseña.
2. Copiar `access_token`.
3. Pulsar **Authorize** y pegar **solo el token**, sin escribir `Bearer`.
4. Probar los endpoints. Swagger agrega el encabezado `Authorization: Bearer ...`.

Los contratos completos aparecen en `/docs`. El resumen está en [docs/ENDPOINTS.md](docs/ENDPOINTS.md).

## Pruebas

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

La suite habitual no requiere Oracle: comprueba la API con dependencias simuladas, validaciones, permisos y reglas transaccionales. La prueba real de integración Oracle se omite hasta habilitarla expresamente en un esquema de pruebas. Los comandos y pasos manuales están en [docs/PRUEBAS.md](docs/PRUEBAS.md).

## Estructura

```text
revendedores_project/
├── frontend/          # Login, interfaz, CSS/Bootstrap y fetch
├── backend/
│   ├── routers/       # Endpoints y permisos
│   ├── services/      # SQL y reglas del negocio
│   ├── schemas/       # Contratos y validación
│   ├── database/      # Conexiones y transacciones
│   └── main.py        # API, Swagger y frontend estático
├── database/          # Tablas, restricciones, datos y consultas
├── docs/              # Análisis, modelos, pruebas y sustentación
└── tests/             # Pruebas automáticas y comprobación UI opcional
```

No se requiere ORM ni modelos Python duplicados: el modelo físico está definido en SQL. Las páginas de módulos se muestran dentro de `index.html`.

## Documentación para entregar

- [Análisis y requisitos](docs/REQUISITOS.md)
- [Arquitectura](docs/ARQUITECTURA.md)
- [Diagrama entidad-relación](docs/MODELO_ER.md)
- [Modelo lógico y diccionario](docs/MODELO_LOGICO.md)
- [Modelo físico](docs/MODELO_FISICO.md)
- [Relaciones y reglas](docs/MODELO_RELACIONAL.md)
- [Pruebas y evidencias](docs/PRUEBAS.md)
- [Despliegue](docs/DESPLIEGUE.md)
- [Guion de sustentación](docs/SUSTENTACION.md)
- [Integrantes y contribuciones: completar con datos reales](docs/INTEGRANTES.md)

## Estado y tareas del equipo

El repositorio incluye la implementación y las comprobaciones reproducibles. El equipo debe configurar su Oracle, ejecutar el flujo real, guardar sus evidencias, completar integrantes y contribuciones y preparar la explicación de su código. No se incluye una instancia Oracle, credenciales ni un despliegue público. Esto es una base académica; no tiene pagos bancarios reales, facturación, recuperación de contraseña ni auditoría completa.
