# Instalación y despliegue para la demostración

## Demostración local

Con Oracle configurado y los scripts ejecutados, desde `revendedores_project/`:

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Abrir `http://127.0.0.1:8000/app/login.html`. La misma API entrega el frontend, sin servidor Node ni compilación. La documentación está en `/docs`. `/health` comprueba que el proceso responde, no que Oracle esté disponible. El login y la consulta de productos comprueban la conexión real.

## Demostración en una red local

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

El resto del grupo abre `http://IP_DEL_EQUIPO:8000/app/login.html`. El equipo servidor debe poder acceder a Oracle y permitir el puerto de demostración. No abrir un router a Internet para esta prueba.

## Si el profesor pide una URL pública

Usar un servidor Python con Python 3.11/3.12, instalar `backend/requirements.txt`, configurar las variables del ejemplo de entorno y ejecutar `uvicorn backend.main:app --host 0.0.0.0 --port PUERTO_DEL_PROVEEDOR`. Mantener frontend y API en el mismo dominio y habilitar HTTPS desde el proveedor/proxy. La base Oracle debe permitir la conexión de ese servidor. Si usa wallet, cargarlo como secreto/archivo privado y definir TNS_ADMIN.

GitHub Pages solo sirve archivos estáticos; no ejecuta FastAPI ni Oracle. Este repositorio no crea un despliegue público automáticamente ni incluye una URL pública verificada.

## Lista previa

- Crear tablas y roles en el esquema correcto.
- Configurar `.env` o secretos del servidor, sin subirlos a GitHub.
- Crear el primer administrador mediante el comando interactivo.
- Iniciar sesión y probar crear/consultar un cliente desde el navegador.
- Comprobar que las peticiones HTTP llegan a FastAPI y que el dato está en Oracle.
- Registrar en `docs/evidencias/` capturas y resultados reales sin contraseñas ni tokens.
