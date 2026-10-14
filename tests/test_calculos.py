from decimal import Decimal
from datetime import date
import pytest
from fastapi import HTTPException
from backend.services.rules import (
    calcular_precio_venta,
    validate_period,
    validate_payment,
    editable_order,
    applied_price,
)


@pytest.mark.parametrize(
    "cost,margin,expected",
    [
        (40000, 25, "50000.00"),
        (12500, 0, "12500.00"),
        ("0.10", 10, "0.11"),
        ("1.01", 50, "1.52"),
    ],
)
def test_precio_real_del_servicio(cost, margin, expected):
    assert calcular_precio_venta(cost, margin) == Decimal(expected)


def test_precio_no_desborda_columna_oracle():
    with pytest.raises(HTTPException) as error:
        calcular_precio_venta("9999999999.99", 100)
    assert error.value.status_code == 400


def test_periodo_invertido():
    with pytest.raises(HTTPException):
        validate_period(date(2026, 2, 1), date(2026, 1, 1))
    validate_period(date(2026, 1, 1), date(2026, 1, 1))


@pytest.mark.parametrize(
    "total,paid,amount,state",
    [(100, 90, 11, "PENDIENTE"), (0, 0, 1, "PENDIENTE"), (100, 0, 10, "CANCELADO")],
)
def test_pago_invalido(total, paid, amount, state):
    with pytest.raises(HTTPException) as error:
        validate_payment(total, paid, amount, state)
    assert error.value.status_code == 400


def test_pago_decimal_exacto():
    validate_payment("0.30", "0.10", "0.20", "PENDIENTE")


@pytest.mark.parametrize(
    "state,paid", [("CANCELADO", 0), ("ENTREGADO", 0), ("PENDIENTE", 1)]
)
def test_no_editar_detalle_cerrado_o_pagado(state, paid):
    with pytest.raises(HTTPException):
        editable_order(state, paid)


def test_editar_cantidad_conserva_precio_historico():
    assert applied_price(200, 100, None, True, False) == Decimal("100.00")
    assert applied_price(200, 100, None, False, False) == Decimal("200.00")
    with pytest.raises(HTTPException) as error:
        applied_price(200, 100, 90, True, False)
    assert error.value.status_code == 403
    assert applied_price(200, 100, 90, True, True) == Decimal("90.00")
