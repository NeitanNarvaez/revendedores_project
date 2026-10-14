from backend.services.rules import validate_period

from backend.database.connection import get_connection
from backend.security import get_current_user


def dashboard(user=None):
    conn = get_connection()
    try:
        cur = conn.cursor()
        filter_sql = (
            " AND p.id_usuario=:usuario" if user["rol"] != "ADMINISTRADOR" else ""
        )
        binds = (
            {"usuario": user["id_usuario"]} if user["rol"] != "ADMINISTRADOR" else {}
        )
        cur.execute(
            "SELECT COUNT(*) FROM pedidos p WHERE p.estado='PENDIENTE'" + filter_sql,
            binds,
        )
        pendientes = cur.fetchone()[0]
        cur.execute(
            "SELECT NVL(SUM(d.cantidad*d.precio_unitario),0) FROM detalle_pedido d JOIN pedidos p ON p.id_pedido=d.id_pedido\n          WHERE p.estado<>'CANCELADO' AND p.fecha_pedido>=TRUNC(SYSDATE,'MM')"
            + filter_sql,
            binds,
        )
        ventas_mes = float(cur.fetchone()[0])
        cur.execute(
            "SELECT pr.nombre,SUM(d.cantidad) unidades FROM detalle_pedido d JOIN productos pr ON pr.id_producto=d.id_producto\n          JOIN pedidos p ON p.id_pedido=d.id_pedido WHERE p.estado<>'CANCELADO'"
            + filter_sql
            + " GROUP BY pr.nombre ORDER BY unidades DESC FETCH FIRST 5 ROWS ONLY",
            binds,
        )
        top = [{"producto": r[0], "unidades": r[1]} for r in cur.fetchall()]
        return {
            "ventas_mes": ventas_mes,
            "pedidos_pendientes": pendientes,
            "productos_mas_vendidos": top,
        }
    finally:
        conn.close()


def ventas_cliente(user=None):
    conn = get_connection()
    try:
        cur = conn.cursor()
        sql = "SELECT c.id_cliente,c.nombre,COUNT(DISTINCT p.id_pedido) pedidos,\n          NVL(SUM(d.cantidad*d.precio_unitario),0) ventas FROM clientes c JOIN pedidos p ON p.id_cliente=c.id_cliente\n          LEFT JOIN detalle_pedido d ON d.id_pedido=p.id_pedido WHERE p.estado<>'CANCELADO'"
        binds = {}
        if user["rol"] != "ADMINISTRADOR":
            sql += " AND p.id_usuario=:usuario"
            binds["usuario"] = user["id_usuario"]
        sql += " GROUP BY c.id_cliente,c.nombre ORDER BY ventas DESC"
        cur.execute(sql, binds)
        names = [d[0].lower() for d in cur.description]
        return [dict(zip(names, r)) for r in cur.fetchall()]
    finally:
        conn.close()


def ventas_proveedor(user=None):
    conn = get_connection()
    try:
        cur = conn.cursor()
        sql = "SELECT pv.id_proveedor,pv.nombre proveedor,NVL(SUM(d.cantidad*d.precio_unitario),0) ventas\n          FROM proveedores pv JOIN productos pr ON pr.id_proveedor=pv.id_proveedor JOIN detalle_pedido d ON d.id_producto=pr.id_producto\n          JOIN pedidos p ON p.id_pedido=d.id_pedido WHERE p.estado<>'CANCELADO'"
        binds = {}
        if user["rol"] != "ADMINISTRADOR":
            sql += " AND p.id_usuario=:usuario"
            binds["usuario"] = user["id_usuario"]
        sql += " GROUP BY pv.id_proveedor,pv.nombre ORDER BY ventas DESC"
        cur.execute(sql, binds)
        names = [d[0].lower() for d in cur.description]
        return [dict(zip(names, r)) for r in cur.fetchall()]
    finally:
        conn.close()


def ventas_periodo(desde=None, hasta=None, user=None):
    validate_period(desde, hasta)
    conn = get_connection()
    try:
        cur = conn.cursor()
        sql = "SELECT TO_CHAR(TRUNC(p.fecha_pedido,'MM'),'YYYY-MM') periodo,\n          SUM(d.cantidad*d.precio_unitario) ventas,COUNT(DISTINCT p.id_pedido) pedidos\n          FROM pedidos p JOIN detalle_pedido d ON d.id_pedido=p.id_pedido WHERE p.estado<>'CANCELADO'\n          AND p.fecha_pedido>=:desde AND p.fecha_pedido<:hasta+1"
        binds = {"desde": desde, "hasta": hasta}
        if user["rol"] != "ADMINISTRADOR":
            sql += " AND p.id_usuario=:usuario"
            binds["usuario"] = user["id_usuario"]
        sql += (
            " GROUP BY TRUNC(p.fecha_pedido,'MM') ORDER BY TRUNC(p.fecha_pedido,'MM')"
        )
        cur.execute(sql, binds)
        names = [d[0].lower() for d in cur.description]
        return [dict(zip(names, r)) for r in cur.fetchall()]
    finally:
        conn.close()
