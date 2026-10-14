from fastapi import APIRouter, Depends
from backend.schemas.common import LoginIn, RegisterIn, UsuarioUpdate
from backend.security import get_current_user, require_admin
from backend.services import auth

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/register", status_code=201)
def register(data: RegisterIn):
    return auth.register(data)


@router.post("/login")
def login(data: LoginIn):
    return auth.login(data)


@router.get("/me")
def me(user=Depends(get_current_user)):
    return user


@router.get("/usuarios")
def usuarios(admin=Depends(require_admin)):
    return auth.listar_usuarios(admin)


@router.post("/admin/usuarios", status_code=201)
def crear_usuario(data: RegisterIn, admin=Depends(require_admin)):
    return auth.crear_usuario_admin(data, admin)


@router.put("/usuarios/{user_id}")
def editar_usuario(user_id: int, data: UsuarioUpdate, admin=Depends(require_admin)):
    return auth.editar_usuario(user_id, data, admin)


@router.put("/usuarios/{user_id}/estado")
def estado_usuario(user_id: int, activo: int, admin=Depends(require_admin)):
    return auth.cambiar_estado_usuario(user_id, activo, admin)


@router.get("/roles")
def roles(admin=Depends(require_admin)):
    return auth.listar_roles(admin)
