# Guion de sustentación (10–12 minutos)

1. **Problema y alcance (1 min):** explicar cómo un revendedor controla catálogos, pedidos, stock y abonos. Mostrar los cinco módulos principales.
2. **Modelo y arquitectura (2 min):** presentar diagrama ER y las tres capas. Identificar PK/FK y explicar por qué el detalle conserva el precio de venta histórico.
3. **Demostración como administrador (4 min):** iniciar sesión; crear cliente y producto; filtrar/buscar; crear pedido; agregar detalle; mostrar stock; registrar pago; mostrar dashboard/reporte. Consultar el registro en SQL Workshop para comprobar persistencia.
4. **Errores y permisos (2 min):** intentar cantidad mayor al stock, pago superior al saldo y edición del detalle con un pago. Iniciar como vendedor y mostrar 403 en una ruta administrativa desde Swagger.
5. **Código, pruebas y aportes (2–3 min):** mostrar router, esquema, servicio y SQL de una misma operación; ejecutar pytest; presentar evidencias Oracle y commits reales de cada integrante.

## Preguntas que cada integrante debe poder responder

- ¿Qué diferencia hay entre la interfaz, la API y la base de datos?
- ¿Por qué el navegador nunca recibe la contraseña Oracle?
- ¿Qué hace el token y dónde se comprueban los permisos?
- ¿Qué representan 201, 401, 403, 404, 409 y 422?
- ¿Qué tabla representa las líneas de un pedido y por qué existe?
- ¿Cómo se calcula el precio y cómo se conserva al cambiar el catálogo?
- ¿Qué sucede con el stock al cancelar un pedido?
- ¿Qué hacen commit, rollback y el bloqueo de la fila del pedido?
- ¿Qué probaste realmente con Oracle y qué comprobaste con conexiones simuladas?

## Antes de entregar

Completar integrantes y contribuciones, repetir los casos de PRUEBAS.md, adjuntar capturas reales y registrar dónde se ejecutó la demostración. No presentar resultados pendientes como si estuvieran aprobados.
