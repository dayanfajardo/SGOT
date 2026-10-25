# Manual de Usuario SGOT

Este manual explica cómo usar SGOT en el día a día. Está escrito para el personal de la empresa.

SGOT es el sistema interno de órdenes de trabajo. La pantalla de ingreso muestra la marca Centinela de Occidente Ltda.

[CAPTURA: Login]

---

## Introducción

SGOT sirve para seguir una orden de trabajo desde que almacén la registra hasta que queda completada.

Ahí se consulta:

- quién es el cliente y el comercial;
- qué equipos o materiales se pidieron;
- en qué estado va la orden;
- qué técnico y qué fecha tiene;
- qué salió de almacén, qué se devolvió y qué se utilizó;
- quién hizo cada cambio importante.

SGOT no reemplaza la orden física, la factura ni el inventario del sistema contable. El número de la orden y el número de la salida se escriben tal como vienen en el documento. El sistema no los inventa.

Los técnicos no entran a SGOT. Están registrados para asignarlos, pero no tienen usuario ni contraseña.

---

## Inicio de sesión

1. Abra la dirección que le entregue la empresa.
2. Escriba su **usuario** y su **contraseña**.
3. Pulse **Iniciar sesión**.

Si los datos son correctos, llega al Dashboard. Si la cuenta está inactiva, no podrá entrar: pida a un administrador que la active.

Para salir, pulse **Cerrar sesión** en la parte superior. Cerrar el navegador no sustituye ese paso en un equipo compartido.

Arriba también aparece su nombre y un botón para cambiar entre tema claro y tema oscuro. La preferencia se recuerda en ese navegador.

[CAPTURA: Barra superior con usuario y cerrar sesión]

---

## Roles

Su rol define qué botones ve. Si no ve una acción, normalmente corresponde a otro perfil.

| Rol | Para qué entra |
| --- | --- |
| Administrador | Registra y actualiza la operación. Además crea y cuida las cuentas de usuario. |
| Almacén | Hace el mismo trabajo operativo que el administrador: órdenes, estados, salidas, devoluciones, conciliación y cierre. No administra usuarios. |
| Comercial | Consulta solo las órdenes en las que él figura como comercial. Ve el estado, el técnico y la programación. No las modifica. |
| Jefe Técnica | Consulta las órdenes y es quien asigna técnico y fecha. |
| Gerencia | Consulta la operación. No registra ni modifica. |

---

## Dashboard

Al entrar verá un resumen de órdenes.

[CAPTURA: Dashboard]

Primera fila, por estado. Los nombres son los mismos de la orden:

- Recibida
- Pendiente por pedido con proveedor
- Equipos completos para instalación
- En instalación
- Completada

Segunda fila, de la programación:

- **Programadas hoy:** órdenes con fecha de hoy que aún no están completadas.
- **Atrasadas:** fecha ya pasada y todavía no completadas.
- **Próximas:** fecha futura y todavía no completadas.

Debajo hay dos listas, con un máximo de ocho órdenes cada una:

- **Requieren atención:** las atrasadas.
- **Próximas instalaciones:** las de fechas siguientes.

Puede abrir la orden haciendo clic en su número.

Si usted es comercial, los números y las listas cuentan únicamente sus órdenes. Los demás roles ven el conjunto de órdenes del sistema.

---

## Clientes

Menú **Clientes**.

[CAPTURA: Lista de clientes]

Puede buscar por nombre comercial, razón social, documento, código o correo, y filtrar por sistema: Centurión o Arion.

Al abrir un cliente verá su ficha: nombre comercial, razón social, documento o NIT, código, sistema, teléfono y correo.

[CAPTURA: Ficha de cliente]

**Administrador y Almacén** pueden crear y editar clientes. El nombre comercial es obligatorio. El código, si se escribe, no puede repetirse. El sistema (Centurión o Arion) es opcional.

Comercial, Jefe Técnica y Gerencia pueden consultar clientes. No los modifican.

No hay botón para borrar un cliente. Si ya tiene órdenes, el sistema conserva la ficha para no perder el historial.

---

## Técnicos

Menú **Técnicos**. Comercial no ve este menú.

[CAPTURA: Lista de técnicos]

Puede buscar por nombre y filtrar por tipo (Planta o Contratista) y por activo o inactivo.

La ficha muestra nombre, apellido, teléfono y tipo.

**Administrador y Almacén** pueden:

- crear un técnico;
- editar sus datos;
- marcarlo activo o inactivo.

Un técnico inactivo no aparece para programar una orden ni para una salida nueva. Las órdenes que ya lo tenían siguen mostrando su nombre.

Jefe Técnica y Gerencia consultan el listado. No lo modifican.

El técnico no recibe clave de SGOT.

[CAPTURA: Ficha de técnico]

---

## Productos

Menú **Productos**.

[CAPTURA: Lista de productos]

Cada producto tiene:

- **Código.** Tres números separados por guion, por ejemplo `2-1-20`. Debe ser único.
- **Nombre.**
- **Referencia / modelo.** Puede ir vacío.
- **Categoría.** Tiene que coincidir con el inicio del código:

| Si el código empieza por | La categoría es |
| --- | --- |
| 2-1 | Intrusión |
| 1-1 | CCTV |
| 1-2 | Cercas eléctricas |
| 1-3 | Control de acceso |
| 1-4 | Línea vehicular |
| 1-5 | Materiales y accesorios |

- **Tipo.** Equipo o Material. Lo que empieza por `1-5` debe ser Material.
- **Unidad.** Unidad, Metro, Rollo o Caja.
- **Activo o inactivo.**

Puede buscar por código, nombre o referencia, y filtrar por categoría, tipo y estado.

**Administrador y Almacén** crean, editan y activan o desactivan. Un producto inactivo deja de ofrecerse al armar una orden o una salida nueva. No se borra.

Los demás roles que ven el menú solo consultan. Comercial no administra el catálogo, pero sí puede consultarlo.

[CAPTURA: Ficha de producto]

---

## Tipos de trabajo

Menú **Tipos de trabajo**.

[CAPTURA: Lista de tipos de trabajo]

Un tipo tiene nombre, que no se repite, y una descripción opcional. Puede estar activo o inactivo.

**Administrador y Almacén** los crean, editan y activan o desactivan. El resto de roles que ven el menú solo consulta.

Al registrar una orden hay que elegir uno de estos tipos. Conviene dejar inactivo un tipo que ya no se use, en lugar de reutilizar el nombre para otra cosa: las órdenes viejas siguen apuntando a ese tipo.

---

## Órdenes de trabajo

Menú **Órdenes de trabajo**.

[CAPTURA: Lista de órdenes]

La lista muestra número, cliente, comercial, tipo de trabajo, estado, técnico, fecha recibida y fecha programada.

Puede buscar por número de orden, nombre comercial o código de cliente, y filtrar por estado, técnico, comercial y fecha programada. El comercial no ve el filtro de comercial: la lista ya está limitada a sus órdenes.

**Nueva orden** solo aparece para Administrador y Almacén.

### De la orden nueva al cierre

Este es el recorrido normal. Varias personas intervienen. La orden es una sola.

#### 1. Registrar la OT

Lo hacen **Administrador o Almacén**.

1. Pulse **Nueva orden**.
2. Escriba el número de la orden física. No puede repetirse.
3. Elija cliente, comercial, tipo de trabajo y fecha de recepción.
4. Si la tiene, escriba la dirección de instalación y las notas.
5. En **Equipos / productos**, agregue cada producto activo y la cantidad pedida. La cantidad debe ser mayor que cero. Use **+ Agregar producto** para más filas y **Quitar** si una fila sobra, antes de guardar.
6. Guarde.

La orden queda en **Recibida**.

El comercial que elija debe ser una persona activa con ese rol.

[CAPTURA: Formulario de nueva orden]

#### 2. Revisar equipos

Abra la orden. La sección **Productos / equipos** muestra lo solicitado. Esa lista queda como constancia: la pantalla de la orden no permite cambiarla después.

[CAPTURA: Detalle OT]

#### 3. Cambiar estado

Lo hacen **Administrador o Almacén**, con **Actualizar estado**.

- De **Recibida** puede pasar a **Pendiente por pedido con proveedor** o a **Equipos completos para instalación**.
- De **Pendiente por pedido con proveedor** solo puede pasar a **Equipos completos para instalación**.

No se puede devolver la orden a un estado anterior.

Use Pendiente por pedido con proveedor cuando falte pedir o recibir equipo del proveedor. Use Equipos completos para instalación cuando ya se pueda programar e instalar.

#### 4. Programar técnico

Lo hace **Jefe Técnica**, cuando la orden ya está en Equipos completos para instalación.

En **Programación técnica** elija un técnico activo y la fecha. Pulse **Guardar programación**.

La orden sigue en Equipos completos para instalación. Programar no la pasa a otro estado.

[CAPTURA: Programación técnica]

#### 5. Crear la salida

Lo hacen **Administrador o Almacén**.

El botón **Crear salida de almacén** aparece cuando ya hay técnico, fecha programada, el estado es Equipos completos para instalación y todavía no existe salida.

1. Escriba el número de la salida física y la fecha de salida.
2. Agregue las líneas.
3. Guarde.

El técnico de la salida es el que ya está asignado a la orden. No se elige otro en este formulario.

[CAPTURA: Crear salida de almacén]

#### 6. Iniciar instalación

Lo hacen **Administrador o Almacén**, con **Iniciar instalación**.

Hace falta que la orden esté en Equipos completos para instalación, con técnico, fecha y salida ya creada. Al confirmar, el estado pasa a **En instalación** y queda registrada la fecha de inicio.

#### 7. Registrar devoluciones

Lo hacen **Administrador o Almacén**, con la orden En instalación y la salida todavía sin conciliar.

En la salida, pulse **Registrar devoluciones** y escriba, por cada línea, cuánto volvió. Cero es válido. No puede devolver más de lo entregado.

[CAPTURA: Registrar devoluciones]

#### 8. Conciliar

Lo hacen **Administrador o Almacén**, con **Conciliar salida**, en el mismo momento: orden En instalación y salida sin conciliar.

Al conciliar, las cantidades devueltas quedan cerradas. Ya no se pueden corregir por esta pantalla. La salida pasa a mostrarse como **Conciliada**, con fecha y persona que concilió.

[CAPTURA: Salida conciliada]

#### 9. Completar

Lo hacen **Administrador o Almacén**, con **Completar orden**.

Solo se ofrece cuando la orden está En instalación y la salida ya está conciliada. El estado pasa a **Completada** y queda la fecha de cierre.

[CAPTURA: Orden completada]

### Qué ve cada perfil durante el recorrido

| Paso | Administrador y Almacén | Jefe Técnica | Comercial | Gerencia |
| --- | --- | --- | --- | --- |
| Registrar la orden | Sí | No | No | No |
| Cambiar estado de equipos | Sí | No | No | No |
| Programar | No | Sí | No | No |
| Crear salida, iniciar, devolver, conciliar y completar | Sí | No | No | No |
| Consultar | Sí, todas | Sí, todas | Solo las suyas | Sí, todas |

Comercial y Gerencia no tienen botones de cambio. Jefe Técnica tiene el formulario de programación y no los demás botones de la operación.

---

## Reprogramaciones

Si la orden ya tiene fecha y Jefe Técnica la cambia, el **motivo de reprogramación** es obligatorio. El recuadro solo aparece cuando ya existe una fecha. El texto de ayuda lo recuerda: es obligatorio si cambia la fecha actualmente programada.

Si solo cambia el técnico y la fecha sigue igual, no se pide motivo.

Si guarda técnico y fecha iguales a los que ya están, el sistema avisa que no hay cambios.

La fecha nueva reemplaza a la anterior. El historial conserva las dos y el motivo.

No se pueden anotar varias visitas por separado. La orden tiene una fecha vigente, un inicio y un cierre.

[CAPTURA: Motivo de reprogramación]

---

## Almacén

No hay una pantalla general de almacén ni un ítem de menú con ese nombre. Todo está dentro de la orden, en **Salida de almacén**.

[CAPTURA: Sección salida de almacén]

Qué puede registrar:

- **Salida.** Una sola por orden. Si ya existe, no aparece de nuevo el botón de crearla.
- **Material de la orden.** Elija el ítem solicitado. El mismo ítem no se repite en la salida.
- **Material adicional.** Si salió algo que no estaba en la orden, elija el producto y deje el ítem de la orden vacío. En la tabla se ve como **Adicional**. En cada línea se usa una de las dos opciones, no las dos.
- **Cantidad entregada.** Mayor que cero.
- **Cantidad devuelta.** Lo que regresa después de la instalación. Se llena en Registrar devoluciones, no al crear la salida.
- **Cantidad utilizada.** La calcula el sistema: entregada menos devuelta. No se escribe a mano.
- **Conciliación.** Cierra las devoluciones. Sin ese cierre no se puede completar la orden.

La salida muestra número, técnico, fecha, quién la creó, si está pendiente de conciliación o conciliada, y las notas.

---

## Historial

Al final de la orden está **Historial**.

[CAPTURA: Historial de la orden]

Sirve para ver qué pasó, sin depender de la memoria de quien estuvo ese día. Cada fila tiene:

- fecha y hora;
- tipo de evento (creación, cambio de estado, programación, reprogramación, cambio de técnico, inicio de instalación o finalización);
- usuario que lo hizo;
- descripción;
- valor anterior y valor nuevo.

En una reprogramación, la descripción incluye el motivo.

La conciliación no sale como fila de este historial. Se consulta en la propia salida: fecha de conciliación y quién concilió.

Quien puede abrir la orden puede leer este historial.

---

## Usuarios

Solo **Administrador**. Menú **Usuarios**.

[CAPTURA: Lista de usuarios]

Puede buscar por usuario, nombre, apellido o correo, y filtrar por rol y por activo o inactivo.

### Crear

1. Pulse **Nuevo usuario**.
2. Escriba el username, el nombre, el apellido y, si lo tiene, el correo.
3. Elija el rol: Administrador, Almacén, Comercial, Jefe Técnica o Gerencia.
4. Escriba la **contraseña inicial** y confírmela.
5. Guarde.

Entregue esa contraseña a la persona por un medio seguro. SGOT no la envía por correo.

La contraseña no puede ser muy corta, solo números, demasiado común ni muy parecida al nombre o al usuario. El mínimo que aplica el sistema es de 8 caracteres, además de esas reglas.

[CAPTURA: Crear usuario]

### Editar y cambiar rol

En la ficha, **Editar**. Puede corregir nombre, apellido, correo, username y rol.

Cambiar el username cambia la palabra con la que esa persona entra. Al editarlo, use minúsculas, números, punto, guion o guion bajo, sin espacios.

Una persona solo queda con el rol elegido. No acumula varios.

Usted no puede quitarse su propio rol de Administrador. Así se evita dejar el sistema sin quien administre las cuentas.

### Activar o desactivar

En la ficha:

- **Desactivar usuario** impide el ingreso y conserva la cuenta y todo lo que esa persona registró.
- **Activar usuario** vuelve a permitir el ingreso.

No puede desactivar su propia cuenta. No existe la opción de borrar un usuario.

### Restablecer contraseña

**Restablecer contraseña** permite escribir una clave nueva y confirmarla. Úselo cuando la persona olvidó la suya o cuando debe dejar de usar la anterior. No llega un correo con un enlace: la nueva clave la define el administrador y se la comunica a la persona.

[CAPTURA: Restablecer contraseña]

---

## Preguntas frecuentes

### ¿Por qué no puedo iniciar una instalación?

El botón solo lo ven Administrador y Almacén, y solo si se cumple todo esto:

- la orden está en Equipos completos para instalación;
- tiene técnico asignado;
- tiene fecha programada;
- ya tiene salida de almacén.

Si falta la programación, corresponde a Jefe Técnica. Si falta la salida, corresponde a Almacén o al Administrador.

### ¿Por qué no puedo completar una OT?

Completar solo aparece para Administrador y Almacén cuando la orden está **En instalación** y la salida ya está **conciliada**. Si sigue pendiente de conciliación, primero registre las devoluciones que correspondan y después concilie.

### ¿Por qué no puedo programar?

Programar corresponde a **Jefe Técnica**. Además, la orden tiene que estar en Equipos completos para instalación. En Recibida o en Pendiente por pedido con proveedor el formulario no se muestra.

### ¿Por qué no veo todas las órdenes?

Si su rol es Comercial, SGOT muestra solo las órdenes en las que usted es el comercial. Si busca una orden de otro asesor, no aparecerá y tampoco podrá abrirla por el número.

### ¿Qué pasa si un usuario deja la empresa?

El administrador **desactiva** la cuenta. La persona deja de entrar. Sus órdenes, salidas e historial se conservan con su nombre. No se borra el usuario.

### ¿Qué significa conciliar una salida?

Significa cerrar las cantidades devueltas. A partir de ese momento no se corrigen por la pantalla de devoluciones. La conciliación es el paso previo obligatorio para completar la orden. Indica que almacén ya revisó lo entregado, lo devuelto y, por diferencia, lo utilizado.

### ¿Puedo crear dos salidas para la misma orden?

No. Cada orden tiene una sola salida, y sus líneas se escriben al crearla. Después de guardarla, la pantalla no ofrece agregar productos ni cambiar lo entregado. Mientras la orden está En instalación y la salida no está conciliada, solo se pueden registrar las devoluciones. Después de conciliar, tampoco se pueden cambiar las devoluciones.

### ¿Puedo anotar un material que no venía en la orden?

Sí, al crear la salida, como material adicional. La lista original de la orden no se modifica.

### ¿Puedo borrar una orden o un cliente?

La pantalla de trabajo no ofrece borrar órdenes, clientes, productos, técnicos ni tipos de trabajo. Los catálogos se desactivan cuando dejan de usarse. La orden completada permanece como constancia.

### ¿El técnico puede consultar su programación en SGOT?

No. Quien consulta y asigna es el personal con usuario. El técnico es un dato de la orden.

### ¿Dónde registro una salida de almacén?

En la orden de trabajo, sección **Salida de almacén**. No hay un menú aparte de Almacén.

### ¿Qué hago si olvidé mi contraseña?

Pida a un administrador que use **Restablecer contraseña**. No hay recuperación automática por correo.
