from unittest.mock import MagicMock, Mock
import pytest
from fastapi import HTTPException
from backend.database import helpers
from backend.services import orders, payments
from backend.schemas.common import DetallePedidoIn, PagoIn

USER = {"id_usuario": 2, "rol": "VENDEDOR"}


@pytest.fixture
def db(monkeypatch):
    conn = MagicMock()
    cur = conn.cursor.return_value.__enter__.return_value
    monkeypatch.setattr(helpers, "get_connection", lambda: conn)
    return conn, cur


def test_stock_insuficiente_revierte_transaccion(db):
    conn, cur = db
    # order, paid total, product; atomic stock UPDATE then reports no affected row.
    cur.fetchone.side_effect = [(2, "PENDIENTE"), (0,), (100, 1)]
    cur.rowcount = 0
    with pytest.raises(HTTPException) as error:
        orders.save_detail(
            DetallePedidoIn(id_pedido=1, id_producto=4, cantidad=5), USER
        )
    assert error.value.status_code == 400
    conn.rollback.assert_called_once()
    conn.commit.assert_not_called()
    sql = [call.args[0] for call in cur.execute.call_args_list]
    assert "FOR UPDATE" in sql[0]
    assert any("existencia>=:cantidad" in text for text in sql)


def test_pago_excesivo_no_se_inserta(db):
    conn, cur = db
    # order, existing payments, detail total
    cur.fetchone.side_effect = [(2, "PENDIENTE"), (80,), (100,)]
    with pytest.raises(HTTPException) as error:
        payments.save_payment(PagoIn(id_pedido=1, monto=30, metodo="EFECTIVO"), USER)
    assert error.value.status_code == 400
    conn.rollback.assert_called_once()
    assert all(
        not call.args[0].startswith("INSERT") for call in cur.execute.call_args_list
    )


def test_cambio_cantidad_preserva_precio_y_stock(db, monkeypatch):
    conn, cur = db
    # order, payments, existing detail, current product price
    cur.fetchone.side_effect = [(2, "PENDIENTE"), (0,), (1, 4, 2, 100), (200, 1)]
    cur.rowcount = 1
    monkeypatch.setattr(
        orders, "get_detail", Mock(return_value={"precio_unitario": 100})
    )
    orders.save_detail(DetallePedidoIn(id_pedido=1, id_producto=4, cantidad=3), USER, 7)
    calls = cur.execute.call_args_list
    updated = [c for c in calls if c.args[0].startswith("UPDATE detalle_pedido")][0]
    assert updated.args[1]["precio"] == 100
    assert any(
        c.args[0].startswith("UPDATE productos SET existencia=existencia+")
        for c in calls
    )
    assert any(
        c.args[0].startswith("UPDATE productos SET existencia=existencia-")
        for c in calls
    )
    conn.commit.assert_called_once()


def test_cancelar_devuelve_stock_una_vez(db):
    from backend.schemas.common import PedidoIn

    conn, cur = db
    cur.fetchone.side_effect = [(2, "PENDIENTE"), (0,)]
    cur.fetchall.return_value = [(4, 3)]
    from unittest.mock import patch

    with patch.object(orders, "get_order", return_value={}):
        orders.update_order(1, PedidoIn(id_cliente=1, estado="CANCELADO"), USER)
    updates = [
        c
        for c in cur.execute.call_args_list
        if c.args[0].startswith("UPDATE productos")
    ]
    assert len(updates) == 1
    assert updates[0].args[1] == {"cantidad": 3, "id": 4}
    conn.commit.assert_called_once()


def test_pedido_ajeno_es_403(db):
    conn, cur = db
    cur.fetchone.return_value = (999, "PENDIENTE")
    with pytest.raises(HTTPException) as error:
        orders.get_order(1, USER)
    assert error.value.status_code == 403
