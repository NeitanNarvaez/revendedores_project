-- Datos iniciales de catalogos. Ejecutar despues de 01_tables.sql.
INSERT INTO roles (nombre, descripcion) VALUES ('ADMINISTRADOR', 'Gestion total del sistema');
INSERT INTO roles (nombre, descripcion) VALUES ('VENDEDOR', 'Gestion de clientes, productos y pedidos autorizados');

INSERT INTO proveedores (nombre, contacto, telefono, correo, direccion) VALUES
('Proveedor Demo', 'Contacto Comercial', '3000000000', 'proveedor@example.com', 'Cali, Colombia');
INSERT INTO clientes (nombre, telefono, correo, direccion) VALUES
('Cliente Demo', '3100000000', 'cliente@example.com', 'Cali, Colombia');

INSERT INTO productos (id_proveedor,nombre,descripcion,precio_compra,margen_porcentaje,precio_venta,existencia)
SELECT id_proveedor,'Camiseta deportiva','Talla M',40000,25,50000,10
FROM proveedores WHERE nombre='Proveedor Demo';
INSERT INTO productos (id_proveedor,nombre,descripcion,precio_compra,margen_porcentaje,precio_venta,existencia)
SELECT id_proveedor,'Gorra','Color negro',20000,50,30000,8
FROM proveedores WHERE nombre='Proveedor Demo';

-- Crear un usuario real con la API /api/auth/register. No insertar contrasenas en texto plano.
COMMIT;
