# Memoria Técnica
## Módulo Odoo: ColorTech Órdenes de Trabajo

**Módulo:** colortech_workorders  
**Empresa:** ColorTech Guadalajara S.L.  
**Curso:** 2.º DAM  
**Fecha:** Febrero 2026  

---

## 1. Descripción de la empresa

ColorTech Guadalajara es un taller que se dedica a personalizar dispositivos electrónicos. Básicamente lo que hacen es pintar, lacar y personalizar móviles, consolas, portátiles, tablets y auriculares. Tienen clientes particulares que quieren darle un aspecto único a su PS5 o a su iPhone, y también trabajan con tiendas de segunda mano que les mandan dispositivos para dejarlos como nuevos antes de venderlos.

Es un negocio bastante concreto y especializado, no es solo "reparación" sino que están enfocados en la parte estética. Tienen técnicos especializados en pintura y lacado, no en electrónica.

**Necesidades detectadas**

El problema que vi cuando analicé cómo trabajaban es que todo lo llevaban a mano. Literalmente tenían un cuaderno con las órdenes, un Excel para los precios y un grupo de WhatsApp donde los técnicos comentaban en qué estaban. Era bastante caótico.

Los problemas concretos eran que no sabían de un vistazo qué órdenes estaban esperando, cuáles en proceso y cuáles listas para entregar. Cuando llamaba un cliente a preguntar por su consola, tenían que ponerse a buscar en el cuaderno. Tampoco controlaban bien los tiempos, o sea sabían que un lacado completo tardaba "unas pocas horas" pero no tenían datos reales. Y los costes los calculaban a ojo más o menos.

**Por qué Odoo**

La empresa ya usa Odoo para facturación así que no era plan de hacerles una aplicación aparte desde cero. Lo más lógico era extender lo que ya tienen con un módulo personalizado para el taller. Así queda todo integrado en el mismo sistema y no tienen que andar pasando datos de un sitio a otro.

---

## 2. Diseño del módulo

### Los modelos

El módulo tiene 4 modelos. Tardé un poco en decidir cómo estructurarlo porque al principio pensé en hacerlo todo en uno, pero luego vi que separar el catálogo de servicios de las órdenes tiene mucho más sentido.

Los modelos son:

- **colortech.device.type**  los tipos de dispositivo (móvil, consola, portátil...)
- **colortech.service**  el catálogo de servicios con precios y tiempos
- **colortech.workorder**  la orden de trabajo en sí
- **colortech.workorder.line**  cada servicio concreto que se hace dentro de una orden

La relación entre ellos es así: una orden tiene un tipo de dispositivo (Many2one), y dentro de esa orden hay varias líneas (One2many), donde cada línea apunta a un servicio del catálogo (Many2one). Es el mismo patrón que usan las facturas de Odoo, con cabecera y líneas.

### colortech.device.type

Este es el más sencillo. Solo guarda el nombre del tipo de dispositivo, un código único y una descripción. El campo `active` sirve para poder archivar tipos que ya no usen sin borrarlos del historial. Tiene una restricción SQL para que no se puedan meter dos tipos con el mismo código.

### colortech.service

El catálogo de servicios. Cada servicio tiene nombre, código, tipo (pintura, personalización, restauración, protección u otro), precio base y tiempo estimado en horas.

Separar esto en su propio modelo fue buena idea porque cuando cambian los precios no hay que tocar todas las órdenes, solo el servicio. Y al crear una línea de orden, el precio se copia automáticamente desde aquí pero se puede cambiar para casos especiales.

Tiene una validación para que el precio no pueda ser negativo, que parece una tontería pero es mejor tenerla.

### colortech.workorder

Este es el modelo principal. Guarda toda la información de una orden: datos del cliente (nombre, teléfono, email), datos del dispositivo (tipo, marca, modelo, número de serie, estado en el que llegó), el técnico asignado, la prioridad, las fechas y el estado actual.

El estado es lo más importante del modelo. El flujo es:

Recibido  En Proceso  En Secado  Control de Calidad  Terminado  Entregado

También existe el estado Cancelado al que se puede ir desde casi cualquier punto.

El campo `name` es el número de orden, que se genera automáticamente (OT-0001, OT-0002...) usando una secuencia de Odoo. Se guarda como solo lectura una vez creado.

Hereda de `mail.thread` y `mail.activity.mixin` para tener el chatter, que es el sistema de comentarios y registro de cambios que tienen todos los documentos de Odoo. Así queda registrado quién cambió el estado y cuándo.

Los campos `total_cost`, `total_hours` y `service_count` son calculados automáticamente a partir de las líneas.

### colortech.workorder.line

Cada línea es un servicio dentro de una orden. Tiene el servicio, una descripción que se rellena sola al elegir el servicio, cantidad, precio unitario y el subtotal que se calcula solo. También guarda las horas estimadas para ese servicio concreto.

---

## 3. Desarrollo

### Estructura de carpetas

```
colortech_workorders/
 __init__.py
 __manifest__.py
 data/
    colortech_demo_data.xml
 models/
    __init__.py
    colortech_device_type.py
    colortech_service.py
    colortech_workorder.py
 security/
    ir.model.access.csv
 static/
    description/
        index.html
 views/
     colortech_device_type_views.xml
     colortech_menus.xml
     colortech_service_views.xml
     colortech_workorder_views.xml
```

### Código relevante

**La secuencia automática**

```python
@api.model_create_multi
def create(self, vals_list):
    for vals in vals_list:
        if vals.get('name', 'Nuevo') == 'Nuevo':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'colortech.workorder') or 'Nuevo'
    return super().create(vals_list)
```

Esto sobreescribe el método `create` base. Cuando se crea una orden nueva, si el nombre sigue siendo "Nuevo" (el valor por defecto), lo reemplaza por el siguiente número de la secuencia. La secuencia está definida en el XML con prefijo `OT-` y 4 dígitos. Al final queda algo como OT-0001.

---

**Los botones de estado**

```python
def action_en_proceso(self):
    for rec in self:
        if not rec.line_ids:
            raise ValidationError(
                'Añade al menos un servicio antes de iniciar.')
        rec.state = 'en_proceso'
```

Cada botón del cabecero llama a uno de estos métodos. El primero tiene una validación extra: si intentas iniciar el trabajo sin haber metido ningún servicio, lanza un error. El resto son más directos. El de entregar también guarda la fecha de entrega real automáticamente.

---

**Los campos calculados**

```python
@api.depends('line_ids.subtotal', 'line_ids.estimated_hours')
def _compute_totals(self):
    for rec in self:
        rec.total_cost = sum(rec.line_ids.mapped('subtotal'))
        rec.total_hours = sum(rec.line_ids.mapped('estimated_hours'))
        rec.service_count = len(rec.line_ids)
```

Con `@api.depends` le dices a Odoo qué campos tiene que vigilar. Cada vez que cambia el subtotal o las horas de alguna línea, se recalculan los totales. El `store=True` en los campos hace que se guarden en base de datos, lo que permite filtrar y ordenar por ellos, cosa que no puedes hacer con campos calculados sin almacenar.

---

**El onchange que rellena precio y horas**

```python
@api.onchange('service_id')
def _onchange_service_id(self):
    if self.service_id:
        self.unit_price = self.service_id.default_price
        self.estimated_hours = self.service_id.estimated_hours
        if not self.description:
            self.description = self.service_id.name
```

Cuando eliges un servicio en una línea, este método copia el precio y las horas del catálogo. Si la descripción está vacía también la rellena con el nombre del servicio. El técnico puede cambiar los valores después si ese trabajo concreto lo requiere.

---

**Colores de estado en la lista**

```xml
<field name="state" widget="badge"
       decoration-success="state == 'entregado'"
       decoration-info="state == 'recibido'"
       decoration-warning="state == 'secado'"
       decoration-danger="state == 'cancelado'"/>
```

El widget `badge` muestra el estado con un chip de color. Verde para entregado, azul para recibido, amarillo para en secado y rojo para cancelado. De un vistazo en la lista ya sabes cómo está cada orden sin tener que abrirla.

---

**Permisos**

En `ir.model.access.csv` hay dos niveles: usuarios normales y administradores. Los usuarios pueden leer, crear y editar, pero no borrar (`perm_unlink = 0`). Solo los administradores eliminan registros. Así no desaparecen órdenes por accidente.

### Vistas

Se han implementado las siguientes vistas:

- Lista de órdenes con badges de color según el estado
- Formulario completo con botones de flujo en el cabecero, barra de progreso de estados, pestañas para servicios, observaciones del dispositivo y notas internas
- Lista y formulario de servicios, con búsqueda y agrupación por tipo
- Lista y formulario de tipos de dispositivo
- Menú principal con dos secciones: Órdenes de Trabajo y Configuración

---

## 4. Git

**Repositorio:** `https://github.com/[usuario]/colortech-workorders`

Usé Git desde el principio para controlar los cambios. Trabajé en la rama `main` porque lo hice solo y no necesité ramas paralelas. Fui haciendo commits cada vez que terminaba una parte que funcionaba, sin acumular demasiados cambios juntos.

Commits principales:

```
feat: estructura inicial del módulo y manifest
feat: modelo device_type con restricción de código único
feat: modelo service con validación de precio negativo
feat: modelo workorder con flujo de estados y secuencia
feat: workorder.line con onchange y subtotal computado
fix: validación de líneas vacías al iniciar la orden
feat: vistas XML con badges y barra de estado
feat: menús y permisos CSV
feat: datos de demo con tipos y servicios reales
```

---

## 5. Pruebas

**Instalación**

Copiar la carpeta en el directorio de addons de Odoo, activar el modo desarrollador desde Ajustes, actualizar la lista de aplicaciones y buscar "ColorTech". Al instalar ya carga los datos de demo: 5 tipos de dispositivo y varios servicios con sus precios.

**Pruebas realizadas**

Primero comprobé que los datos de demo se cargaban bien y aparecían en sus menús correspondientes.

Luego creé una orden desde cero. El número se generó automáticamente (OT-0001). Intenté pulsar "Iniciar Trabajo" sin añadir servicios y saltó el error de validación. Añadí un servicio, el precio y las horas se rellenaron solos, y fui avanzando por todos los estados hasta llegar a "Entregado". La fecha de entrega apareció automáticamente.

También probé los filtros: filtrar por estado "En Proceso" y agrupar por técnico funcionó bien. Los totales de la orden se actualizan en tiempo real al cambiar cantidades o precios en las líneas.

Lo único que tuve que corregir durante las pruebas fue un problema con la secuencia: el código en Python y en el XML no coincidían y la numeración no funcionaba. Una vez igualados fue todo bien.

---

## 6. Conclusiones

**Qué aprendí**

Antes de este proyecto sabía Python pero no había tocado Odoo. Lo que más me costó al principio fue el sistema de decoradores: `@api.depends`, `@api.onchange` y `@api.constrains` parecen similares pero funcionan en momentos distintos y no son intercambiables. Una vez que lo entendí fue bastante más fácil avanzar.

También aprendí que merece la pena dedicar tiempo al diseño del modelo de datos antes de ponerse a programar. Las primeras horas las invertí en pensar qué modelos necesitaba y cómo se relacionaban, y eso me ahorró muchos problemas después porque no tuve que rehacer estructuras.

**Dificultades**

El problema más frecuente fue que Odoo a veces no aplicaba los cambios en las vistas sin reiniciar el servidor o limpiar la caché. Al principio perdí bastante tiempo con eso sin entender por qué mis cambios no se veían.

Lo de la secuencia automática también me dio problemas porque la documentación no dejaba claro que el código en el XML y en el método `create` tienen que ser exactamente el mismo string.

En general, trabajar con un framework tan grande sin conocerlo de antes es bastante abrumador. Hay cosas que no sabes que existen hasta que te encuentras con un problema concreto.

**Qué mejoraría**

Lo más importante que me quedó pendiente es vincular el cliente con el modelo `res.partner` de Odoo en lugar de guardarlo como texto. Ahora mismo si el mismo cliente trae varios dispositivos en distintos momentos no hay forma de ver su historial fácilmente.

También añadiría generación de PDF para el albarán de recepción y para el resumen final al entregar el dispositivo.

Y a más largo plazo, un dashboard con estadísticas del taller le daría mucho valor: órdenes del mes, ingresos, tiempo medio por tipo de servicio, carga de trabajo por técnico. Eso sería lo que convertiría el módulo en algo realmente útil para que los responsables puedan tomar decisiones.

---

*ColorTech Guadalajara  DAM 2026*
