"""Business rules kept small so they can be explained and tested independently."""

from decimal import Decimal, ROUND_HALF_UP
from fastapi import HTTPException


def money(value):
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calcular_precio_venta(precio_compra, margen_porcentaje):
    result = money(
        Decimal(str(precio_compra)) * (1 + Decimal(str(margen_porcentaje)) / 100)
    )
    if result > Decimal("9999999999.99"):
        raise HTTPException(400, "El precio calculado supera el máximo permitido")
    return result


def validate_period(desde, hasta):
    if desde > hasta:
        raise HTTPException(400, "La fecha inicial no puede ser posterior a la final")


def validate_payment(total, paid, amount, order_state):
    if order_state == "CANCELADO":
        raise HTTPException(400, "No se puede pagar un pedido cancelado")
    if money(total) <= 0:
        raise HTTPException(400, "Agrega productos al pedido antes de registrar pagos")
    if money(paid) + money(amount) > money(total):
        raise HTTPException(400, "El pago supera el saldo pendiente del pedido")


def editable_order(state, paid):
    if state in ("CANCELADO", "ENTREGADO"):
        raise HTTPException(400, "El pedido no admite cambios de productos")
    if paid > 0:
        raise HTTPException(
            400,
            "Anula los pagos registrados antes de modificar los productos del pedido",
        )


def applied_price(
    current_price, historical_price, requested_price, same_product, is_admin
):
    base = historical_price if same_product else current_price
    if (
        requested_price is not None
        and money(requested_price) != money(base)
        and not is_admin
    ):
        raise HTTPException(
            403, "Solo un administrador puede cambiar el precio aplicado"
        )
    return money(base if requested_price is None else requested_price)
