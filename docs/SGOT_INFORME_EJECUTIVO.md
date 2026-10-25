# Informe Ejecutivo — Sistema SGOT

Documento de presentación de la versión 1 para la propietaria y la gerencia.

Estado:

- **IMPLEMENTADO:** el sistema descrito en las secciones 3 a 6.
- **EN PREPARACIÓN PARA DESPLIEGUE:** la versión 1 está desarrollada. Falta instalarla en el servidor de la empresa, con acceso seguro y copias de la información.
- **PROPUESTO PARA FUTURAS VERSIONES:** lo indicado en la sección 9. No tiene fecha ni aprobación de alcance.

La pantalla de ingreso identifica a la organización como Centinela de Occidente Ltda.

Octubre de 2026.

---

## 1. Resumen ejecutivo

SGOT es el sistema interno de órdenes de trabajo de la empresa. Permite registrar la orden que ya existe en papel y seguirla en un solo lugar: cliente, comercial, equipos, estado, técnico, fecha, salida de almacén, devoluciones, conciliación y cierre.

El problema que atiende es operativo. Comercial, almacén y el área técnica necesitan ver la misma orden y dejar constancia de quién avanzó cada paso. SGOT no sustituye la facturación ni el inventario contable. Los complementa.

La versión 1 está lista como aplicación. El paso siguiente es el despliegue en la infraestructura de la empresa.

---

## 2. Situación que motivó el proyecto

La operación de una orden cruza varias áreas y sigue apoyándose en documentos físicos.

Sin un registro común ocurre lo siguiente, como condición de trabajo y no como una medición:

- el estado se consulta de forma dispersa;
- no queda una traza única de quién programó, qué salió de almacén y qué se devolvió;
- comercial, almacén y jefatura técnica no miran la misma información al mismo tiempo;
- el avance (recibida, pendiente de equipos, lista para instalar, en instalación, completada) no tiene un lugar único de consulta.

Este informe no incluye cifras de pérdida, tiempos ni costos. Esas mediciones no forman parte del sistema entregado.

---

## 3. Solución desarrollada

SGOT es una plataforma web interna. El personal entra con usuario y contraseña. Según su rol, registra o solo consulta.

Cada orden conserva:

- el número del documento físico;
- el cliente y el comercial responsable;
- el tipo de trabajo y los equipos pedidos;
- el estado;
- el técnico y la fecha, cuando ya fueron programados;
- la salida de almacén, las devoluciones y la conciliación;
- el historial de los cambios importantes.

Hay un tablero inicial con el conteo por estado, las órdenes atrasadas y las próximas instalaciones.

---

## 4. Funcionalidades entregadas

Todo lo siguiente está disponible en la versión 1.

- **Usuarios y roles.** Administrador, Almacén, Comercial, Jefe Técnica y Gerencia. Cada persona ve solo lo que le corresponde. El comercial ve únicamente sus órdenes.
- **Clientes.** Consulta, búsqueda y, para administración y almacén, alta y edición. El código puede asociarse a Centurión o Arion.
- **Técnicos.** Catálogo de planta y contratistas, activos o inactivos. El técnico no entra al sistema.
- **Productos.** Código, nombre, referencia, categoría, tipo y unidad, con activación e inactivación.
- **Tipos de trabajo.** Catálogo para clasificar la orden.
- **Órdenes de trabajo.** Registro con sus equipos, consulta, búsqueda y filtros.
- **Programación.** Jefe Técnica asigna técnico y fecha, y deja motivo cuando cambia una fecha ya puesta.
- **Almacén.** Una salida por orden, con los materiales de la orden y materiales adicionales si salió algo que no estaba pedido.
- **Devoluciones.** Cantidad que regresa, con la cantidad utilizada calculada por diferencia.
- **Conciliación.** Cierre de esas cantidades antes de dar la orden por terminada.
- **Historial.** Usuario, fecha, descripción y valores anterior y nuevo de los eventos de la orden.
- **Dashboard.** Conteos por estado, programadas hoy, atrasadas y próximas.
- **Filtros y búsqueda** en órdenes, clientes, productos, técnicos, tipos de trabajo y usuarios.

Quedan fuera de esta entrega la facturación, el inventario de existencias, las compras, el ingreso de los técnicos y una aplicación para el celular.

---

## 5. Flujo operativo digitalizado

```
Registro de la OT
    → Equipos
    → Programación
    → Almacén
    → Instalación
    → Devoluciones
    → Conciliación
    → Cierre
```

En la práctica:

1. Almacén o Administración registra la orden recibida y los equipos.
2. Si falta equipo de proveedor, la dejan pendiente. Cuando está completo, la marcan lista para instalación.
3. Jefe Técnica asigna técnico y fecha.
4. Almacén registra la salida.
5. Almacén o Administración inicia la instalación.
6. Al terminar el trabajo de campo, se registran las devoluciones.
7. Almacén concilia la salida.
8. La orden se completa.

Comercial y Gerencia consultan ese recorrido. Comercial, solo en sus órdenes. No se puede saltar el cierre: sin salida conciliada, la orden no pasa a completada. Tampoco se puede iniciar la instalación sin técnico, fecha y salida.

---

## 6. Beneficios para la empresa

Beneficios derivados de lo que el sistema ya hace. No son porcentajes ni un cálculo de retorno.

- **Trazabilidad.** Queda quién creó la orden, quién cambió el estado, quién programó y quién cerró.
- **Centralización.** Cliente, orden, programación y salida se consultan en el mismo lugar.
- **Control de responsabilidades.** Cada rol tiene un papel distinto. Programar no es lo mismo que registrar la salida ni que completar.
- **Menos pérdida de información operativa.** La fecha anterior, el técnico anterior y el motivo de una reprogramación no dependen de un chat o de una nota suelta.
- **Consulta rápida.** Búsqueda por orden o cliente, filtros y un tablero de atrasos y próximas visitas.
- **Historial.** La orden completada sigue disponible, con sus cantidades entregadas, devueltas y utilizadas.
- **Base para indicadores.** El dashboard actual ya cuenta estados y cumplimiento de fechas. Indicadores de gerencia más amplios pueden construirse después, sobre estos mismos datos.

---

## 7. Seguridad y control

### Implementado

- Ingreso con usuario y contraseña.
- Cinco roles, con permisos distintos.
- El comercial no ve las órdenes de los demás.
- Una cuenta se puede desactivar sin borrar su historia. Una persona inactiva no entra.
- No hay forma, para estos roles, de eliminar usuarios.
- Un administrador no puede quitarse a sí mismo el rol ni desactivar su propia cuenta.
- Las contraseñas nuevas deben cumplir reglas mínimas de seguridad del sistema.
- Los usuarios del día a día no entran a la herramienta técnica de base de datos.

### Planeado para el despliegue

Todavía no está instalado en un servidor de producción. Forma parte de la infraestructura prevista, no del programa ya configurado:

- acceso por **HTTPS**, para que la clave viaje cifrada;
- **copias de seguridad** de la base de datos y una prueba de recuperación;
- servidor y dominio de la empresa, con la base de datos cerrada a la red interna.

Hasta que eso esté en marcha, el sistema no debe usarse con información real en un equipo expuesto a internet.

---

## 8. Estado actual

La versión 1 está **funcionalmente desarrollada** y **en preparación para despliegue**.

Incluye las pantallas de operación, las reglas del flujo, las pruebas automáticas del proyecto y esta documentación. No incluye el servidor definitivo, el dominio, el certificado de seguridad ni la rutina de respaldos. Esos puntos son trabajo de puesta en marcha, no funciones pendientes de la operación diaria.

---

## 9. Próximas etapas

### Cierre de la versión 1

- Instalación en el servidor de la empresa.
- Cuentas reales de cada rol y retiro o desactivación de cuentas de prueba.
- Acuerdos de copia de seguridad y de quién administra los usuarios.
- Acompañamiento inicial para que cada área use su parte del flujo.

### Propuesto para más adelante

Sin fecha y sin compromiso de hacerlo:

- indicadores de gerencia además del tablero actual.

No se propone, en este informe, conectar facturación, inventario o el acceso de los técnicos. Eso sería otro proyecto.

---

## 10. Reconocimiento por desarrollo

### Propuesta de reconocimiento por el desarrollo

Esta sección es una **propuesta de reconocimiento económico** por el trabajo realizado. No es una factura cerrada, no fija una deuda y no describe una obligación laboral ni contractual. El valor queda para conversación y acuerdo de las partes.

El desarrollo ha incluido, entre otros:

- levantamiento y análisis del proceso de la orden;
- definición de la estructura del sistema;
- modelado de la información (clientes, catálogo, órdenes, almacén e historial);
- programación de la lógica de negocio y de las pantallas;
- roles y permisos de las cinco áreas;
- reglas del flujo, de la programación, de la salida y de la conciliación;
- pruebas automatizadas y pruebas de uso de las pantallas;
- documentación técnica, manual de usuario y este informe;
- preparación de la base para el despliegue;
- acompañamiento previsto para la adopción.

**Valor propuesto de reconocimiento: $________________ COP**

Justificación, para completar cuando exista una cifra acordada:

- **Alcance.** Cubre el ciclo operativo de la orden, no una pantalla aislada.
- **Horas y esfuerzo.** El valor puede apoyarse en el tiempo dedicado a análisis, construcción, pruebas y documentación. La cifra de horas se completa con el registro de quien desarrolló; este informe no inventa un total.
- **Responsabilidad.** El sistema pasa a guardar la traza de la operación. Diseñarlo implica cuidar permisos, cierres y la imposibilidad de borrar la historia por descuido.
- **Valor generado.** La empresa queda con un activo usable para coordinar comercial, almacén y área técnica, y con información que antes no tenía un lugar único.
- **Continuidad.** Después del arranque hará falta mantenimiento: cuentas, copias, ajustes menores y, si se acuerda, mejoras.

Tres formas posibles de plantear el acuerdo. Se elige una; no se suman solas:

1. **Reconocimiento único por la versión 1.** Un valor por el sistema entregado, documentación incluida. El despliegue y el soporte posterior se conversan aparte.
2. **Reconocimiento más mantenimiento.** El valor de la versión 1 y, además, un periodo acotado de soporte: usuarios, correcciones y acompañamiento del arranque. El periodo y el monto se escriben al acordarlos.
3. **Reconocimiento más una bolsa de mejoras.** El valor de la versión 1 y una bolsa posterior para mejoras ya conversadas, por ejemplo indicadores. Lo que no esté en la bolsa no se asume incluido.

Cualquiera de las tres requiere un valor y unas condiciones escritas por las partes. Este documento solo deja el espacio.

---

## 11. Conclusión

SGOT ya es un activo digital interno de la empresa: el flujo de la orden de trabajo quedó registrado, con responsables, estados y constancia de almacén. Es también una base concreta para evolucionar, cuando la empresa lo decida, hacia una lectura de gestión más amplia.

El paso inmediato no es agregar funciones. Es desplegarlo con acceso seguro, cuentas reales y copias de la información, y acompañar a cada área en su parte del recorrido.
