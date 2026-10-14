from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator


class InputModel(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True, extra="forbid", allow_inf_nan=False
    )


class LoginIn(InputModel):
    correo: EmailStr
    contrasena: str = Field(min_length=8, max_length=72)

    @field_validator("contrasena")
    @classmethod
    def password_bytes(cls, value):
        if len(value.encode("utf-8")) > 72:
            raise ValueError("La contraseña no puede superar 72 bytes UTF-8")
        return value

    model_config = ConfigDict(str_strip_whitespace=False, extra="forbid")


class RegisterIn(LoginIn):
    nombre: str = Field(min_length=2, max_length=100)

    @field_validator("nombre")
    @classmethod
    def clean_name(cls, value):
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Escribe un nombre válido")
        return value


class UsuarioUpdate(InputModel):
    nombre: str = Field(min_length=2, max_length=100)
    correo: EmailStr
    rol: Literal["ADMINISTRADOR", "VENDEDOR"]
    activo: Literal[0, 1] = 1


class ProveedorIn(InputModel):
    nombre: str = Field(min_length=2, max_length=120)
    contacto: str | None = Field(None, max_length=100)
    telefono: str | None = Field(None, max_length=30)
    correo: EmailStr | None = None
    direccion: str | None = Field(None, max_length=250)
    activo: Literal[0, 1] = 1


class ProductoIn(InputModel):
    id_proveedor: int = Field(gt=0)
    nombre: str = Field(min_length=2, max_length=150)
    descripcion: str | None = Field(None, max_length=500)
    precio_compra: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    margen_porcentaje: Decimal = Field(default=0, ge=0, max_digits=7, decimal_places=2)
    existencia: int = Field(default=0, ge=0, le=9999999999)
    activo: Literal[0, 1] = 1


class ClienteIn(InputModel):
    nombre: str = Field(min_length=2, max_length=120)
    telefono: str | None = Field(None, max_length=30)
    correo: EmailStr | None = None
    direccion: str | None = Field(None, max_length=250)


class PedidoIn(InputModel):
    id_cliente: int = Field(gt=0)
    estado: Literal["PENDIENTE", "CONFIRMADO", "ENVIADO", "ENTREGADO", "CANCELADO"] = (
        "PENDIENTE"
    )
    observaciones: str | None = Field(None, max_length=500)


class DetallePedidoIn(InputModel):
    id_pedido: int = Field(gt=0)
    id_producto: int = Field(gt=0)
    cantidad: int = Field(gt=0, le=9999999999)
    precio_unitario: Decimal | None = Field(None, ge=0, max_digits=12, decimal_places=2)


class PagoIn(InputModel):
    id_pedido: int = Field(gt=0)
    monto: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    metodo: Literal["EFECTIVO", "TRANSFERENCIA", "TARJETA", "OTRO"]
    referencia: str | None = Field(None, max_length=100)
    estado: Literal["REGISTRADO", "ANULADO"] = "REGISTRADO"
