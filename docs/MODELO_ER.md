# Modelo entidad-relación

```mermaid
erDiagram
    ROLES ||--o{ USUARIOS : asigna
    USUARIOS ||--o{ PEDIDOS : registra
    CLIENTES ||--o{ PEDIDOS : solicita
    PROVEEDORES ||--o{ PRODUCTOS : suministra
    PEDIDOS ||--o{ DETALLE_PEDIDO : contiene
    PRODUCTOS ||--o{ DETALLE_PEDIDO : aparece
    PEDIDOS ||--o{ PAGOS : recibe
    ROLES {
        NUMBER id_rol PK
        VARCHAR2 nombre UK
    }
    USUARIOS {
        NUMBER id_usuario PK
        NUMBER id_rol FK
        VARCHAR2 correo UK
        VARCHAR2 hash_contrasena
    }
    PROVEEDORES {
        NUMBER id_proveedor PK
        VARCHAR2 nombre
    }
    PRODUCTOS {
        NUMBER id_producto PK
        NUMBER id_proveedor FK
        VARCHAR2 nombre
        NUMBER precio_venta
        NUMBER existencia
    }
    CLIENTES {
        NUMBER id_cliente PK
        VARCHAR2 nombre
    }
    PEDIDOS {
        NUMBER id_pedido PK
        NUMBER id_cliente FK
        NUMBER id_usuario FK
        VARCHAR2 estado
    }
    DETALLE_PEDIDO {
        NUMBER id_detalle PK
        NUMBER id_pedido FK
        NUMBER id_producto FK
        NUMBER cantidad
        NUMBER precio_unitario
    }
    PAGOS {
        NUMBER id_pago PK
        NUMBER id_pedido FK
        NUMBER monto
        VARCHAR2 estado
    }
```

Se permite crear una cabecera de pedido sin líneas para completar su formulario después. Para avanzar del estado PENDIENTE, el pedido debe tener un total positivo. Las tablas pueden no tener registros hijos; cada registro hijo siempre tiene su padre correspondiente. La relación muchos a muchos entre pedidos y productos se resuelve mediante detalle_pedido.
