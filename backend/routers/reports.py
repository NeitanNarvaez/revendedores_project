from datetime import date
from fastapi import APIRouter, Depends
from backend.security import get_current_user
from backend.services import reports

router = APIRouter(tags=["Dashboard y reportes"])


@router.get("/dashboard")
def dashboard(user=Depends(get_current_user)):
    return reports.dashboard(user)


@router.get("/reportes/ventas-cliente")
def ventas_cliente(user=Depends(get_current_user)):
    return reports.ventas_cliente(user)


@router.get("/reportes/ventas-proveedor")
def ventas_proveedor(user=Depends(get_current_user)):
    return reports.ventas_proveedor(user)


@router.get("/reportes/ventas-periodo")
def ventas_periodo(desde: date, hasta: date, user=Depends(get_current_user)):
    return reports.ventas_periodo(desde, hasta, user)
