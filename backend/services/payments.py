from fastapi import HTTPException
from backend.database.helpers import database, rows, new_id
from backend.services.orders import order_for_user, order_total
from backend.services.rules import validate_payment


def list_payments(user, id_pedido=None, estado=None):
    with database() as cur:
        sql = "SELECT pa.* FROM pagos pa JOIN pedidos p ON p.id_pedido=pa.id_pedido WHERE 1=1"
        params = {}
        if id_pedido:
            order_for_user(cur, id_pedido, user)
            sql += " AND pa.id_pedido=:pedido"
            params["pedido"] = id_pedido
        if estado:
            sql += " AND pa.estado=:estado"
            params["estado"] = estado
        if user["rol"] != "ADMINISTRADOR":
            sql += " AND p.id_usuario=:usuario"
            params["usuario"] = user["id_usuario"]
        cur.execute(sql + " ORDER BY pa.id_pago DESC", params)
        return rows(cur)


def get_payment(payment_id, user):
    with database() as cur:
        cur.execute("SELECT * FROM pagos WHERE id_pago=:id", {"id": payment_id})
        result = rows(cur)
        if not result:
            raise HTTPException(404, "Pago no encontrado")
        order_for_user(cur, result[0]["id_pedido"], user)
        return result[0]


def save_payment(data, user, payment_id=None):
    with database(write=True) as cur:
        order = order_for_user(cur, data.id_pedido, user, lock=True)
        if payment_id is not None:
            cur.execute(
                "SELECT id_pedido FROM pagos WHERE id_pago=:id FOR UPDATE",
                {"id": payment_id},
            )
            old = cur.fetchone()
            if not old:
                raise HTTPException(404, "Pago no encontrado")
            if old[0] != data.id_pedido:
                raise HTTPException(400, "No se puede mover un pago a otro pedido")
        if data.estado == "REGISTRADO":
            cur.execute(
                "SELECT NVL(SUM(monto),0) FROM pagos WHERE id_pedido=:pedido AND estado='REGISTRADO' AND id_pago<>:id",
                {"pedido": data.id_pedido, "id": payment_id or 0},
            )
            validate_payment(
                order_total(cur, data.id_pedido),
                cur.fetchone()[0],
                data.monto,
                order[1],
            )
        values = {
            "pedido": data.id_pedido,
            "monto": data.monto,
            "metodo": data.metodo,
            "ref": data.referencia,
            "estado": data.estado,
        }
        if payment_id is None:
            payment_id = new_id(
                cur,
                "INSERT INTO pagos(id_pedido,monto,metodo,referencia,estado) VALUES(:pedido,:monto,:metodo,:ref,:estado)",
                {**values, "_pk": "id_pago"},
            )
        else:
            cur.execute(
                "UPDATE pagos SET monto=:monto,metodo=:metodo,referencia=:ref,estado=:estado WHERE id_pago=:id",
                {
                    k: v
                    for k, v in {**values, "id": payment_id}.items()
                    if k != "pedido"
                },
            )
    return get_payment(payment_id, user)


def annul_payment(payment_id, user):
    payment = get_payment(payment_id, user)
    with database(write=True) as cur:
        order_for_user(cur, payment["id_pedido"], user, lock=True)
        cur.execute(
            "UPDATE pagos SET estado='ANULADO' WHERE id_pago=:id", {"id": payment_id}
        )
        if not cur.rowcount:
            raise HTTPException(404, "Pago no encontrado")
    return {"mensaje": "Pago anulado"}
