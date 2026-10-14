from typing import Literal
from fastapi import APIRouter, Depends, Query
from backend.schemas.common import PedidoIn, DetallePedidoIn
from backend.security import get_current_user
from backend.services import orders

router = APIRouter(tags=["Pedidos"])


@router.get("/pedidos")
def listar(
    estado: (
        Literal["PENDIENTE", "CONFIRMADO", "ENVIADO", "ENTREGADO", "CANCELADO"] | None
    ) = None,
    id_cliente: int | None = Query(None, gt=0),
    user=Depends(get_current_user),
):
    return orders.list_orders(user, estado, id_cliente)


@router.get("/pedidos/{item_id}")
def obtener(item_id: int, user=Depends(get_current_user)):
    return orders.get_order(item_id, user)


@router.post("/pedidos", status_code=201)
def crear(data: PedidoIn, user=Depends(get_current_user)):
    return orders.create_order(data, user)


@router.put("/pedidos/{item_id}")
def actualizar(item_id: int, data: PedidoIn, user=Depends(get_current_user)):
    return orders.update_order(item_id, data, user)


@router.delete("/pedidos/{item_id}")
def eliminar(item_id: int, user=Depends(get_current_user)):
    return orders.delete_order(item_id, user)


@router.get("/detalle-pedidos")
def detalles(id_pedido: int | None = Query(None, gt=0), user=Depends(get_current_user)):
    return orders.list_details(user, id_pedido)


@router.get("/detalle-pedidos/{item_id}")
def detalle(item_id: int, user=Depends(get_current_user)):
    return orders.get_detail(item_id, user)


@router.post("/detalle-pedidos", status_code=201)
def agregar_detalle(data: DetallePedidoIn, user=Depends(get_current_user)):
    return orders.save_detail(data, user)


@router.put("/detalle-pedidos/{item_id}")
def editar_detalle(item_id: int, data: DetallePedidoIn, user=Depends(get_current_user)):
    return orders.save_detail(data, user, item_id)


@router.delete("/detalle-pedidos/{item_id}")
def quitar_detalle(item_id: int, user=Depends(get_current_user)):
    return orders.delete_detail(item_id, user)
