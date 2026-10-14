from fastapi import APIRouter, Depends, Query
from backend.schemas.common import ProveedorIn, ProductoIn, ClienteIn
from backend.security import get_current_user, require_admin
from backend.services import catalog

router = APIRouter(tags=["Catálogos"])


def add_routes(resource, schema):
    @router.get("/" + resource, name="listar_" + resource)
    def listar(
        q: str | None = Query(None, max_length=100),
        activo: int | None = Query(None, ge=0, le=1),
        user=Depends(get_current_user),
    ):
        return catalog._list(resource, q, activo)

    @router.get("/" + resource + "/{item_id}", name="obtener_" + resource)
    def obtener(item_id: int, user=Depends(get_current_user)):
        return catalog._get(resource, item_id)

    @router.post("/" + resource, status_code=201, name="crear_" + resource)
    def crear(data: schema, user=Depends(get_current_user)):
        return catalog._create(resource, data)

    @router.put("/" + resource + "/{item_id}", name="actualizar_" + resource)
    def actualizar(item_id: int, data: schema, user=Depends(get_current_user)):
        return catalog._update(resource, item_id, data)

    @router.delete("/" + resource + "/{item_id}", name="eliminar_" + resource)
    def eliminar(item_id: int, user=Depends(require_admin)):
        return catalog._delete(resource, item_id)


add_routes("proveedores", ProveedorIn)
add_routes("productos", ProductoIn)
add_routes("clientes", ClienteIn)
