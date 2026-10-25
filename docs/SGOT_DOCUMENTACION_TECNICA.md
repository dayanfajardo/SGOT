# SGOT

Documentación técnica de la versión 1.

Estado del sistema:

- **IMPLEMENTADO:** aplicación web operativa descrita en este documento.
- **EN PREPARACIÓN PARA DESPLIEGUE:** la V1 está desarrollada y probada en el repositorio. No hay configuración de producción (servidor de aplicaciones, HTTPS, `STATIC_ROOT`, logging ni respaldos automáticos).
- **PROPUESTO PARA FUTURAS VERSIONES:** mejoras identificables a partir del código actual. No constituyen un compromiso de alcance ni de fecha.

La interfaz de inicio de sesión identifica a la organización como **Centinela de Occidente Ltda.** Confirmar el nombre legal antes de la entrega definitiva.

Fecha de esta documentación: octubre de 2026.

---

## 1. Introducción

### Propósito

SGOT es una aplicación web interna para registrar y seguir órdenes de trabajo de una empresa de seguridad electrónica. Centraliza el recorrido operativo de una orden física ya existente: recepción, estado de equipos, programación del técnico, salida de almacén, instalación, devoluciones, conciliación y cierre.

SGOT complementa los documentos físicos y los sistemas que la empresa ya usa para inventario y facturación. No los reemplaza.

### Problema que resuelve

El seguimiento de una orden cruza comercial, almacén y área técnica. Sin un registro común, el estado, el técnico, la fecha, los materiales entregados y las devoluciones quedan dispersos. SGOT guarda ese recorrido en una sola orden, con el usuario y el momento de cada evento relevante.

### Alcance de V1

La versión 1 incluye:

- autenticación de usuarios internos y cinco roles;
- clientes, productos, técnicos y tipos de trabajo;
- órdenes de trabajo con ítems y cinco estados;
- programación y reprogramación;
- una salida de almacén por orden, con materiales de la orden y materiales adicionales;
- devoluciones, cantidad utilizada y conciliación;
- historial de la orden;
- un dashboard operativo con conteos, atrasos y próximas instalaciones;
- búsqueda y filtros en los listados principales.

Queda fuera de esta versión, porque no existe en el código:

- integración con SIIGO u otro sistema contable o de inventario;
- control de existencias, compras o proveedores;
- cotizaciones y facturación;
- ingreso de técnicos al sistema;
- aplicación móvil;
- API REST;
- notificaciones por correo;
- numeración automática de órdenes o de salidas;
- registro de varias visitas como entidades separadas;
- paneles de indicadores distintos del dashboard actual.

Los técnicos son un catálogo. No tienen usuario ni contraseña.

---

## 2. Stack tecnológico

Versiones fijadas en el repositorio:

| Componente | Versión o detalle | Dónde está |
| --- | --- | --- |
| Python | 3.12 (`python:3.12-slim`) | `Dockerfile` |
| Django | 5.2.17 | `requirements.txt` |
| PostgreSQL | 16 Alpine en Compose; el motor en configuración es `django.db.backends.postgresql` | `docker-compose.yml`, `config/settings.py` |
| Driver | `psycopg` 3.3.5 y `psycopg-binary` 3.3.5 | `requirements.txt` |
| Variables de entorno | `django-environ` 0.14.0 | `requirements.txt`, `config/settings.py` |
| Interfaz | Plantillas Django. No hay frontend separado | `templates/`, `apps/*/templates/` |
| CSS | Bootstrap 5.3.3 desde CDN y `static/css/sgot.css` | `templates/base.html` |
| JavaScript | `static/js/theme.js` (tema claro / oscuro) | `templates/base.html` |
| Tipografía | Inter Variable, cargada desde rsms.me | `static/css/sgot.css` |
| Contenedores | Docker y Docker Compose | `Dockerfile`, `docker-compose.yml` |
| Servidor de la imagen | `runserver` en el puerto 8000 | `Dockerfile`, `docker-compose.yml` |

Otras dependencias directas: `asgiref` 3.12.1, `sqlparse` 0.6.0, `typing_extensions` 4.16.0, `tzdata` 2026.4.

No están en el proyecto: Gunicorn, uWSGI, WhiteNoise, Nginx, Celery, Redis, React, Vue ni un archivo de requisitos de producción distinto de `requirements.txt`.

---

## 3. Arquitectura

SGOT es un monolito modular de Django. Cada dominio vive en una aplicación y las operaciones de orden y de almacén pasan por servicios. Las vistas autentican, comprueban permisos, validan formularios y delegan.

Aplicaciones instaladas, además de las contribuciones de Django (`admin`, `auth`, `contenttypes`, `sessions`, `messages`, `staticfiles`):

| Aplicación | Responsabilidad real |
| --- | --- |
| `apps.accounts` | Usuario propio (`AUTH_USER_MODEL`), login, logout y administración de usuarios. El comando `setup_roles` crea los grupos y sus permisos. |
| `apps.customers` | Ficha de cliente. No tiene `services.py`. |
| `apps.catalog` | Productos, técnicos y tipos de trabajo. No tiene `services.py`. |
| `apps.workorders` | Orden, ítems, historial, dashboard y transiciones. La lógica está en `services.py`. |
| `apps.warehouse` | Salida de almacén, ítems, devoluciones y conciliación. La lógica está en `services.py`. |

`config` contiene `settings.py`, `urls.py`, `wsgi.py` y `asgi.py`. El punto de entrada es `manage.py`.

Las vistas usan `@login_required`. Si el usuario autenticado no tiene el permiso, responden `PermissionDenied`. Comercial, además del permiso, solo ve las órdenes en las que figura como comercial.

Django Admin está habilitado en `/admin/` y los modelos están registrados. Un superusuario puede modificar registros por esa vía. La interfaz operativa es la que aplica los servicios. Admin no debe usarse para el día a día: puede alterar estados o cantidades sin pasar por `services.py`. El admin de `WarehouseOutput` ni siquiera muestra los campos de conciliación.

### Dependencias entre módulos

```
accounts.User
    ├── WorkOrder.commercial            (PROTECT)
    ├── WorkOrder.created_by            (PROTECT)
    ├── WorkOrderHistory.user           (PROTECT)
    ├── WarehouseOutput.created_by      (PROTECT)
    └── WarehouseOutput.reconciled_by   (PROTECT)

customers.Customer
    └── WorkOrder.customer              (PROTECT)

catalog.WorkType
    └── WorkOrder.work_type             (PROTECT)

catalog.Technician
    ├── WorkOrder.assigned_technician   (PROTECT, opcional)
    └── WarehouseOutput.technician      (PROTECT)

catalog.Product
    ├── WorkOrderItem.product           (PROTECT)
    └── WarehouseOutputItem.product     (PROTECT)

workorders.WorkOrder
    ├── WorkOrderItem                   (CASCADE)
    ├── WorkOrderHistory                (CASCADE)
    └── warehouse.WarehouseOutput       (OneToOne, PROTECT)
            └── WarehouseOutputItem     (CASCADE)
                    └── WorkOrderItem   (PROTECT, opcional)
```

`customers` y `catalog` no dependen de `workorders` ni de `warehouse`. `warehouse` depende de `workorders`, `catalog` y `accounts`. `workorders` consulta `WarehouseOutput` al iniciar o cerrar una orden.

---

## 4. Estructura del repositorio

Carpetas y archivos que importan para operar o mantener el sistema:

```
manage.py
requirements.txt
.env.example
Dockerfile
docker-compose.yml
config/
    settings.py
    urls.py
    wsgi.py
    asgi.py
apps/
    accounts/          modelos, vistas, formularios, setup_roles, pruebas
    customers/
    catalog/
    workorders/        incluye services.py
    warehouse/         incluye services.py
templates/base.html    marco de la aplicación autenticada
static/
    css/sgot.css
    js/theme.js
    img/logo-centinela.png
docs/                  esta documentación
```

Cada aplicación de dominio tiene `models.py`, `views.py`, `forms.py`, `urls.py`, `admin.py`, `migrations/` y `tests` o `tests.py`. Solo `workorders` y `warehouse` tienen `services.py`.

`apps/accounts/management/commands/setup_roles.py` es el único comando de gestión propio.

`.cursor/rules/` guarda convenciones de alcance, arquitectura y estilo usadas durante el desarrollo. No interviene en la ejecución de la aplicación.

No hay `README` en la raíz. No hay flujo de integración continua. `.gitignore` excluye `.env`, entornos virtuales, `db.sqlite3` y `staticfiles/`. La configuración actual no define `STATIC_ROOT` ni usa SQLite: la base configurada es PostgreSQL.

---

## 5. Modelo de datos

El usuario de autenticación es `accounts.User`, subclase de `AbstractUser`. El correo es único y puede quedar vacío (`blank` y `null`). El resto de campos de usuario son los de Django: nombre, apellido, `is_active`, `is_staff`, `is_superuser`, `last_login` y `date_joined`. Los roles no son un campo del usuario: son grupos de `django.contrib.auth`.

### Customer

Cliente. Campos: `customer_code` (único, opcional, máximo 20), `code_system` (`CENTURION` Centurión o `ARION` Arion, opcional), `trade_name`, `legal_name`, `document`, `phone`, `email`, `created_at`, `updated_at`. No tiene bandera de activo. Una migración anterior exigía el código único por sistema; la migración `0002` la reemplazó por unicidad global del código.

### Product

Equipo o material. Campos: `product_code` (único, obligatorio), `name`, `reference`, `category`, `product_type` (Equipo o Material), `unit` (Unidad, Metro, Rollo, Caja), `active`, `created_at`, `updated_at`.

Categorías y prefijo de código:

| Prefijo | Categoría |
| --- | --- |
| 2-1 | Intrusión |
| 1-1 | CCTV |
| 1-2 | Cercas eléctricas |
| 1-3 | Control de acceso |
| 1-4 | Línea vehicular |
| 1-5 | Materiales y accesorios |

El código tiene tres segmentos numéricos separados por guion, por ejemplo `2-1-20`. La categoría debe coincidir con el prefijo. El prefijo `1-5` solo admite tipo Material. La validación está en `validate_product_code` y se ejecuta en `Product.clean()`.

### Technician

Nombre, apellido opcional, teléfono opcional, tipo (`STAFF` Planta o `CONTRACTOR` Contratista), `active` y fechas. No está ligado a `User`.

### WorkType

`name` único, `description` opcional, `active` y fechas.

### WorkOrder

Orden de trabajo. El número es texto único de hasta 20 caracteres, escrito por quien registra. No hay secuencia automática.

Relaciones: cliente, comercial y tipo de trabajo con `PROTECT`; técnico asignado opcional con `PROTECT`; `created_by` con `PROTECT`.

Estados (`WorkOrder.Status`):

| Valor interno | Etiqueta del modelo y de las insignias |
| --- | --- |
| `RECEIVED` | Recibida |
| `PENDING_EQUIPMENT` | Pendiente por pedido con proveedor |
| `EQUIPMENT_OK` | Equipos completos para instalación |
| `IN_INSTALLATION` | En instalación |
| `COMPLETED` | Completada |

El alta deja la orden en Recibida. También guarda fecha de recepción, fecha programada, inicio de instalación, cierre, dirección, notas y marcas de tiempo. Hay índices por estado, fecha de recepción y fecha programada. Orden por defecto: fecha de recepción descendente y luego id.

Permiso propio del modelo: `schedule_workorder` (“Puede programar órdenes de trabajo”).

### WorkOrderItem

Ítem solicitado. `CASCADE` hacia la orden y `PROTECT` hacia el producto. `requested_quantity` es decimal (10 dígitos, 2 decimales) y debe ser mayor que cero (`workorderitem_requested_quantity_positive`). Notas opcionales. La cantidad original no se recalcula después: la interfaz operativa no edita la orden una vez creada.

### WorkOrderHistory

Evento de la orden. `CASCADE` hacia la orden y `PROTECT` hacia el usuario. Ver la sección 11.

### WarehouseOutput

Salida física. Número único escrito a mano. `work_order` es `OneToOneField` con `PROTECT` y `related_name="warehouse_output"`: una orden admite como máximo una salida, también a nivel de base de datos. Técnico, fecha de salida, notas, `created_by`, fechas, `reconciled_at` y `reconciled_by` (ambos opcionales, el usuario con `PROTECT`).

### WarehouseOutputItem

Ítem entregado. `CASCADE` hacia la salida, `PROTECT` hacia el producto y `PROTECT` opcional hacia `WorkOrderItem`. Si `work_order_item` está vacío, el ítem es material adicional.

`delivered_quantity` y `returned_quantity` son decimales (10, 2). Restricciones:

- entregada mayor que cero;
- devuelta mayor o igual que cero;
- devuelta menor o igual que entregada.

`used_quantity` no es una columna. Es la propiedad `delivered_quantity - returned_quantity`.

Los formularios de salida y de devolución piden cantidades enteras. El modelo acepta decimales.

---

## 6. Roles y permisos

`python manage.py setup_roles` crea o actualiza exactamente estos grupos y les asigna la matriz de abajo. El comando es idempotente: volver a ejecutarlo no duplica grupos y deja los permisos de esos cinco grupos como aquí se indican.

| Rol | Qué puede hacer en la aplicación |
| --- | --- |
| Administrador | Operación completa: clientes, catálogo, órdenes (alta y cambio), salidas, devoluciones y conciliación. Además consulta, crea y edita usuarios. Programa órdenes solo si además tuviera el permiso de programación; la matriz no se lo da. |
| Almacén | La misma operación que Administrador, sin gestión de usuarios. Tampoco tiene el permiso de programación. |
| Comercial | Consulta clientes, productos, tipos de trabajo y órdenes. En dashboard, listado y detalle solo ve las órdenes donde él es el comercial. No crea ni modifica. |
| Jefe Técnica | Consulta clientes, productos, técnicos, tipos de trabajo y órdenes. Es el único rol con `workorders.schedule_workorder`. No cambia el estado, no crea salidas y no cierra la orden. |
| Gerencia | Consulta operativa: clientes, catálogo, órdenes, historial (permiso) y salidas. Sin altas ni cambios. |

Ningún rol de la matriz tiene `accounts.delete_user`. La interfaz no ofrece borrar usuarios.

Detalle útil para soporte:

- Registrar, cambiar estado, iniciar instalación y completar exigen permisos de cambio de orden. Los tienen Administrador y Almacén.
- Crear la salida exige `warehouse.add_warehouseoutput`. Registrar devoluciones y conciliar exigen `warehouse.change_warehouseoutput`. Los tienen Administrador y Almacén.
- Programar exige `workorders.schedule_workorder`. Solo lo tiene Jefe Técnica.
- El formulario de alta de orden solo ofrece como comercial a usuarios activos del grupo Comercial.
- Los usuarios creados por el formulario quedan activos, con `is_staff=False` e `is_superuser=False`, y con un solo grupo: el rol elegido. `groups.set` sustituye los grupos anteriores.

El menú lateral muestra Técnicos, Productos, Tipos de trabajo y Usuarios según el permiso de consulta. Dashboard, Órdenes y Clientes se muestran siempre; la vista igual rechaza a quien no tenga permiso. No hay entrada de Almacén en el menú: no existe un listado propio de salidas. La salida se trabaja desde la orden.

### Grupo legado «Administrador / Almacén»

La constante `LEGACY_ADMIN_WAREHOUSE_GROUP` existe. `setup_roles` no crea ese grupo, no lo borra y no mueve a sus usuarios. Las pruebas fijan ese comportamiento.

El formulario de usuarios solo permite los cinco roles actuales. No se puede asignar el grupo legado. Si un usuario legado se edita y se guarda, queda únicamente con el rol nuevo elegido.

Mientras nadie lo edite, el grupo y sus permisos previos permanecen. Esos permisos no los repara `setup_roles`.

---

## 7. Flujo completo de una Orden de Trabajo

La programación, la salida, las devoluciones y la conciliación son pasos operativos. No son estados. Los estados son cinco.

```
Recibida
    → Pendiente por pedido con proveedor
    → Equipos completos para instalación
        → programación técnica (sigue en el mismo estado)
        → salida de almacén (sigue en el mismo estado)
        → inicio de instalación
    → En instalación
        → registro de devoluciones
        → conciliación
        → Completada
```

Desde Recibida se puede pasar a Pendiente por pedido con proveedor o directamente a Equipos completos para instalación. Desde Pendiente por pedido con proveedor solo se puede pasar a Equipos completos para instalación. No hay transiciones hacia atrás. En instalación y Completada no se cambian con el formulario de estado: el inicio y el cierre tienen acciones propias.

Quién actúa en la interfaz actual:

| Paso | Quién ve la acción |
| --- | --- |
| Registrar la orden y sus equipos | Administrador, Almacén |
| Cambiar el estado de equipos | Administrador, Almacén |
| Programar o reprogramar | Jefe Técnica, y solo si el estado es Equipos completos para instalación |
| Crear la salida | Administrador, Almacén. El botón aparece con estado Equipos completos, técnico, fecha programada y sin salida previa |
| Iniciar instalación | Administrador, Almacén |
| Registrar devoluciones y conciliar | Administrador, Almacén, con la orden En instalación y la salida aún no conciliada |
| Completar | Administrador, Almacén, con la salida ya conciliada |

Comercial y Gerencia consultan. Comercial, solo sus órdenes.

### Validaciones de programación

`schedule_work_order` exige:

- estado Equipos completos para instalación;
- técnico seleccionado y activo;
- fecha programada;
- que haya un cambio real de técnico o de fecha.

La primera programación (sin técnico y sin fecha previos) registra el evento Programación. Si ya hay fecha y la fecha cambia, el motivo es obligatorio y el evento es Reprogramación. Si solo cambia el técnico y la fecha se mantiene, el motivo no es obligatorio y el evento es Cambio de técnico. El formulario solo muestra el motivo cuando la orden ya tiene fecha programada.

Programar no cambia el estado.

### Validaciones de inicio

`start_installation` exige estado Equipos completos para instalación, técnico asignado, fecha programada y una salida ya registrada. Entonces pasa a En instalación y guarda `installation_started_at`.

### Validaciones de cierre

`complete_work_order` exige estado En instalación, una salida existente y `reconciled_at` con valor. Entonces pasa a Completada y guarda `completed_at`.

### Historial

Cada alta, cambio de estado, programación, reprogramación, cambio de técnico, inicio y cierre escribe `WorkOrderHistory` con el usuario que ejecutó la acción. La conciliación no escribe un evento en ese historial: queda en `reconciled_at` y `reconciled_by` de la salida.

El sistema conserva una sola fecha programada, un solo inicio y un solo cierre. Una reprogramación sustituye la fecha y deja constancia. No hay entidad de visita.

### Etiquetas visibles

Dashboard, listados, detalle, historial y selector de estado usan las mismas etiquetas del modelo:

- Recibida
- Pendiente por pedido con proveedor
- Equipos completos para instalación
- En instalación
- Completada

Los valores guardados siguen siendo los códigos internos (`RECEIVED`, `PENDING_EQUIPMENT`, `EQUIPMENT_OK`, `IN_INSTALLATION`, `COMPLETED`). El historial reescribe esos códigos a las etiquetas anteriores al mostrarlos. No se reescriben los registros históricos.

---

## 8. Gestión de almacén

No hay inventario. SGOT registra la salida asociada a la orden, no el saldo del producto.

### Creación

`create_warehouse_output` exige:

- orden en Equipos completos para instalación;
- técnico asignado en la orden;
- que el técnico de la salida sea ese mismo técnico y esté activo;
- que la orden no tenga ya una salida.

El número y la fecha de salida se capturan en el formulario. La vista usa el técnico ya asignado a la orden; no deja elegir otro.

El servicio no exige fecha programada. La pantalla solo muestra el botón «Crear salida de almacén» cuando esa fecha ya existe (`show_create_warehouse_output_primary`).

### Ítems

Cada línea es un ítem de la orden o un producto adicional, no ambos. El mismo ítem de la orden no puede repetirse en la salida. Un adicional no lleva `work_order_item` y en la orden se muestra como «Adicional». La cantidad entregada debe ser mayor que cero. En el formulario es un entero mínimo 1.

Puede registrarse material que no estaba en la orden. La cantidad solicitada original del ítem no se modifica. Las líneas solo se cargan al crear la salida: no hay pantalla para agregar ítems ni para corregir la cantidad entregada después. A partir de ahí, el cambio permitido es la cantidad devuelta, y solo antes de conciliar.

### Devoluciones, uso y conciliación

Las devoluciones solo se registran con la orden En instalación y la salida sin conciliar. La cantidad devuelta no puede ser negativa ni mayor que la entregada. En el formulario es un entero mínimo 0.

Cantidad utilizada = entregada − devuelta. Se calcula al mostrar; no se edita.

Conciliar exige orden En instalación y salida todavía no conciliada. Guarda fecha y usuario. Después no se pueden cambiar las devoluciones. El texto de ayuda de la pantalla lo dice: al conciliar, las cantidades devueltas quedan cerradas. No hay confirmación adicional ni reversa.

La salida, sus cantidades y su estado de conciliación se ven en el detalle de la orden para quien pueda abrir esa orden. Crear, devolver y conciliar siguen exigiendo los permisos de almacén.

---

## 9. Gestión de usuarios

Solo Administrador tiene `view_user`, `add_user` y `change_user`.

- **Crear.** Username, nombre, apellido, correo opcional, rol y contraseña inicial con confirmación. El correo vacío se guarda como nulo y, si viene, se normaliza a minúsculas. El usuario nace activo, sin acceso a Django Admin.
- **Rol.** Uno de los cinco grupos. Al guardar se reemplazan los grupos del usuario.
- **Editar.** Los mismos datos, incluido el username. El texto de ayuda advierte que cambiar el username cambia el identificador de inicio de sesión. En edición el username se pasa a minúsculas y solo admite letras, números, punto, guion y guion bajo, sin espacios. En el alta, el username usa el validador estándar de Django y no se fuerza ese formato ni las minúsculas.
- **Activar o desactivar.** Invierte `is_active`. Un usuario no puede desactivar su propia cuenta. Un inactivo no inicia sesión. No se borra: las órdenes y el historial lo referencian con `PROTECT`.
- **Contraseña inicial.** La define el administrador al crear la cuenta. No hay envío por correo.
- **Restablecer.** El administrador escribe una contraseña nueva y su confirmación. No es un enlace de recuperación. Si el administrador cambia su propia contraseña, la sesión actual se mantiene (`update_session_auth_hash`).
- **Restricciones.** No puede quitarse su propio rol de Administrador. Nadie de estos roles puede eliminar usuarios. Las contraseñas usan los validadores por defecto de Django: longitud mínima de 8, que no sea demasiado parecida a los datos del usuario, que no sea una contraseña común y que no sea solo numérica. El formulario no asigna `is_staff` ni `is_superuser`.

El primer acceso al sistema vacío no sale de esta pantalla. Hace falta un superusuario creado con el comando de Django (sección 13) o un usuario cargado por administración. Un superusuario tiene todos los permisos aunque no pertenezca a un grupo. Conviene crear después los usuarios de operación con su rol y reservar el superusuario para administración técnica.

---

## 10. Validaciones de negocio importantes

Reglas presentes en modelos, formularios o servicios:

**Orden**

- El número de orden es único.
- El estado inicial es Recibida.
- Transiciones permitidas solo las de la sección 7. El estado nuevo debe ser distinto del actual.
- La cantidad solicitada de cada ítem es mayor que cero.
- Al crear, el comercial debe ser un usuario activo del grupo Comercial.
- Los productos ofrecidos en el alta son los activos.
- No existe vista operativa para editar o anular una orden ya guardada.

**Programación, inicio y cierre**

- Solo se programa en Equipos completos para instalación, con técnico activo y fecha.
- Sin cambio de técnico ni de fecha, la programación se rechaza.
- Cambiar una fecha ya programada exige motivo.
- No se inicia sin técnico, fecha y salida.
- No se completa fuera de En instalación, ni sin salida, ni con la salida sin conciliar.

**Almacén**

- Como máximo una salida por orden (`OneToOne` y validación del servicio).
- La salida solo se crea en Equipos completos para instalación, con el técnico asignado y activo.
- Cada línea es ítem de la orden o adicional, no los dos, y el ítem no se repite.
- El ítem debe pertenecer a la misma orden. Si se informan ítem y producto, deben coincidir; en el formulario la interfaz pide uno u otro.
- Entregada mayor que cero. Devuelta entre cero y la entregada, solo En instalación y antes de conciliar.
- No se concilia dos veces ni fuera de En instalación.

**Catálogo y clientes**

- Código de producto único, con tres segmentos numéricos y categoría coherente con el prefijo. `1-5-*` es Material.
- Nombre de tipo de trabajo único.
- Código de cliente único si se informa. Sistema Centurión o Arion, opcional. El formulario no obliga a informar los dos juntos.
- Productos, técnicos y tipos de trabajo se activan o desactivan; no hay borrado en la interfaz. Un técnico inactivo no se programa ni recibe una salida nueva. Un producto inactivo no sale en los formularios de alta.

**Usuarios**

- Correo único si se informa.
- Un administrador no se desactiva a sí mismo ni se quita el rol Administrador.
- Sin permiso de borrado de usuarios.

---

## 11. Historial y trazabilidad

`WorkOrderHistory` guarda:

| Campo | Uso |
| --- | --- |
| `event_type` | Tipo de evento |
| `user` | Quién lo hizo |
| `created_at` | Fecha y hora |
| `previous_value` | Valor anterior, texto |
| `new_value` | Valor nuevo, texto |
| `description` | Texto del evento |

Tipos definidos:

| Código | Etiqueta |
| --- | --- |
| `CREATED` | Creación |
| `UPDATED` | Actualización |
| `STATUS_CHANGED` | Cambio de estado |
| `SCHEDULED` | Programación |
| `RESCHEDULED` | Reprogramación |
| `TECHNICIAN_CHANGED` | Cambio de técnico |
| `INSTALLATION_STARTED` | Inicio de instalación |
| `COMPLETED` | Finalización |

Los servicios actuales escriben todos esos tipos excepto `UPDATED`. Ese valor existe en el modelo y en el admin; ninguna operación de `services.py` lo genera.

En programación y reprogramación, el valor compuesto se guarda como `fecha | técnico`. El motivo de reprogramación va en la descripción (`Motivo: ...`), no en una columna propia. La pantalla reescribe fechas y estados a español y muestra motivo, valor anterior y valor nuevo.

El permiso `view_workorderhistory` está en Administrador, Almacén y Gerencia. El detalle de la orden no consulta ese permiso: muestra el historial a quien pueda abrir la orden, incluidos Comercial y Jefe Técnica.

La conciliación no es un evento de este historial.

En Django Admin el historial es de solo lectura.

---

## 12. Configuración

`django-environ` lee el archivo `.env` en la raíz. Plantilla: `.env.example`. No se documentan aquí valores reales. El archivo `.env` no debe versionarse.

| Variable | Uso |
| --- | --- |
| `DJANGO_SECRET_KEY` | `SECRET_KEY`. Obligatoria. Usar `<SECRET_KEY>`. |
| `DJANGO_DEBUG` | `DEBUG`. En el código el valor por defecto es `False` si la variable falta. `.env.example` trae `True` para desarrollo. |
| `DJANGO_ALLOWED_HOSTS` | Lista separada por comas. Por defecto `localhost,127.0.0.1`. |
| `POSTGRES_DB` | Nombre de la base. El ejemplo usa `sgot`. |
| `POSTGRES_USER` | Usuario. El ejemplo usa `sgot_user`. |
| `POSTGRES_PASSWORD` | Contraseña. Usar `<DB_PASSWORD>`. |
| `POSTGRES_HOST` | Host. `localhost` si Django corre en la máquina. Compose fija `db` para el servicio `web`. |
| `POSTGRES_PORT` | Puerto. Por defecto `5432`. |

Otros ajustes de `config/settings.py`:

- `LANGUAGE_CODE = "es"`.
- `TIME_ZONE = "America/Bogota"` y `USE_TZ = True`. Las fechas conscientes se almacenan en UTC y se muestran en hora de Colombia.
- `STATIC_URL = "static/"` y `STATICFILES_DIRS` apunta a `static/`. No hay `STATIC_ROOT` ni `MEDIA_ROOT`.
- `AUTH_USER_MODEL = "accounts.User"`.
- `LOGIN_URL = "/login/"`.
- `LOGIN_REDIRECT_URL = "workorders:dashboard"`.
- `LOGOUT_REDIRECT_URL = "/login/"`.
- Validadores de contraseña por defecto de Django.
- `DEFAULT_AUTO_FIELD = BigAutoField`.

No hay configuración de correo, logging, HTTPS, CSRF de dominio público ni cabeceras de proxy.

---

## 13. Instalación local

No hay URL de clonación en el repositorio. Partir de la copia entregada.

Requisitos: Python 3.12 y Docker si se usa el Compose incluido. PostgreSQL 16 es la versión de la imagen `postgres:16-alpine`.

### Entorno y dependencias

```bash
python -m venv .venv
```

Activar:

- Windows PowerShell: `.venv\Scripts\Activate.ps1`
- Linux o macOS: `source .venv/bin/activate`

```bash
pip install -r requirements.txt
```

Copiar `.env.example` a `.env` y completar `<SECRET_KEY>`, `<DB_PASSWORD>` y el resto. Para Django en la máquina, `POSTGRES_HOST=localhost` y `DJANGO_DEBUG=True`.

### Base de datos

Opción A. Solo PostgreSQL en Docker y la aplicación en el entorno virtual:

```bash
docker compose up -d db
python manage.py migrate
python manage.py setup_roles
python manage.py createsuperuser
python manage.py runserver
```

Opción B. Aplicación y base como las define Compose. El servicio `web` ejecuta `runserver` y no migra solo. `POSTGRES_HOST` del contenedor queda en `db`.

```bash
docker compose up --build -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py setup_roles
docker compose exec web python manage.py createsuperuser
```

La aplicación queda en el puerto 8000. El inicio de sesión es `/login/`. La raíz redirige al dashboard si hay sesión.

`createsuperuser` hace falta porque ningún comando crea el primer usuario. `setup_roles` solo crea grupos. Después, desde Usuarios, crear las cuentas de cada rol. El superusuario no sustituye al rol Administrador: tiene todos los permisos y puede entrar a `/admin/`.

`depends_on` arranca el contenedor de Postgres, no espera a que acepte conexiones. Si `migrate` falla al primer intento, repetirlo cuando la base esté lista.

---

## 14. Tests

El proyecto usa el runner de Django. No hay `pytest.ini` ni `pyproject.toml`.

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Para conocer el número de pruebas de una ejecución:

```bash
python manage.py test -v 1
```

La última línea del runner indica cuántas se ejecutaron. Ese número cambia si se agregan o quitan pruebas; no se fija en este documento.

Cobertura por área, según los módulos de prueba existentes:

| Área | Qué ejercitan las pruebas |
| --- | --- |
| `apps/accounts/tests.py` | `setup_roles`, matriz de permisos, grupo legado, listado, alta, edición, activación y contraseñas |
| `apps/customers/tests/` | modelo, listado, detalle y formularios |
| `apps/catalog/tests/` | modelo y pantallas de productos, técnicos y tipos de trabajo, incluida la activación |
| `apps/workorders/tests/` | modelo, servicios, alta, listado, detalle, dashboard, programación, inicio y cierre |
| `apps/warehouse/tests/` | modelo, servicios, formularios, alta de salida, devoluciones y conciliación |

No hay informe de cobertura configurado en el repositorio. `.gitignore` prevé `.coverage` y `htmlcov/`, pero no hay dependencia ni comando de coverage en `requirements.txt`.

---

## 15. Preparación para producción

### Implementado

- `DEBUG` puede apagarse con `DJANGO_DEBUG`.
- `ALLOWED_HOSTS` sale de la variable de entorno.
- `SECRET_KEY` no está escrita en `settings.py`.
- PostgreSQL es el motor configurado.
- Hay `Dockerfile` y `docker-compose.yml` para desarrollo: imagen slim, código montado en `/app`, `runserver` y un volumen `postgres_data`.
- Existen `wsgi.py` y `asgi.py`.
- Contraseñas con los validadores de Django y protección CSRF de los formularios.
- Usuarios de la interfaz operativa sin `is_staff`.

### En preparación para despliegue

El Compose actual no es un despliegue de producción: usa `runserver`, publica el puerto 5432, no define healthcheck, no recoge estáticos y no termina TLS.

### Recomendaciones de despliegue

Esta lista no está implementada en el repositorio. Son medidas a preparar en la infraestructura:

- `DJANGO_DEBUG=False`.
- `DJANGO_ALLOWED_HOSTS` con el dominio real.
- HTTPS terminado en un proxy inverso, con redirección desde HTTP.
- Servir la aplicación con un servidor WSGI y no con `runserver`.
- Definir `STATIC_ROOT`, ejecutar `collectstatic` y servir `/static/` desde el proxy o el servidor web.
- No publicar PostgreSQL a internet. Dejar el puerto 5432 solo en la red interna.
- Copias de seguridad de la base y prueba de restauración.
- Logging fuera del contenedor y rotación.
- Confirmar que el servidor y el contenedor tienen zona horaria coherente. La aplicación ya usa `America/Bogota` con `USE_TZ = True`.
- Firewall que solo exponga 443 (y 80 si redirige a HTTPS).
- Secreto y contraseña de base distintos de cualquier valor de desarrollo.
- Una cuenta superusuario de emergencia, separada de los usuarios diarios, y el alta de un Administrador de operación.

---

## 16. Backups y recuperación

**No hay respaldos implementados** en la aplicación ni en Compose. No hay tarea programada, volcado ni runbook.

Estrategia recomendada, todavía por implantar:

- Volcado lógico periódico de PostgreSQL (`pg_dump`) del volumen `postgres_data`, o el mecanismo equivalente del proveedor.
- Copia del volcado fuera del mismo servidor.
- Retención acordada con la empresa (diaria y una copia semanal o mensual).
- Un ensayo de restauración en una base vacía antes de dar por bueno el procedimiento.
- El código puede recuperarse desde el repositorio Git. Los datos de operación solo viven en PostgreSQL.
- `.env` debe custodiarse aparte: no está en Git y sin él no arranca la configuración.

Restaurar es volver a crear la base, cargar el volcado, colocar el `.env` de producción y levantar la misma versión de código con la que se generó ese volcado. No hay comando propio de recuperación.

---

## 17. Mantenimiento y futuras versiones

### V1, ya en el código

Usuarios y roles, clientes, técnicos, productos, tipos de trabajo, órdenes e ítems, cinco estados, programación con motivo de reprogramación, una salida por orden, adicionales, devoluciones, conciliación, historial, dashboard y filtros.

### Mantenimiento previsto al recibir el sistema

- Ejecutar `migrate` cuando lleguen migraciones nuevas.
- Volver a ejecutar `setup_roles` si cambia la matriz; el comando reescribe los permisos de los cinco grupos y no toca el grupo legado.
- Crear y desactivar usuarios desde la pantalla Usuarios.
- No borrar clientes, productos, técnicos ni órdenes que ya tengan historia: las claves usan `PROTECT` precisamente para impedirlo cuando hay referencias.
- Preferir la interfaz operativa a Django Admin.

### Propuesto para futuras versiones

No hay roadmap en el repositorio. Lo siguiente es propuesta, no alcance aprobado:

- Paginación de listados. Hoy no hay paginador.
- Indicadores de gerencia adicionales al dashboard actual.
- Endurecer el permiso de historial y de consulta de salida para que coincida con lo que la pantalla ya muestra.
- Numeración asistida de órdenes y salidas, si la empresa deja de usar el número del documento físico.
- Procedimiento de producción (servidor WSGI, estáticos, HTTPS y respaldos) como trabajo de despliegue, no como función de negocio.

No están propuestas aquí, y no deben asumirse, las exclusiones ya dichas: SIIGO, inventario, proveedores, facturación, acceso de técnicos y aplicación móvil.
