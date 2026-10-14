"""Crear primer administrador interactivamente. Ejecutar: python -m backend.create_admin"""

import getpass
from backend.database.connection import get_connection
from backend.security import hash_password
from backend.schemas.common import RegisterIn
from pydantic import ValidationError


def main():
    nombre = input("Nombre del administrador: ").strip()
    correo = input("Correo: ").strip().lower()
    password = getpass.getpass("Contrasena (minimo 8 caracteres): ")
    try:
        data = RegisterIn(nombre=nombre, correo=correo, contrasena=password)
    except ValidationError:
        raise SystemExit(
            "Revisa nombre, correo y contraseña (8 caracteres mínimo, 72 bytes máximo)"
        )
    nombre, correo, password = data.nombre, str(data.correo), data.contrasena
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id_rol FROM roles WHERE nombre='ADMINISTRADOR'")
        role = cur.fetchone()
        if not role:
            raise SystemExit(
                "No existe el rol ADMINISTRADOR. Ejecute primero database/03_data.sql"
            )
        cur.execute(
            "INSERT INTO usuarios(id_rol,nombre,correo,hash_contrasena,activo) VALUES(:rol,:nombre,:correo,:hash,1)",
            {
                "rol": role[0],
                "nombre": nombre,
                "correo": correo,
                "hash": hash_password(password),
            },
        )
        conn.commit()
        print("Administrador creado correctamente. No comparta sus credenciales.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
