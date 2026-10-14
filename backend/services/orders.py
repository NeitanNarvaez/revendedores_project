from fastapi import HTTPException
from backend.database.helpers import database, rows, new_id
from backend.services.rules import editable_order, applied_price


def order_for_user(cur, order_id, user, lock=False):
    cur.execute(
        "SELECT id_usuario,estado FROM pedidos WHERE id_pedido=:id"
        + (" FOR UPDATE" if lock else ""),
        {"id": order_id},
    )
    order = cur.fetchone()
    if not order:
        raise HTTPException(404, "Pedido no encontrado")
    if user["rol"] != "ADMINISTRADOR" and order[0] != user["id_usuario"]:
        raise HTTPException(403, "No tienes permiso para acceder a este pedido")
    return order


def paid_total(cur, order_id):
    cur.execute(
        "SELECT NVL(SUM(monto),0) FROM pagos WHERE id_pedido=:id AND estado='REGISTRADO'",
        {"id": order_id},
    )
    return cur.fetchone()[0]


def order_total(cur, order_id):
    cur.execute(
        "SELECT NVL(SUM(cantidad*precio_unitario),0) FROM detalle_pedido WHERE id_pedido=:id",
        {"id": order_id},
    )
    return cur.fetchone()[0]


def list_orders(user, estado=None, id_cliente=None):
    with database() as cur:
        sql = """SELECT p.*,c.nombre cliente,u.nombre vendedor,
          NVL((SELECT SUM(cantidad*precio_unitario) FROM detalle_pedido d WHERE d.id_pedido=p.id_pedido),0) total
          FROM pedidos p JOIN clientes c ON c.id_cliente=p.id_cliente JOIN usuarios u ON u.id_usuario=p.id_usuario WHERE 1=1"""
        params = {}
        if estado:
            sql += " AND p.estado=:estado"
            params["estado"] = estado
        if id_cliente:
            sql += " AND p.id_cliente=:cliente"
            params["cliente"] = id_cliente
        if user["rol"] != "ADMINISTRADOR":
            sql += " AND p.id_usuario=:usuario"
            params["usuario"] = user["id_usuario"]
        cur.execute(sql + " ORDER BY p.id_pedido DESC", params)
        return rows(cur)


def get_order(order_id, user):
    with database() as cur:
        order_for_user(cur, order_id, user)
        cur.execute(
            "SELECT p.*,c.nombre cliente FROM pedidos p JOIN clientes c ON c.id_cliente=p.id_cliente WHERE p.id_pedido=:id",
            {"id": order_id},
        )
        result = rows(cur)[0]
        cur.execute(
            """SELECT d.*,pr.nombre producto,d.cantidad*d.precio_unitario subtotal FROM detalle_pedido d
          JOIN productos pr ON pr.id_producto=d.id_producto WHERE d.id_pedido=:id ORDER BY d.id_detalle""",
            {"id": order_id},
        )
        result["detalles"] = rows(cur)
        cur.execute(
            "SELECT * FROM pagos WHERE id_pedido=:id ORDER BY id_pago", {"id": order_id}
        )
        result["pagos"] = rows(cur)
        result["total"] = order_total(cur, order_id)
        result["pagado"] = paid_total(cur, order_id)
        result["saldo"] = result["total"] - result["pagado"]
        return result


def create_order(data, user):
    if data.estado != "PENDIENTE":
        raise HTTPException(400, "Los pedidos nuevos deben comenzar en PENDIENTE")
    with database(write=True) as cur:
        order_id = new_id(
            cur,
            "INSERT INTO pedidos(id_cliente,id_usuario,estado,observaciones) VALUES(:cliente,:usuario,:estado,:obs)",
            {
                "cliente": data.id_cliente,
                "usuario": user["id_usuario"],
                "estado": data.estado,
                "obs": data.observaciones,
                "_pk": "id_pedido",
            },
        )
    return get_order(order_id, user)


def restore_stock(cur, order_id):
    cur.execute(
        "SELECT id_producto,cantidad FROM detalle_pedido WHERE id_pedido=:id ORDER BY id_producto",
        {"id": order_id},
    )
    for product_id, quantity in cur.fetchall():
        cur.execute(
            "UPDATE productos SET existencia=existencia+:cantidad WHERE id_producto=:id",
            {"cantidad": quantity, "id": product_id},
        )


def update_order(order_id, data, user):
    with database(write=True) as cur:
        old = order_for_user(cur, order_id, user, lock=True)
        if old[1] in ("CANCELADO", "ENTREGADO"):
            raise HTTPException(
                400, "Un pedido cancelado o entregado no se puede modificar"
            )
        if data.estado == "CANCELADO":
            if paid_total(cur, order_id) > 0:
                raise HTTPException(400, "Anula los pagos antes de cancelar el pedido")
            restore_stock(cur, order_id)
        elif data.estado != "PENDIENTE" and order_total(cur, order_id) <= 0:
            raise HTTPException(
                400, "Agrega productos antes de avanzar el estado del pedido"
            )
        cur.execute(
            "UPDATE pedidos SET id_cliente=:cliente,estado=:estado,observaciones=:obs WHERE id_pedido=:id",
            {
                "cliente": data.id_cliente,
                "estado": data.estado,
                "obs": data.observaciones,
                "id": order_id,
            },
        )
    return get_order(order_id, user)


def delete_order(order_id, user):
    with database(write=True) as cur:
        order = order_for_user(cur, order_id, user, lock=True)
        if order[1] == "ENTREGADO":
            raise HTTPException(400, "No se puede eliminar un pedido entregado")
        cur.execute("SELECT COUNT(*) FROM pagos WHERE id_pedido=:id", {"id": order_id})
        if cur.fetchone()[0]:
            raise HTTPException(
                409,
                "El pedido tiene historial de pagos; consérvalo y usa la cancelación",
            )
        if order[1] != "CANCELADO":
            restore_stock(cur, order_id)
        cur.execute("DELETE FROM pedidos WHERE id_pedido=:id", {"id": order_id})
    return {"mensaje": "Pedido eliminado"}


def list_details(user, id_pedido=None):
    with database() as cur:
        sql = """SELECT d.*,pr.nombre producto,d.cantidad*d.precio_unitario subtotal FROM detalle_pedido d
          JOIN pedidos p ON p.id_pedido=d.id_pedido JOIN productos pr ON pr.id_producto=d.id_producto WHERE 1=1"""
        params = {}
        if id_pedido:
            order_for_user(cur, id_pedido, user)
            sql += " AND d.id_pedido=:pedido"
            params["pedido"] = id_pedido
        if user["rol"] != "ADMINISTRADOR":
            sql += " AND p.id_usuario=:usuario"
            params["usuario"] = user["id_usuario"]
        cur.execute(sql + " ORDER BY d.id_detalle DESC", params)
        return rows(cur)


def get_detail(detail_id, user):
    with database() as cur:
        cur.execute(
            "SELECT * FROM detalle_pedido WHERE id_detalle=:id", {"id": detail_id}
        )
        result = rows(cur)
        if not result:
            raise HTTPException(404, "Detalle no encontrado")
        order_for_user(cur, result[0]["id_pedido"], user)
        return result[0]


def reserve_stock(cur, product_id, quantity):
    cur.execute(
        "UPDATE productos SET existencia=existencia-:cantidad WHERE id_producto=:id AND existencia>=:cantidad AND activo=1",
        {"cantidad": quantity, "id": product_id},
    )
    if cur.rowcount == 0:
        raise HTTPException(400, "Producto inactivo o existencia insuficiente")


def save_detail(data, user, detail_id=None):
    with database(write=True) as cur:
        order = order_for_user(cur, data.id_pedido, user, lock=True)
        editable_order(order[1], paid_total(cur, data.id_pedido))
        old = None
        if detail_id is not None:
            cur.execute(
                "SELECT id_pedido,id_producto,cantidad,precio_unitario FROM detalle_pedido WHERE id_detalle=:id FOR UPDATE",
                {"id": detail_id},
            )
            old = cur.fetchone()
            if not old:
                raise HTTPException(404, "Detalle no encontrado")
            if old[0] != data.id_pedido:
                raise HTTPException(400, "No se puede mover un detalle a otro pedido")
        # Lock products in a stable order when a detail changes product.
        product_ids = sorted({data.id_producto} | ({old[1]} if old else set()))
        products = {}
        for product_id in product_ids:
            cur.execute(
                "SELECT precio_venta,activo FROM productos WHERE id_producto=:id FOR UPDATE",
                {"id": product_id},
            )
            products[product_id] = cur.fetchone()
        product = products[data.id_producto]
        if not product or product[1] != 1:
            raise HTTPException(404, "Producto no encontrado o inactivo")
        same = old is not None and old[1] == data.id_producto
        price = applied_price(
            product[0],
            old[3] if old else product[0],
            data.precio_unitario,
            same,
            user["rol"] == "ADMINISTRADOR",
        )
        if old:
            cur.execute(
                "UPDATE productos SET existencia=existencia+:cantidad WHERE id_producto=:id",
                {"cantidad": old[2], "id": old[1]},
            )
        reserve_stock(cur, data.id_producto, data.cantidad)
        values = {
            "pedido": data.id_pedido,
            "producto": data.id_producto,
            "cantidad": data.cantidad,
            "precio": price,
        }
        if old:
            cur.execute(
                "UPDATE detalle_pedido SET id_producto=:producto,cantidad=:cantidad,precio_unitario=:precio WHERE id_detalle=:id",
                {
                    "producto": data.id_producto,
                    "cantidad": data.cantidad,
                    "precio": price,
                    "id": detail_id,
                },
            )
        else:
            detail_id = new_id(
                cur,
                "INSERT INTO detalle_pedido(id_pedido,id_producto,cantidad,precio_unitario) VALUES(:pedido,:producto,:cantidad,:precio)",
                {**values, "_pk": "id_detalle"},
            )
    return get_detail(detail_id, user)


def delete_detail(detail_id, user):
    # Initial read locates the order; check again under its lock before writing.
    detail = get_detail(detail_id, user)
    with database(write=True) as cur:
        order = order_for_user(cur, detail["id_pedido"], user, lock=True)
        editable_order(order[1], paid_total(cur, detail["id_pedido"]))
        cur.execute(
            "SELECT id_producto,cantidad FROM detalle_pedido WHERE id_detalle=:id FOR UPDATE",
            {"id": detail_id},
        )
        old = cur.fetchone()
        if not old:
            raise HTTPException(404, "Detalle no encontrado")
        cur.execute(
            "UPDATE productos SET existencia=existencia+:cantidad WHERE id_producto=:id",
            {"cantidad": old[1], "id": old[0]},
        )
        cur.execute(
            "DELETE FROM detalle_pedido WHERE id_detalle=:id", {"id": detail_id}
        )
    return {"mensaje": "Detalle eliminado y existencia devuelta"}
