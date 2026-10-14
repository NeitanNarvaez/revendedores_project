from typing import Literal
from fastapi import APIRouter, Depends, Query
from backend.schemas.common import PagoIn
from backend.security import get_current_user, require_admin
from backend.services import payments

router = APIRouter(tags=["Pagos"])


@router.get("/pagos")
def listar(
    id_pedido: int | None = Query(None, gt=0),
    estado: Literal["REGISTRADO", "ANULADO"] | None = None,
    user=Depends(get_current_user),
):
    return payments.list_payments(user, id_pedido, estado)


@router.get("/pagos/{item_id}")
def obtener(item_id: int, user=Depends(get_current_user)):
    return payments.get_payment(item_id, user)


@router.post("/pagos", status_code=201)
def crear(data: PagoIn, user=Depends(get_current_user)):
    return payments.save_payment(data, user)


@router.put("/pagos/{item_id}")
def actualizar(item_id: int, data: PagoIn, user=Depends(require_admin)):
    return payments.save_payment(data, user, item_id)


@router.delete("/pagos/{item_id}")
def anular(item_id: int, user=Depends(require_admin)):
    return payments.annul_payment(item_id, user)
