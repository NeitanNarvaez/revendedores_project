from backend.services.rules import calcular_precio_venta
from fastapi import HTTPException
from pydantic import BaseModel
import oracledb
from backend.database.connection import get_connection

CONFIG = {
    "proveedores": {
        "table": "proveedores",
        "pk": "id_proveedor",
        "cols": ["nombre", "contacto", "telefono", "correo", "direccion", "activo"],
    },
    "productos": {
        "table": "productos",
        "pk": "id_producto",
        "cols": [
            "id_proveedor",
            "nombre",
            "descripcion",
            "precio_compra",
            "margen_porcentaje",
            "existencia",
            "activo",
        ],
    },
    "clientes": {
        "table": "clientes",
        "pk": "id_cliente",
        "cols": ["nombre", "telefono", "correo", "direccion"],
    },
}


def _create(resource: str, data: BaseModel):
    cfg = CONFIG[resource]
    values = data.model_dump()
    if resource == "productos":
        values["precio_venta"] = calcular_precio_venta(
            values["precio_compra"], values["margen_porcentaje"]
        )
        cfg_cols = cfg["cols"] + ["precio_venta"]
    else:
        cfg_cols = cfg["cols"]
    binds = {col: values.get(col) for col in cfg_cols}
    names = ", ".join(cfg_cols)
    placeholders = ", ".join((":" + c for c in cfg_cols))
    conn = get_connection()
    try:
        cur = conn.cursor()
        out = cur.var(oracledb.NUMBER)
        cur.execute(
            f"INSERT INTO {cfg['table']} ({names}) VALUES ({placeholders}) RETURNING {cfg['pk']} INTO :out_id",
            {**binds, "out_id": out},
        )
        new_id = int(out.getvalue()[0])
        conn.commit()
        return _get(resource, new_id)
    except oracledb.IntegrityError as exc:
        conn.rollback()
        msg = str(exc)
        if "ORA-02291" in msg:
            raise HTTPException(400, "La referencia indicada no existe")
        raise HTTPException(
            409, "No se pudo crear el registro por una restriccion de integridad"
        )
    except HTTPException:
        conn.rollback()
        raise
    except Exception:
        conn.rollback()
        raise HTTPException(500, "No fue posible crear el registro")
    finally:
        conn.close()


def _get(resource: str, item_id: int):
    cfg = CONFIG[resource]
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            f"SELECT * FROM {cfg['table']} WHERE {cfg['pk']}=:id", {"id": item_id}
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Registro no encontrado")
        return {d[0].lower(): v for d, v in zip(cur.description, row)}
    finally:
        conn.close()


def _list(resource: str, q: str | None = None, activo: int | None = None):
    cfg = CONFIG[resource]
    conn = get_connection()
    try:
        cur = conn.cursor()
        sql = f"SELECT * FROM {cfg['table']} WHERE 1=1"
        binds = {}
        if q and resource in ("proveedores", "productos", "clientes"):
            column = "nombre"
            sql += f" AND LOWER({column}) LIKE LOWER(:q)"
            binds["q"] = "%" + q.strip() + "%"
        if activo is not None and "activo" in cfg["cols"]:
            sql += " AND activo=:activo"
            binds["activo"] = activo
        sql += f" ORDER BY {cfg['pk']} DESC"
        cur.execute(sql, binds)
        names = [d[0].lower() for d in cur.description]
        return [dict(zip(names, row)) for row in cur.fetchall()]
    finally:
        conn.close()


def _update(resource: str, item_id: int, data: BaseModel):
    cfg = CONFIG[resource]
    values = data.model_dump()
    if resource == "productos":
        values["precio_venta"] = calcular_precio_venta(
            values["precio_compra"], values["margen_porcentaje"]
        )
        cols = cfg["cols"] + ["precio_venta"]
    else:
        cols = cfg["cols"]
    binds = {col: values.get(col) for col in cols}
    binds["id"] = item_id
    assignments = ", ".join((f"{col}=:{col}" for col in cols))
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            f"UPDATE {cfg['table']} SET {assignments} WHERE {cfg['pk']}=:id", binds
        )
        if cur.rowcount == 0:
            raise HTTPException(404, "Registro no encontrado")
        conn.commit()
        return _get(resource, item_id)
    except HTTPException:
        conn.rollback()
        raise
    except oracledb.IntegrityError:
        conn.rollback()
        raise HTTPException(400, "No se puede actualizar: hay referencias invalidas")
    except Exception:
        conn.rollback()
        raise HTTPException(500, "No fue posible actualizar el registro")
    finally:
        conn.close()


def _delete(resource: str, item_id: int):
    cfg = CONFIG[resource]
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            f"DELETE FROM {cfg['table']} WHERE {cfg['pk']}=:id", {"id": item_id}
        )
        if cur.rowcount == 0:
            raise HTTPException(404, "Registro no encontrado")
        conn.commit()
        return {"mensaje": "Registro eliminado"}
    except HTTPException:
        conn.rollback()
        raise
    except oracledb.IntegrityError:
        conn.rollback()
        raise HTTPException(
            409, "No se puede eliminar: el registro esta relacionado con otros datos"
        )
    except Exception:
        conn.rollback()
        raise HTTPException(500, "No fue posible eliminar el registro")
    finally:
        conn.close()
