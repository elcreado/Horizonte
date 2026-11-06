from pathlib import Path
from copy import deepcopy
from zipfile import ZipFile, ZIP_DEFLATED
from hashlib import sha256
import json, re, textwrap
from lxml import etree
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[2]
WORK=Path(__file__).resolve().parent
REF=ROOT/'Proyecto/Plantilla.docx'
OUT=ROOT/'Proyecto/Documentacion_BD_Horizonte_Adrian_Perez_Pacheco.docx'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
tables=[]
def table(name, purpose, fields, unique='', checks='', note=''):
    fs=[]
    for row in fields.strip().split('\n'):
        n,t,k,d=row.strip().split('|',3)
        fs.append(dict(name=n,type=t,key=k,desc=d))
    tables.append(dict(name=name,purpose=purpose,fields=fs,unique=unique,checks=checks,note=note))

table('empresa','Identifica cada microempresa y su umbral operativo de liquidez.', '''
id|BIGINT|PK|Identificador interno
nit|VARCHAR(30)|UQ|NIT normalizado sin separadores
nombre|VARCHAR(200)||Nombre de la microempresa
umbral|NUMERIC(18,2)||Saldo mínimo definido por el propietario
''',checks='umbral >= 0')
table('usuario','Representa al usuario autenticado sin repetir sus datos en cada empresa.', '''
id|BIGINT|PK|Identificador de auth_user
username|VARCHAR(150)|UQ|Nombre único de acceso
password_hash|VARCHAR(128)||Hash de autenticación
nombres|VARCHAR(150)||Nombres del usuario
apellidos|VARCHAR(150)||Apellidos del usuario
email|VARCHAR(254)||Correo de recuperación
activo|BOOLEAN||Habilitación de la cuenta
superusuario|BOOLEAN||Administración global
fecha_registro|TIMESTAMPTZ||Fecha de alta
ultimo_acceso|TIMESTAMPTZ|NULL|Último acceso exitoso
''',note='Proyección funcional de auth_user. Django administra permisos, grupos, sesiones y migraciones como infraestructura, fuera del modelo financiero.')
table('rol','Catálogo de responsabilidades dentro de una empresa.', '''
codigo|VARCHAR(16)|PK|owner accountant o viewer
nombre|VARCHAR(40)|UQ|Propietario Contador o Consulta
''')
table('membresia','Resuelve la relación muchos a muchos entre usuarios y empresas.', '''
empresa_id|BIGINT|PK FK empresa|Empresa autorizada
usuario_id|BIGINT|PK FK usuario|Usuario miembro
rol_codigo|VARCHAR(16)|FK rol|Rol en esa empresa
''')
table('proveedor','Catálogo de adaptadores bancarios identificados por un código estable.', '''
codigo|VARCHAR(40)|PK|Código del adaptador
nombre|VARCHAR(100)|UQ|Nombre del proveedor
''')
table('consentimiento','Conserva quién autorizó el acceso bancario y cuándo lo revocó.', '''
id|BIGINT|PK|Identificador de autorización
empresa_id|BIGINT|FK empresa|Empresa titular
usuario_id|BIGINT|FK usuario|Persona que autorizó
otorgado_en|TIMESTAMPTZ||Instante de autorización
revocado_en|TIMESTAMPTZ|NULL|Instante de revocación
''',checks='revocado_en IS NULL OR revocado_en >= otorgado_en')
table('alcance','Catálogo de permisos de lectura de una conexión.', '''
codigo|VARCHAR(60)|PK|Código del permiso
descripcion|VARCHAR(150)||Descripción del alcance
''')
table('consentimiento_alcance','Extrae la lista scopes a una asociación con valores atómicos.', '''
consentimiento_id|BIGINT|PK FK consentimiento|Autorización que concede el permiso
alcance_codigo|VARCHAR(60)|PK FK alcance|Permiso individual
''')
table('conexion','Enlaza una autorización con un adaptador bancario.', '''
id|BIGINT|PK|Identificador de conexión
consentimiento_id|BIGINT|UQ FK consentimiento|Consentimiento exclusivo
proveedor_codigo|VARCHAR(40)|FK proveedor|Adaptador utilizado
estado|VARCHAR(12)||active o revoked
creada_en|TIMESTAMPTZ||Creación de la conexión
revocada_en|TIMESTAMPTZ|NULL|Momento de revocación
''',checks="estado IN ('active','revoked')",note='La empresa se obtiene por consentimiento; no se repite. La exclusividad de una conexión activa por empresa y proveedor se valida mediante un trigger con bloqueo de la fila empresa.')
table('cuenta','Registra la cuenta bancaria y la cobertura de su historial.', '''
id|BIGINT|PK|Identificador de cuenta
empresa_id|BIGINT|FK empresa|Titular empresarial
nombre|VARCHAR(120)||Nombre de la cuenta
conexion_id|BIGINT|NULL UQ FK conexion|Conexión opcional de una cuenta
historial_desde|DATE|NULL|Primer día confirmado de cobertura
historial_hasta|DATE|NULL|Último día confirmado de cobertura
confirmado_en|TIMESTAMPTZ|NULL|Fecha de validación del historial
confirmado_por|BIGINT|NULL FK usuario|Usuario que confirmó
''',checks='historial_desde IS NULL OR historial_hasta IS NULL OR historial_desde <= historial_hasta',note='Todas las cuentas operan en COP. La coincidencia entre la empresa de la cuenta y la del consentimiento se comprueba al asociar una conexión.')
table('corte_cuenta','Conserva saldos observados por cuenta y fecha sin confundirlos con sumas de movimientos.', '''
cuenta_id|BIGINT|PK FK cuenta|Cuenta observada
fecha|DATE|PK|Fecha del corte
saldo|NUMERIC(18,2)||Saldo informado en COP
''',note='Sustituye balance y balance_date. El saldo vigente es el corte de fecha máxima; un saldo negativo puede representar sobregiro.')
table('tercero','Identifica comercios normalizados en el contexto de una empresa.', '''
id|BIGINT|PK|Identificador del comercio
empresa_id|BIGINT|FK empresa|Empresa que reconoce al tercero
nombre_normalizado|VARCHAR(250)||Nombre canónico para comparación
nombre_visible|VARCHAR(250)||Nombre de presentación
''',unique='empresa_id,nombre_normalizado')
table('alias_tercero','Conserva las variantes de un comercio según el proveedor.', '''
id|BIGINT|PK|Identificador del alias
tercero_id|BIGINT|FK tercero|Comercio canónico
proveedor_codigo|VARCHAR(40)|FK proveedor|Fuente del alias
alias_normalizado|VARCHAR(250)||Descripción alternativa
''',unique='tercero_id,proveedor_codigo,alias_normalizado',note='La empresa se deriva de tercero. Un trigger impide que el mismo alias del mismo proveedor apunte a terceros distintos de una misma empresa.')
table('categoria','Taxonomía compartida de categorías financieras.', '''
id|BIGINT|PK|Identificador de categoría
nombre|VARCHAR(80)|UQ|Nombre único como Software u Otros
''',note='La dirección del flujo se obtiene del signo del movimiento; una categoría no impone un signo.')
table('movimiento','Registra cada ingreso o egreso bancario con deduplicación por cuenta.', '''
id|BIGINT|PK|Identificador de movimiento
cuenta_id|BIGINT|FK cuenta|Cuenta de origen
externo_id|VARCHAR(120)||Identificador en la fuente
fecha|DATE||Fecha de negocio
importe|NUMERIC(18,2)||Valor positivo de ingreso o negativo de egreso
descripcion|VARCHAR(250)||Texto original del banco
descripcion_normalizada|TEXT||Texto procesado para clasificación
tercero_id|BIGINT|NULL FK tercero|Comercio reconocido
tercero_original|VARCHAR(250)||Nombre recibido de la fuente
categoria_id|BIGINT|FK categoria|Categoría vigente
fuente_clasificacion|VARCHAR(16)||Origen de la clasificación
''',unique='cuenta_id,externo_id',checks='importe <> 0',note='tercero_original es evidencia inmutable de la fuente y no una copia editable del nombre canónico; no depende de tercero_id.')
table('regla_clasificacion','Aprende una categoría por empresa descripción y sentido del flujo.', '''
id|BIGINT|PK|Identificador de regla
empresa_id|BIGINT|FK empresa|Empresa donde se aplica
descripcion_normalizada|VARCHAR(250)||Patrón exacto recordado
direccion|VARCHAR(3)||in o out
categoria_id|BIGINT|FK categoria|Categoría asignada
actualizada_en|TIMESTAMPTZ||Última modificación
''',unique='empresa_id,descripcion_normalizada,direccion',checks="direccion IN ('in','out')")
table('cambio_clasificacion','Conserva el historial de correcciones manuales.', '''
id|BIGINT|PK|Identificador del evento
movimiento_id|BIGINT|FK movimiento|Movimiento corregido
usuario_id|BIGINT|FK usuario|Autor de la corrección
categoria_anterior_id|BIGINT|FK categoria|Categoría antes del cambio
categoria_nueva_id|BIGINT|FK categoria|Categoría después del cambio
recordado|BOOLEAN||Indica si creó o actualizó una regla
creado_en|TIMESTAMPTZ||Instante de la corrección
''')
table('importacion_movimiento','Registra los intentos de importación CSV o XLSX.', '''
id|BIGINT|PK|Identificador del trabajo
cuenta_id|BIGINT|FK cuenta|Cuenta receptora
usuario_id|BIGINT|FK usuario|Solicitante
formato|VARCHAR(4)||csv o xlsx
checksum|CHAR(64)||Huella del archivo sin imponer unicidad
contenido|TEXT|NULL|Carga temporal eliminada al finalizar
estado|VARCHAR(12)||queued completed o failed
creados|INTEGER||Movimientos creados en este intento
duplicados|INTEGER||Filas omitidas por idempotencia
error|VARCHAR(300)|NULL|Diagnóstico sin secretos
creada_en|TIMESTAMPTZ||Fecha de solicitud
finalizada_en|TIMESTAMPTZ|NULL|Fin del procesamiento
''',checks="formato IN ('csv','xlsx') AND creados >= 0 AND duplicados >= 0",note='Los contadores son el resultado del intento, no el total actual de movimientos. El archivo es una unidad documental temporal, no una lista consultable del modelo financiero.')
table('sincronizacion','Registra cada ejecución de sincronización bancaria.', '''
id|BIGINT|PK|Identificador de ejecución
conexion_id|BIGINT|FK conexion|Conexión sincronizada
usuario_id|BIGINT|FK usuario|Solicitante
estado|VARCHAR(12)||Estado de procesamiento
creados|INTEGER||Movimientos creados en el intento
duplicados|INTEGER||Duplicados detectados
error|VARCHAR(300)|NULL|Diagnóstico resumido
creada_en|TIMESTAMPTZ||Inicio
finalizada_en|TIMESTAMPTZ|NULL|Fin
''',checks='creados >= 0 AND duplicados >= 0')
table('obligacion','Representa un cobro o pago esperado antes de su conciliación.', '''
id|BIGINT|PK|Identificador de obligación
empresa_id|BIGINT|FK empresa|Empresa responsable
referencia|VARCHAR(120)||Referencia única por empresa
contraparte_original|VARCHAR(200)||Contraparte declarada al registrar
descripcion|VARCHAR(200)||Concepto de la obligación
direccion|VARCHAR(3)||in para cobro u out para pago
vencimiento|DATE||Fecha esperada de caja
importe_base|NUMERIC(18,2)||Pendiente al registrar la obligación
cancelada|BOOLEAN||Anulación operativa
''',unique='empresa_id,referencia',checks="importe_base >= 0 AND direccion IN ('in','out')",note='El pendiente vigente se calcula restando conciliaciones activas. La contraparte es texto histórico declarado, no un maestro de proveedores.')
table('conciliacion','Asocia un abono parcial o total de un movimiento a una obligación.', '''
id|BIGINT|PK|Identificador de aplicación
obligacion_id|BIGINT|FK obligacion|Cobro o pago aplicado
movimiento_id|BIGINT|FK movimiento|Movimiento bancario real
usuario_id|BIGINT|FK usuario|Autor de la aplicación
importe|NUMERIC(18,2)||Importe positivo aplicado
solicitud_id|UUID||Identificador de reintento
creada_en|TIMESTAMPTZ||Fecha de conciliación
revertida_en|TIMESTAMPTZ|NULL|Anulación sin borrar evidencia
''',unique='obligacion_id,solicitud_id',checks='importe > 0')
table('factura','Guarda la cabecera financiera extraída del XML sin repetirla en un JSON.', '''
id|BIGINT|PK|Identificador de factura
empresa_id|BIGINT|FK empresa|Empresa que registra el documento
cufe|VARCHAR(150)||Identificador fiscal del XML
numero|VARCHAR(100)||Número declarado en el documento
emision|DATE||Fecha de emisión
vencimiento_xml|DATE|NULL|Vencimiento declarado en el XML
subtotal|NUMERIC(18,2)||Base antes de impuestos declarada
total|NUMERIC(18,2)||Total con impuestos declarado
pagadero|NUMERIC(18,2)||Importe pagadero declarado
obligacion_id|BIGINT|NULL UQ FK obligacion|Obligación confirmada o vinculada
creada_en|TIMESTAMPTZ||Registro del documento
''',unique='empresa_id,cufe',checks='subtotal >= 0 AND total >= 0 AND pagadero >= 0',note='No almacena dirección ni pendiente duplicados. El sentido se deriva del NIT empresarial y las partes del documento. Los importes son valores declarados independientes, no una igualdad aritmética asumida.')
table('parte_factura','Registra las dos partes históricas del XML como filas atómicas.', '''
factura_id|BIGINT|PK FK factura|Documento de origen
papel|VARCHAR(8)|PK|emisor o receptor
nit_declarado|VARCHAR(30)||Identificación histórica del XML
nombre_declarado|VARCHAR(200)||Razón social histórica del XML
''',checks="papel IN ('emisor','receptor')",note='Cada factura debe tener exactamente un emisor y un receptor. Un NIT no determina universalmente el nombre histórico declarado en documentos de fechas distintas.')
table('importacion_factura','Conserva intentos de lectura y validación de XML.', '''
id|BIGINT|PK|Identificador del intento
empresa_id|BIGINT|FK empresa|Empresa solicitante
usuario_id|BIGINT|FK usuario|Autor de la carga
contenido|TEXT|NULL|XML temporal purgado al finalizar
estado|VARCHAR(12)||Estado del procesamiento
factura_id|BIGINT|NULL FK factura|Documento identificado si terminó
duplicada|BOOLEAN||Resultado de deduplicación del intento
error|VARCHAR(300)|NULL|Diagnóstico de validación
creada_en|TIMESTAMPTZ||Inicio
finalizada_en|TIMESTAMPTZ|NULL|Fin
''',note='empresa_id corresponde a la solicitud incluso si no se llega a producir factura; el trigger valida pertenencia cuando factura_id tiene valor. Se conserva como contexto histórico del intento, no como atributo del documento.')
table('revision_recurrencia','Conserva la decisión humana sobre un patrón recurrente.', '''
id|BIGINT|PK|Identificador de revisión
empresa_id|BIGINT|FK empresa|Empresa analizada
huella|CHAR(64)||Huella del patrón en la empresa
estado|VARCHAR(12)||pending confirmed o rejected
usuario_id|BIGINT|FK usuario|Usuario que revisó
actualizada_en|TIMESTAMPTZ||Instante de revisión
''',unique='empresa_id,huella',checks="estado IN ('pending','confirmed','rejected')")
table('evidencia_recurrencia','Descompone la evidencia repetida de una recurrencia en movimientos observados.', '''
revision_id|BIGINT|PK FK revision_recurrencia|Revisión del patrón
movimiento_id|BIGINT|PK FK movimiento|Movimiento que sustenta el patrón
fecha_observada|DATE||Fecha en la versión evaluada
importe_observado|NUMERIC(18,2)||Valor en la versión evaluada
''',note='Los valores observados son snapshots inmutables; no dependen del estado actual del movimiento.')
table('ocurrencia_recurrencia','Vincula una materialización del patrón con la obligación generada.', '''
id|BIGINT|PK|Identificador de ocurrencia
revision_id|BIGINT|FK revision_recurrencia|Patrón de origen
clave|CHAR(64)||Huella de materialización dentro del patrón
obligacion_id|BIGINT|UQ FK obligacion|Obligación generada
''',unique='revision_id,clave',note='No repite empresa_id. Un trigger mantiene además la unicidad de clave por empresa, compatible con RecurrenceOccurrence.')
table('pronostico','Cabecera inmutable de una ejecución de proyección de caja.', '''
id|BIGINT|PK|Identificador de ejecución
empresa_id|BIGINT|FK empresa|Empresa evaluada
usuario_id|BIGINT|FK usuario|Solicitante
huella|CHAR(64)||Huella de entradas y configuración
metodo|VARCHAR(32)||Método y versión utilizados
horizonte|SMALLINT||Días proyectados
fecha_corte|DATE||Fecha de referencia
creado_en|TIMESTAMPTZ||Instante de cálculo
''',unique='empresa_id,huella',checks='horizonte BETWEEN 30 AND 90')
table('parametro_pronostico','Registra parámetros escalares de una ejecución reproducible.', '''
pronostico_id|BIGINT|PK FK pronostico|Ejecución propietaria
nombre|VARCHAR(80)|PK|Nombre del parámetro
valor|TEXT||Valor escalar serializado sin listas
''')
table('punto_pronostico','Almacena el resultado diario por escenario en lugar de un arreglo JSON.', '''
pronostico_id|BIGINT|PK FK pronostico|Ejecución de origen
fecha|DATE|PK|Día proyectado
escenario|VARCHAR(12)|PK|expected lower o upper
saldo|NUMERIC(18,2)||Saldo proyectado en COP
''',checks="escenario IN ('expected','lower','upper')",note='Los escenarios son salidas del método; lower y upper no se presentan como cuantiles calibrados sin evidencia experimental.')
table('entrada_cuenta','Conserva el saldo de entrada de cada cuenta en cada pronóstico.', '''
pronostico_id|BIGINT|PK FK pronostico|Ejecución
cuenta_id|BIGINT|PK FK cuenta|Cuenta utilizada
fecha_observada|DATE||Corte utilizado al ejecutar
saldo_observado|NUMERIC(18,2)||Saldo de entrada inmutable
''')
table('entrada_movimiento','Conserva los valores de movimientos utilizados por cada ejecución.', '''
pronostico_id|BIGINT|PK FK pronostico|Ejecución
movimiento_id|BIGINT|PK FK movimiento|Movimiento utilizado
fecha_observada|DATE||Fecha del movimiento al ejecutar
importe_observado|NUMERIC(18,2)||Valor utilizado
categoria_observada_id|BIGINT|FK categoria|Categoría utilizada al ejecutar
''')
table('entrada_obligacion','Conserva pendientes y vencimientos tal como fueron proyectados.', '''
pronostico_id|BIGINT|PK FK pronostico|Ejecución
obligacion_id|BIGINT|PK FK obligacion|Obligación utilizada
vencimiento_observado|DATE||Vencimiento al ejecutar
pendiente_observado|NUMERIC(18,2)||Pendiente utilizado
direccion_observada|VARCHAR(3)||Sentido utilizado
''',checks="pendiente_observado >= 0 AND direccion_observada IN ('in','out')")
table('evaluacion_alerta','Registra una evaluación histórica de riesgo con su umbral de entrada.', '''
id|BIGINT|PK|Identificador de evaluación
pronostico_id|BIGINT|FK pronostico|Pronóstico evaluado
usuario_id|BIGINT|FK usuario|Solicitante de la evaluación
huella|CHAR(64)||Huella de evaluación
umbral_observado|NUMERIC(18,2)||Umbral utilizado en ese instante
creada_en|TIMESTAMPTZ||Instante de evaluación
''',unique='pronostico_id,huella',note='La empresa se deriva del pronóstico. La unicidad histórica por empresa y huella del modelo original se conserva mediante trigger con bloqueo de empresa.')
table('alerta','Almacena cada hallazgo de una evaluación de riesgo.', '''
id|BIGINT|PK|Identificador de alerta
evaluacion_id|BIGINT|FK evaluacion_alerta|Evaluación de origen
secuencia|SMALLINT||Posición única dentro de la evaluación
nivel|VARCHAR(12)||Nivel de riesgo comunicado
fecha_inicio|DATE||Inicio del período en riesgo
fecha_fin|DATE||Fin del período en riesgo
saldo_minimo|NUMERIC(18,2)||Mínimo proyectado en el período
mensaje|TEXT||Explicación del hallazgo
''',unique='evaluacion_id,secuencia',checks='fecha_inicio <= fecha_fin')
table('factor_alerta','Separa la lista de factores explicativos de cada alerta.', '''
alerta_id|BIGINT|PK FK alerta|Alerta explicada
posicion|SMALLINT|PK|Orden del factor
descripcion|VARCHAR(250)||Factor explicativo en lenguaje natural
''')
table('auditoria','Registra un evento de modificación sin sobrescribir el historial.', '''
id|BIGINT|PK|Identificador del evento
empresa_id|BIGINT|FK empresa|Contexto empresarial del evento
usuario_id|BIGINT|FK usuario|Actor responsable
accion|VARCHAR(80)||Operación ejecutada
entidad|VARCHAR(80)||Tipo de objeto auditado
objeto_id|VARCHAR(80)||Identificador histórico textual
creada_en|TIMESTAMPTZ||Momento del evento
''',note='objeto_id es una referencia histórica descriptiva, no una FK polimórfica; conserva eventos aunque el objeto deje de existir. No sustituye las FKs del modelo financiero.')
table('detalle_auditoria','Descompone before y after en cambios escalares por atributo.', '''
auditoria_id|BIGINT|PK FK auditoria|Evento auditado
campo|VARCHAR(120)|PK|Ruta de atributo escalar
valor_anterior|TEXT|NULL|Valor antes del evento
valor_nuevo|TEXT|NULL|Valor después del evento
''',note='Las colecciones se expanden por ruta e índice; cada fila representa un cambio elemental y no almacena objetos JSON.')
table('tarea','Registra los mensajes persistentes de trabajo en segundo plano.', '''
id|BIGINT|PK|Identificador de mensaje
nombre|VARCHAR(120)||Función autorizada a ejecutar
estado|VARCHAR(12)||Estado de la entrega
intentos|SMALLINT||Número de intentos
disponible_en|TIMESTAMPTZ||Instante de próximo procesamiento
lease|UUID|NULL|Identificador del reclamo temporal
creada_en|TIMESTAMPTZ||Creación
finalizada_en|TIMESTAMPTZ|NULL|Finalización
''',checks='intentos BETWEEN 0 AND 3')
table('parametro_tarea','Representa argumentos escalares posicionales o nombrados de una tarea.', '''
tarea_id|BIGINT|PK FK tarea|Mensaje propietario
nombre|VARCHAR(80)|PK|Nombre o posición arg0 arg1
valor|TEXT||Valor escalar del argumento
''',note='El contrato de tareas permite IDs de trabajo y escalares. Se purgan los parámetros al finalizar; el despachador valida nombre y tipo del argumento.')
table('limite_solicitud','Conserva contadores persistentes para ventanas de autenticación.', '''
clave|CHAR(64)|PK|HMAC de identidad y ventana
solicitudes|INTEGER||Peticiones acumuladas
vence_en|TIMESTAMPTZ||Fin de la ventana
''',checks='solicitudes >= 0')

# Optional one-to-one links are relations of their own; import results do not
# duplicate the enterprise already fixed by their document.
for tn,removed in [('cuenta',{'conexion_id'}),('factura',{'obligacion_id','empresa_id'}),('importacion_factura',{'factura_id','duplicada'})]:
    t=next(t for t in tables if t['name']==tn)
    t['fields']=[f for f in t['fields'] if f['name'] not in removed]
    if tn=='cuenta':t['note']='Todas las cuentas operan en COP. La asociación opcional con una conexión se conserva en cuenta_conexion.'
    if tn=='importacion_factura':t['note']='El resultado se conserva en resultado_importacion_factura; así factura_id no determina una empresa repetida dentro del intento.'
    if tn=='factura':
        t['unique']=''
        next(f for f in t['fields'] if f['name']=='cufe')['key']='UQ'
        t['note']='CUFE es clave candidata global del documento. Su registro por empresa se separa en registro_factura; así un mismo XML no repite sus datos financieros cuando lo registra el emisor y también el receptor. La dirección se deriva del NIT empresarial y las partes históricas.'
table('registro_factura','Asocia una factura global con cada empresa que la registra.', '''
id|BIGINT|PK|Identificador del registro empresarial
empresa_id|BIGINT|FK empresa|Empresa que incorpora la factura
factura_id|BIGINT|FK factura|Documento global por CUFE
registrada_en|TIMESTAMPTZ||Instante del registro empresarial
''',unique='empresa_id,factura_id',note='El documento existe una sola vez por CUFE y la pareja empresa factura existe una sola vez. La empresa debe ser emisor o receptor según las partes del XML.')
table('cuenta_conexion','Separa la asociación opcional entre una cuenta y una conexión.', '''
cuenta_id|BIGINT|PK FK cuenta|Cuenta vinculada
conexion_id|BIGINT|UQ FK conexion|Conexión exclusiva de la cuenta
''',note='Ambas columnas son claves candidatas. Un trigger valida que la cuenta y el consentimiento pertenezcan a la misma empresa.')
table('factura_obligacion','Separa el vínculo opcional uno a uno entre registro empresarial y obligación.', '''
registro_id|BIGINT|PK FK registro_factura|Registro de factura confirmado
obligacion_id|BIGINT|UQ FK obligacion|Obligación respaldada por el documento
''',note='Ambas columnas son claves candidatas; la empresa y el sentido se verifican sin repetirlos en esta asociación.')
table('resultado_importacion_factura','Registra el documento identificado por un intento exitoso.', '''
importacion_id|BIGINT|PK FK importacion_factura|Intento de importación
registro_id|BIGINT|FK registro_factura|Registro empresarial creado o ya existente
duplicada|BOOLEAN||Indica si la factura ya existía al importar
''',note='Un registro empresarial admite muchos intentos; cada intento tiene a lo sumo un resultado. La empresa de la solicitud debe coincidir con la del registro.')

# Template evidence and package contract, before modifying the working copy.
z=ZipFile(REF); baseline={n:sha256(z.read(n)).hexdigest() for n in z.namelist()}
reference_hash=sha256(REF.read_bytes()).hexdigest()
(WORK/'package-baseline.json').write_text(json.dumps(baseline,indent=2),encoding='utf-8')
(WORK/'schema.json').write_text(json.dumps(tables,ensure_ascii=False,indent=2),encoding='utf-8')
(WORK/'artifact.md').write_text(f'''# Contrato de plantilla
Referencia {REF}\nSHA256 {sha256(REF.read_bytes()).hexdigest()}
Render de referencia template.pdf y template-0.png template-1.png. Dos páginas y una sección.
Página oficio 21.5935 por 33.0041 cm. Márgenes superior 4.7008 inferior 3.5013 izquierdo y derecho 2.5012 cm.
Normal Arial 11 pt justificado antes 6 pt; títulos Heading 1 16 pt y Heading 2 12 pt con numeración multinivel real del origen.
Conservar styles.xml numbering.xml tema encabezados pies imágenes y relaciones preexistentes byte por byte.
Cubierta institucional en dos representaciones DrawingML y VML: primer párrafo anclado del body; slots de título descripción y fecha se sustituyen en ambas representaciones.
El bloque título y descripción se amplía verticalmente para autor y documento manteniendo posición y ancho. Segundo párrafo lleva salto a cuerpo.
Eliminar párrafos de muestra document.xml body p[3..13]; insertar secciones propias reutilizando Heading 1 Heading 2 y Normal. Mantener sectPr.
Añadir tablas con Arial 9 pt borde gris y cabecera gris; diagramas negros a ancho útil 16.59 cm. Permitir nuevas relaciones de imágenes sin alterar las existentes.
Portada conserva color institucional del título. En el cuerpo se conserva jerarquía cromática de la plantilla. Cambios de paginación esperados por contenido nuevo.
Footer contiene PAGE; se actualiza campo al renderizar con Word. No se agregan docentes ni credenciales académicas no confirmadas.
Inventario completo package-baseline.json. Solo document.xml document.xml.rels core.xml settings.xml y nuevas imágenes son editables.
''',encoding='utf-8')

d=Document(REF)
body=d._element.body
for e in list(body)[2:]:
    if e.tag!=qn('w:sectPr'): body.remove(e)
# Fill the two cover representations, cloning source formatting for new text lines.
for tx in body.xpath('.//w:txbxContent'):
    pars=tx.findall(qn('w:p'))
    joined=''.join(tx.itertext())
    if 'TÍTULO DEL DOCUMENTO' in joined:
        for t in tx.xpath('.//*[local-name()="t"]'):
            if t.text=='TÍTULO DEL DOCUMENTO': t.text='Base de datos de Horizonte'
            elif t.text=='Descripción': t.text='Diseño relacional normalizado a FN3'
            elif t.text==' del documento': t.text=''
        source=pars[-1]
        for text in ['Adrian Perez Pacheco','Documento 1111043406']:
            p=deepcopy(source)
            for node in list(p):
                if node.tag!=qn('w:pPr'): p.remove(node)
            r=OxmlElement('w:r'); pr=OxmlElement('w:rPr'); fonts=OxmlElement('w:rFonts'); fonts.set(qn('w:ascii'),'Arial'); fonts.set(qn('w:hAnsi'),'Arial'); pr.append(fonts); sz=OxmlElement('w:sz');sz.set(qn('w:val'),'24');pr.append(sz); r.append(pr);t=OxmlElement('w:t');t.text=text;r.append(t);p.append(r);tx.append(p)
    for t in tx.xpath('.//*[local-name()="t"]'):
        if t.text=='Fecha': t.text='15 de octubre de 2026'
for anchor in body.xpath('.//*[local-name()="anchor"]'):
    if 'Base de datos de Horizonte' in ''.join(anchor.itertext()):
        ext=anchor.find('{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}extent');ext.set('cy','2000000')
        for ex in anchor.xpath('.//*[local-name()="xfrm"]/*[local-name()="ext"]'): ex.set('cy','2000000')
for shape in body.xpath('.//*[local-name()="shape"]'):
    if 'Base de datos de Horizonte' in ''.join(shape.itertext()): shape.set('style',re.sub(r'height:76.2pt','height:157.5pt',shape.get('style','')))

def p(text,style=None):
    x=d.add_paragraph(text,style);return x
def h(text,level=1):
    x=d.add_paragraph(text,'Heading '+str(level)); return x
def page(): d.add_page_break()
def grid(headers,rows,widths=None):
    if d.paragraphs:
        d.paragraphs[-1].paragraph_format.keep_with_next=True
    t=d.add_table(rows=1, cols=len(headers));t.autofit=False
    if widths:
        for c,w in zip(t.columns,widths):c.width=Cm(w)
    for c,tx in zip(t.rows[0].cells,headers): c.text=str(tx)
    for row in rows:
        for c,tx in zip(t.add_row().cells,row):c.text=str(tx)
    for i,row in enumerate(t.rows):
        if widths:
            for c,w in zip(row.cells,widths):c.width=Cm(w)
        trpr=row._tr.get_or_add_trPr();cant=OxmlElement('w:cantSplit');trpr.append(cant)
        if i==0:
            repeat=OxmlElement('w:tblHeader');trpr.append(repeat)
        for c in row.cells:
            pr=c._tc.get_or_add_tcPr();mar=OxmlElement('w:tcMar')
            for side in ['top','left','bottom','right']:
                e=OxmlElement('w:'+side);e.set(qn('w:w'),'75');e.set(qn('w:type'),'dxa');mar.append(e)
            pr.append(mar)
            sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'E9E9E9' if i==0 else 'FFFFFF');pr.append(sh)
            for pp in c.paragraphs:
                pp.paragraph_format.space_before=Pt(0);pp.paragraph_format.space_after=Pt(2);pp.paragraph_format.line_spacing=1.0
                pp.paragraph_format.keep_with_next=(i<min(3,len(t.rows)-1))
                pp.alignment=WD_ALIGN_PARAGRAPH.LEFT
                for r in pp.runs:r.font.name='Arial';r.font.size=Pt(9);r.bold=(i==0)
    borders=OxmlElement('w:tblBorders')
    for name in ['top','left','bottom','right','insideH','insideV']:
        b=OxmlElement('w:'+name);b.set(qn('w:val'),'single');b.set(qn('w:sz'),'4');b.set(qn('w:color'),'D9D9D9');borders.append(b)
    t._tbl.tblPr.append(borders)
    return t
def code(text):
    for ln in text.splitlines():
        x=p(ln);x.alignment=WD_ALIGN_PARAGRAPH.LEFT;x.paragraph_format.space_before=Pt(0);x.paragraph_format.space_after=Pt(0);x.paragraph_format.line_spacing=1
        for r in x.runs:r.font.name='Consolas';r.font.size=Pt(8)
def fig(path,caption):
    pp=d.add_paragraph();pp.paragraph_format.keep_with_next=True;pp.add_run().add_picture(str(path),width=Cm(16.4));pp.alignment=WD_ALIGN_PARAGRAPH.CENTER
    cap=p(caption);cap.alignment=WD_ALIGN_PARAGRAPH.CENTER
    for r in cap.runs:r.font.size=Pt(9)

toc_title=p('Contenido');toc_title.paragraph_format.space_after=Pt(12)
for r in toc_title.runs:r.bold=True;r.font.size=Pt(16)
toc_entries=[]
toc_pages=json.loads((WORK/'toc-pages.json').read_text(encoding='utf-8')) if (WORK/'toc-pages.json').exists() else {}
toc_names=['Introducción','Planteamiento del problema','Justificación','Objetivos','Alcance y contexto de implementación','Mapa de módulos y requerimientos de datos','Reglas de negocio e integridad','Modelo entidad relación MER','Modelo relacional inicial y proceso de normalización','Modelo relacional final en FN3','Diccionario de datos y verificación por tabla','Diseño físico y estrategia transaccional','Correspondencia con la implementación existente','Consultas SQL de validación','Escenario ilustrativo y plan de pruebas','Conclusiones','Referencias del proyecto','Anexo de definición física en PostgreSQL']
for num,title in enumerate(toc_names,1):
    x=p(f'{num}  {title}'+('\t'+str(toc_pages[title]) if title in toc_pages else ''));x.paragraph_format.space_before=Pt(3);x.paragraph_format.space_after=Pt(3);x.alignment=WD_ALIGN_PARAGRAPH.LEFT
    x.paragraph_format.tab_stops.add_tab_stop(Cm(16),WD_ALIGN_PARAGRAPH.RIGHT)
    toc_entries.append(x)
page()
h('Introducción')
p('Horizonte integra movimientos bancarios, facturas y obligaciones para analizar la liquidez de microempresas. Este documento diseña su base de datos relacional en PostgreSQL, define las entidades y sus restricciones, presenta el modelo entidad relación y el modelo relacional, y desarrolla la normalización hasta la tercera forma normal o FN3.')
p('La propuesta organiza el dato financiero por empresa y separa tres hechos diferentes: dinero registrado en una cuenta, documentos de facturación y cobros o pagos esperados. Una factura no demuestra un recaudo; la conciliación relaciona la obligación con el movimiento que efectivamente ocurrió. Esta distinción evita contabilizar dos veces el mismo flujo en las proyecciones.')
p('El esquema lógico final formaliza y normaliza los módulos de los modelos Django del proyecto. Su implementación requiere migraciones: los modelos actuales aún incluyen campos JSON, categorías como texto y algunos identificadores empresariales repetidos. El diseño físico incluido corresponde a la propuesta normalizada y no constituye una modificación del código ni de una base de datos en producción.')
h('Planteamiento del problema')
p('La información de caja puede quedar dispersa entre extractos, archivos de carga, facturas y compromisos futuros. Al consolidarla sin reglas comunes aparecen movimientos duplicados, categorías escritas de varias maneras, saldos cuyo corte no coincide y obligaciones sin evidencia de cumplimiento. Las listas guardadas dentro de documentos JSON también dificultan consultar las relaciones mediante claves foráneas.')
p('En el proyecto, una conexión depende de un consentimiento que ya identifica la empresa; repetir esa empresa en ambos registros permite inconsistencias. De forma similar, los nombres de categoría se repiten en movimientos, reglas y correcciones. Los resultados de pronóstico, las evidencias y los alcances necesitan relaciones propias si se pretende un modelo relacional consultable e íntegro.')
p('La pregunta de diseño es cómo centralizar la información de liquidez de varias empresas, preservar su trazabilidad y eliminar dependencias parciales y transitivas, manteniendo deduplicación, conciliación y reproducción histórica de los cálculos.')
h('Justificación')
p('Una base relacional normalizada permite identificar cada hecho una sola vez y unirlo mediante claves explícitas. PostgreSQL aporta importes decimales exactos, restricciones de integridad y transacciones para coordinar importaciones y conciliaciones concurrentes. La separación entre hechos actuales y observaciones históricas permite explicar un pronóstico sin depender de datos que pudieron cambiar después.')
h('Objetivos')
h('Objetivo general',2)
p('Diseñar una base de datos relacional para Horizonte que integre empresas, usuarios, movimientos, facturas, obligaciones, conciliaciones y evaluaciones de liquidez mediante un esquema normalizado hasta FN3.')
h('Objetivos específicos',2)
for tx in ['Identificar las entidades y los requerimientos de información de los módulos existentes.', 'Definir claves candidatas, claves primarias, relaciones, cardinalidades y reglas de pertenencia empresarial.', 'Transformar listas y resultados estructurados en relaciones con atributos atómicos.', 'Demostrar la eliminación de dependencias parciales y transitivas en todas las tablas del modelo final.', 'Especificar tipos de datos, restricciones, índices y operaciones transaccionales para PostgreSQL.', 'Proponer consultas y casos de validación que comprueben integridad, deduplicación y trazabilidad.']: p('• '+tx)
h('Alcance y contexto de implementación')
p('Se incluyen los módulos accounts, banking, classify, invoices y forecast, así como la cola persistente y los límites de solicitudes usados por la aplicación. El modelo financiero opera en COP, con importes NUMERIC de 18 dígitos y 2 decimales; los eventos utilizan TIMESTAMPTZ y las fechas de negocio se interpretan en America/Bogota.')
p('Las fuentes de prueba son archivos CSV y XLSX, facturas XML y el adaptador Mock Bank. El diseño no inicia transferencias, no reemplaza contabilidad oficial y no supone conexión bancaria real en producción. La clasificación y los métodos de proyección se documentan como consumidores de la base de datos; la precisión estadística requiere evaluación independiente.')
p('Las tablas internas de Django para sesiones, grupos, permisos, contenido y migraciones siguen siendo administradas por el framework. No constituyen entidades financieras ni se rediseñan aquí. usuario representa los atributos de auth_user necesarios para relacionar a los actores del dominio.')
h('Mapa de módulos y requerimientos de datos')
grid(['Módulo','Datos y responsabilidad'],[
('Identidad y acceso','empresa usuario rol membresia; pertenencia y permisos por empresa.'),
('Integración bancaria','proveedor consentimiento alcance conexion cuenta corte_cuenta; autorización y saldos.'),
('Movimientos y clasificación','tercero alias_tercero categoria movimiento regla_clasificacion cambio_clasificacion; ETL y corrección.'),
('Facturación y conciliación','factura parte_factura obligacion conciliacion; caja esperada y aplicación de pagos.'),
('Recurrencias y proyección','revision_recurrencia evidencias ocurrencias pronostico entradas y puntos diarios.'),
('Riesgo y operación','evaluacion_alerta alerta factor_alerta auditoria tarea y limite_solicitud; trazabilidad y procesamiento.')],[4,12.5])
p('El flujo de datos es fuente financiera → importación o sincronización → movimiento normalizado → clasificación → conciliación con obligación. En paralelo, el XML genera factura y, después de confirmación, una obligación. Los cortes y las obligaciones pendientes alimentan el pronóstico; sus resultados alimentan las alertas. Cada modificación relevante produce auditoría.')
h('Reglas de negocio e integridad')
rules=[
('RN01','Cada movimiento pertenece a una sola cuenta y cada cuenta a una empresa. Todos los objetos financieros de una operación deben pertenecer a la misma empresa.'),
('RN02','La pareja cuenta e identificador externo es única. Reintentar un archivo no crea un segundo movimiento con la misma identidad.'),
('RN03','Una conexión requiere un consentimiento vigente; revocarlo impide nuevas sincronizaciones. Cada consentimiento respalda a lo sumo una conexión.'),
('RN04','Solo existe una conexión activa por empresa y proveedor. Una cuenta admite como máximo una conexión y una conexión como máximo una cuenta.'),
('RN05','El propietario puede administrar y el contador operar sobre datos financieros; consulta solo lee. La condición de superusuario se conserva separada de los roles empresariales.'),
('RN06','El CUFE identifica globalmente la factura. Su incorporación empresarial se deduplica por empresa y factura. El número comercial por sí solo no identifica universalmente un documento.'),
('RN07','La conciliación requiere importe positivo, igual empresa y dirección compatible con el signo del movimiento. La suma activa no puede superar ni el importe base de la obligación ni el valor absoluto del movimiento.'),
('RN08','Revertir una conciliación registra fecha de reversión y restituye el pendiente calculado. Un reintento con igual obligación y solicitud conserva el resultado original.'),
('RN09','Las facturas tienen exactamente dos partes: emisor y receptor. El NIT de la empresa debe coincidir con exactamente una de ellas.'),
('RN10','Una factura y su obligación vinculada deben tener la misma empresa y sentido, vencimiento no anterior a emisión y pendiente compatible con el pagadero.'),
('RN11','Los snapshots son observaciones inmutables al ejecutar. Un cambio posterior en una categoría, saldo o vencimiento no debe reescribir un resultado histórico.'),
('RN12','Los pronósticos tienen horizonte de 30 a 90 días. La falta de movimientos en un período no prueba cobertura completa ni saldo cero.'),
('RN13','Los mensajes persistentes tienen hasta tres intentos y reclamo temporal; las operaciones financieras deben ser idempotentes ante entregas repetidas.'),
('RN14','Se preservan movimientos y evidencias con borrado restringido. Las listas consultables se guardan como filas, no como arreglos incrustados.')]
grid(['Regla','Condición'],rules,[1.7,14.8])
h('Modelo entidad relación MER')
p('El MER se divide por dominios para conservar la legibilidad. Cada rectángulo representa una entidad; una línea identifica el vínculo y muestra la participación mínima y máxima en sus extremos. La tabla de relaciones complementa los diagramas y enumera todas las claves foráneas del modelo completo. 1 significa exactamente uno y 0..N significa cero o muchos.')

fontfile='C:/Windows/Fonts/arial.ttf';boldfile='C:/Windows/Fonts/arialbd.ttf'
def font(n,b=False): return ImageFont.truetype(boldfile if b else fontfile,n)
def draw_mer(name,nodes,edges):
    W,H=1600,1450;im=Image.new('RGB',(W,H),'white');dr=ImageDraw.Draw(im)
    # A deliberately sparse two-column layout with explicit cardinality labels.
    positions={n:(40+(i%2)*860,60+(i//2)*275) for i,n in enumerate(nodes)}
    for a,b,label,ca,cb in edges:
        ax,ay=positions[a];bx,by=positions[b];ac=(ax+320,ay+70);bc=(bx+320,by+70)
        if ay==by:
            start=(ax+640,ay+70) if ax<bx else (ax,ay+70);end=(bx,by+70) if ax<bx else (bx+640,by+70)
        else:
            start=(ax+320,ay+140 if by>ay else ay);end=(bx+320,by if by>ay else by+140)
        dr.line([start,end],fill='#555555',width=3)
        mx,my=((start[0]+end[0])/2,(start[1]+end[1])/2)
        horizontal=ay==by
        if horizontal:my-=43
        bb=dr.textbbox((0,0),label,font=font(23));dr.rectangle((mx-(bb[2]+14)/2,my-18,mx+(bb[2]+14)/2,my+18),fill='white');dr.text((mx,my),label,font=font(23),fill='black',anchor='mm')
        # Place endpoint multiplicities along the connecting segment.
        for at,other,txt in [(start,end,ca),(end,start,cb)]:
            xx=at[0]*.8+other[0]*.2; yy=at[1]*.8+other[1]*.2
            if horizontal:yy+=30
            dr.rectangle((xx-40,yy-16,xx+40,yy+16),fill='white');dr.text((xx,yy),txt,font=font(23,True),fill='black',anchor='mm')
    byname={t['name']:t for t in tables}
    for n,(x,y) in positions.items():
        dr.rounded_rectangle((x,y,x+640,y+140),radius=10,fill='#F2F2F2',outline='black',width=3)
        tx=n.replace('_',' ').upper();dr.text((x+320,y+42),tx,font=font(28,True),fill='black',anchor='mm')
        key=', '.join(f['name'] for f in byname[n]['fields'] if 'PK' in f['key'])
        dr.text((x+320,y+92),'Identificador  '+key,font=font(21),fill='black',anchor='mm')
    height=max(y for x,y in positions.values())+190
    path=WORK/(name+'.png');im.crop((0,0,W,height)).save(path);return path

mer_specs=[
('mer_acceso',['empresa','membresia','usuario','rol'],[('empresa','membresia','autoriza','1','0..N'),('usuario','membresia','pertenece','1','0..N'),('rol','membresia','define','1','0..N')]),
('mer_banca',['empresa','consentimiento','cuenta','conexion','corte_cuenta','proveedor','consentimiento_alcance','alcance'],[('empresa','consentimiento','otorga','1','0..N'),('empresa','cuenta','posee','1','0..N'),('consentimiento','conexion','habilita','1','0..1'),('cuenta','corte_cuenta','registra','1','0..N'),('proveedor','conexion','atiende','1','0..N'),('consentimiento_alcance','alcance','concede','0..N','1')]),
('mer_caja',['cuenta','movimiento','obligacion','conciliacion','factura','parte_factura'],[('cuenta','movimiento','registra','1','0..N'),('movimiento','conciliacion','se aplica','1','0..N'),('obligacion','conciliacion','se cubre','1','0..N'),('factura','obligacion','respalda por registro','0..1','0..2'),('factura','parte_factura','declara','1','2')]),
('mer_clasificacion',['empresa','tercero','regla_clasificacion','alias_tercero','categoria','movimiento','cambio_clasificacion','usuario'],[('empresa','tercero','reconoce','1','0..N'),('tercero','alias_tercero','admite','1','0..N'),('categoria','movimiento','clasifica','1','0..N'),('movimiento','cambio_clasificacion','conserva','1','0..N'),('usuario','cambio_clasificacion','corrige','1','0..N'),('regla_clasificacion','categoria','asigna','0..N','1')]),
('mer_proyeccion',['revision_recurrencia','evidencia_recurrencia','ocurrencia_recurrencia','obligacion','pronostico','punto_pronostico','evaluacion_alerta','alerta'],[('revision_recurrencia','evidencia_recurrencia','se sustenta','1','0..N'),('revision_recurrencia','ocurrencia_recurrencia','origina','1','0..N'),('ocurrencia_recurrencia','obligacion','materializa','0..1','1'),('pronostico','punto_pronostico','produce','1','0..N'),('pronostico','evaluacion_alerta','se evalúa','1','0..N'),('evaluacion_alerta','alerta','detecta','1','0..N')])]
for i,(nm,nodes,edges) in enumerate(mer_specs,1):
    h(['Acceso empresarial','Autorización y fuentes bancarias','Movimientos documentos y conciliación','Clasificación y terceros','Recurrencias proyección y riesgo'][i-1],2)
    fig(draw_mer(nm,nodes,edges),f'Figura {i} MER del dominio {i}')
    p('Las relaciones auxiliares de importación, entradas históricas, parámetros y auditoría se especifican en el inventario completo que sigue. Los diagramas se leen conjuntamente; las entidades repetidas representan la misma entidad, no copias de los datos.')

h('Inventario completo de relaciones',2)
relations=[]
for t in tables:
    for f in t['fields']:
        if 'FK ' in f['key']:
            target=f['key'].split('FK ')[1].split()[0]
            child='0..1' if 'UQ' in f['key'] or ('PK' in f['key'] and sum('PK' in ff['key'] for ff in t['fields'])==1) else '0..N'
            parent='0..1' if 'NULL' in f['key'] else '1'
            relations.append((target,t['name']+'.'+f['name'],parent,child))
grid(['Entidad referida','Atributo que referencia','Padres por fila','Filas por padre'],relations,[3.1,9.2,2.1,2.1])
p('La cardinalidad especial factura → parte_factura exige exactamente dos filas, una por papel; no se expresa únicamente con una FK y se completa con una restricción diferida. Las asociaciones membresia y consentimiento_alcance resuelven relaciones N a M; conciliacion permite varios movimientos por obligación y varias obligaciones por movimiento, dentro de los límites de importe.')

h('Modelo relacional inicial y proceso de normalización')
h('Punto de partida sin normalizar',2)
p('Como ficha de análisis, una empresa podría almacenarse junto con sus usuarios, cuentas y movimientos, además de listas de permisos y resultados diarios. Esa representación mezcla entidades y grupos repetidos. Se expresa como EMPRESA_FICHA(empresa, nit, nombre, {usuarios y roles}, {cuentas y movimientos}, {consentimientos y alcances}, {facturas y partes}, {pronósticos y puntos}). Las llaves entre llaves indican colecciones, no valores escalares.')
p('Una fila de ejemplo sería una empresa E1 con dos cuentas C1 y C2; C1 incluiría movimientos M1 y M2 y un pronóstico P1 contendría varios días. Agregar M3 obligaría a reescribir una colección, y cambiar un nombre de categoría requeriría modificar múltiples apariciones. Esta ficha sirve para explicar la transformación; no representa una tabla creada en el repositorio.')
h('Primera forma normal',2)
p('Se separan los grupos repetidos en relaciones: cada fila representa un solo usuario, movimiento, alcance, parte de factura o punto diario. Se prohíben listas dentro de atributos consultables. Los archivos temporales de importación permanecen como documentos opacos de transporte y se purgan; su contenido financiero se descompone antes de persistirse en las tablas del dominio.')
code('MOVIMIENTO_1FN(cuenta_id, externo_id, empresa_id, nit,\n nombre_empresa, fecha, importe, categoria_id, nombre_categoria)\nPK(cuenta_id, externo_id)')
p('La clave identifica un movimiento dentro de una cuenta. Ya no hay celdas con varias transacciones, pero empresa_id depende solo de cuenta_id. El nombre de categoría depende de categoria_id, por lo que aún existen redundancias.')
h('Segunda forma normal',2)
p('Se eliminan dependencias de una parte de las claves compuestas. En MOVIMIENTO_1FN, cuenta_id → empresa_id no necesita externo_id. Por ello la empresa sale del movimiento y se relaciona mediante cuenta. En membresia, el nombre del usuario no depende de empresa_id y el nombre del rol no depende de usuario_id; ambos se conservan en sus entidades maestras.')
code('CUENTA_2FN(id, empresa_id, nombre)\nMOVIMIENTO_2FN(cuenta_id, externo_id, fecha, importe,\n categoria_id, nombre_categoria)\nMEMBRESIA(empresa_id, usuario_id, rol_codigo)')
p('Introducir un identificador artificial por sí solo no demuestra FN2: se deben examinar también las claves candidatas naturales. En movimiento se revisa (cuenta_id, externo_id); en membresia se revisa (empresa_id, usuario_id); en puntos de pronóstico se revisa la ejecución, la fecha y el escenario.')
h('Tercera forma normal',2)
p('Se eliminan dependencias transitivas de atributos no clave. Si movimiento_id → categoria_id y categoria_id → nombre_categoria, el nombre pertenece solo a categoria. Si conexion_id → consentimiento_id y consentimiento_id → empresa_id, la empresa se obtiene por el consentimiento y se elimina de conexion. Se aplica la misma separación entre alias y tercero y entre evaluación de alerta y pronóstico.')
code('CATEGORIA(id, nombre)\nMOVIMIENTO(id, cuenta_id, externo_id, fecha, importe, categoria_id, ...)\nCONSENTIMIENTO(id, empresa_id, usuario_id, ...)\nCONEXION(id, consentimiento_id, proveedor_codigo, ...)')
p('Formalmente, para toda dependencia funcional no trivial X → A, X debe ser superclave o A debe ser atributo primo. En el esquema final, con las dependencias declaradas, los determinantes de atributos descriptivos son claves candidatas. Los catálogos con nombre único tienen también esa clave alternativa. La FN3 se verifica con respecto a estas reglas semánticas y no se deduce únicamente del uso de PK numéricas.')
h('Descomposición sin pérdida y conservación de dependencias',2)
p('Separar MOVIMIENTO y CATEGORIA es sin pérdida porque la intersección categoria_id es clave de CATEGORIA. Separar CONEXION y CONSENTIMIENTO también es sin pérdida por consentimiento_id, clave del consentimiento. Las dependencias de cada maestro se mantienen localmente; las asociaciones se reconstruyen mediante FK y JOIN. La unicidad condicionada por empresa que atraviesa varias tablas se mantiene como regla transaccional o trigger, sin reintroducir empresa_id redundante.')
p('El CUFE determina la cabecera fiscal completa aunque el mismo documento sea registrado por dos empresas. Por eso factura utiliza CUFE como clave candidata global y registro_factura separa la asociación empresarial. Conservar la cabecera duplicada bajo la clave empresa y CUFE mantendría una dependencia parcial de CUFE y no satisfaría la normalización pretendida.')
grid(['Anomalía inicial','Transformación final','Efecto'],[
('Nombres de categoría repetidos','categoria y FK desde movimientos reglas y cambios','Una actualización del catálogo no exige reescribir hechos.'),
('empresa_id en conexión y consentimiento','Empresa solo en consentimiento','Se impiden dos empresas para una misma autorización.'),
('scopes como lista','alcance y consentimiento_alcance','Cada permiso puede validarse y consultarse por FK.'),
('before y after como objetos','auditoria y detalle_auditoria','Cada cambio elemental tiene una identidad propia.'),
('Factura con data duplicada','factura y parte_factura','CUFE número importes y partes tienen una sola ubicación.'),
('result y evidence con listas','punto_pronostico y tablas de entrada','Los resultados diarios y observaciones tienen claves explícitas.'),
('Saldo pendiente materializado','importe_base y conciliaciones activas','El pendiente se calcula sin doble mantenimiento.')],[5,5.5,6])
h('Tratamiento de datos históricos',2)
p('Un valor observado en una ejecución no tiene la misma semántica que el valor vigente de su objeto de origen. Por ejemplo, (pronostico_id, movimiento_id) determina importe_observado; movimiento_id por sí solo no lo determina, porque una ejecución posterior puede utilizar una versión distinta. Esta definición evita atribuir dependencias transitivas falsas a los snapshots. Los nombres originales de banco y de partes de factura son evidencias documentales inmutables, no duplicados mantenidos de un maestro actual.')

h('Modelo relacional final en FN3')
p(f'El modelo contiene {len(tables)} relaciones. PK identifica la clave primaria, UQ una clave alternativa y FK una referencia a la clave primaria indicada. NULL permite ausencia de valor; los demás atributos son obligatorios. Las claves compuestas se presentan completas. La siguiente notación es el MR íntegro y coincide con el diccionario y el SQL del anexo.')
for t in tables:
    h(t['name'].replace('_',' '),2)
    pk=[f['name'] for f in t['fields'] if 'PK' in f['key']]
    attrs=[]
    for f in t['fields']:
        flags=[]
        if 'PK' in f['key']:flags.append('PK')
        if 'FK ' in f['key']:flags.append('FK→'+f['key'].split('FK ')[1])
        if 'UQ' in f['key']:flags.append('UQ')
        attrs.append(f['name']+(' ['+', '.join(flags)+']' if flags else ''))
    p(t['name'].upper()+' ('+', '.join(attrs)+').')
    if t['unique']:p('Clave candidata adicional: ('+t['unique']+').')

h('Diccionario de datos y verificación por tabla')
p('Se utilizan BIGINT para identificadores, VARCHAR para códigos y textos acotados, NUMERIC(18,2) para dinero, DATE para fechas de negocio, TIMESTAMPTZ para eventos y UUID para idempotencia y reclamos. Ningún importe financiero utiliza coma flotante. Los nombres SQL se escriben sin tildes para facilitar su uso en PostgreSQL.')
for t in tables:
    h(t['name'].replace('_',' '),2)
    p(t['purpose'])
    grid(['Atributo','Tipo','Clave y nulabilidad','Descripción'],[(f['name'],f['type'],f['key'] or 'Obligatorio',f['desc']) for f in t['fields']],[4.4,3,3.4,5.7])
    pk=[f['name'] for f in t['fields'] if 'PK' in f['key']]
    non=[f['name'] for f in t['fields'] if 'PK' not in f['key']]
    dep='('+', '.join(pk)+') → '+(', '.join(non) if non else 'no hay atributos no clave')
    p('Dependencia funcional: '+dep+'.')
    if len(pk)>1:
        proof='Todos los atributos no clave describen la combinación completa, no un componente aislado.' if non else 'La relación contiene únicamente la clave compuesta; no existen dependencias parciales ni transitivas de atributos no clave.'
    else: proof='La clave primaria es simple; las claves alternativas declaradas también identifican una sola fila. Ningún atributo no clave determina otro atributo no clave bajo las reglas del dominio.'
    p('Verificación FN3: atributos atómicos. '+proof)
    if t['unique']:p('Unicidad adicional: ('+t['unique']+'). Esta combinación determina los atributos de la fila.')
    if t['checks']:p('Restricción de dominio: '+t['checks']+'.')
    if t['note']:p(t['note'])

h('Diseño físico y estrategia transaccional')
p('Las PK y UQ crean índices de búsqueda de identidad. Se agregan índices para FK y consultas frecuentes: movimiento(cuenta_id, fecha), obligacion(empresa_id, vencimiento), corte_cuenta(cuenta_id, fecha DESC), pronostico(empresa_id, fecha_corte), tarea(estado, disponible_en) y limite_solicitud(vence_en). La suma de conciliaciones no se resuelve con un CHECK por fila porque requiere consultar varias filas.')
h('Conciliación y concurrencia',2)
p('La operación de conciliación se ejecuta dentro de una transacción. Se bloquean la obligación y el movimiento con SELECT FOR UPDATE en un orden determinista; se comprueba la membresía, la pertenencia empresarial, el signo y los importes ya aplicados. Si la solicitud ya existe, se devuelve el registro anterior. Si no existe y hay cupo en ambos extremos, se inserta la conciliación y su auditoría. La reversión usa los mismos bloqueos. Así dos peticiones simultáneas no consumen el mismo saldo disponible.')
code('BEGIN;\nSELECT id FROM obligacion WHERE id = :obligacion FOR UPDATE;\nSELECT id FROM movimiento WHERE id = :movimiento FOR UPDATE;\n-- Validar empresa, signo, idempotencia y límites agregados.\n-- Insertar conciliacion y auditoria o revertir toda la operación.\nCOMMIT;')
h('Pertenencia e integridad entre tablas',2)
p('Las FK simples verifican existencia, pero no garantizan que todos los objetos sean de la misma empresa. Se requieren triggers o funciones transaccionales para movimiento y tercero; cuenta y conexión; conciliación con obligación y movimiento; factura con obligación; ocurrencia con revisión y obligación; evidencias y entradas con su empresa de origen; e importación de factura con documento. El usuario autor debe tener membresía al operar; el historial no se elimina si esa membresía se retira después.')
p('La conexión activa se valida bloqueando la fila empresa antes de comprobar otras conexiones del proveedor. Se usa la misma técnica para la unicidad empresarial de alias, ocurrencias y evaluaciones. La relación parte_factura se completa con un CONSTRAINT TRIGGER DEFERRABLE INITIALLY DEFERRED que, al COMMIT, exige un emisor y un receptor. Sobre registro_factura se exige la coincidencia exclusiva del NIT empresarial con una de esas partes; la comprobación también se aplica ante cambios de NIT o reasignación del documento.')
h('Seguridad y recuperación',2)
p('La aplicación debe filtrar toda consulta por membresía y empresa; una FK no es un mecanismo de autorización. Las contraseñas permanecen en hashes administrados por Django. No se guardan credenciales de acceso bancario en las tablas del dominio. Los archivos temporales y los parámetros finalizados se purgan, y los diagnósticos excluyen datos sensibles. Una política de filas en PostgreSQL puede reforzar el aislamiento si se configura y prueba para el rol de ejecución.')
p('El respaldo debe incluir esquema y datos con una herramienta PostgreSQL compatible, registrar fecha y checksum y restaurarse primero en un entorno aislado. Se comprueban claves, conteos y consultas de negocio antes de dar por recuperado el sistema. Este diseño no acredita una restauración remota ya realizada.')
h('Correspondencia con la implementación existente')
grid(['Modelo Django actual','Relaciones propuestas y cambio'],[
('Company CompanyMember y auth.User','empresa usuario membresia rol; se conserva la pertenencia por empresa.'),
('BankConsent y BankConnection','consentimiento alcance consentimiento_alcance conexion proveedor; se elimina empresa redundante en conexión.'),
('BankAccount','cuenta y corte_cuenta; se conserva historial de saldos observados.'),
('Merchant y MerchantAlias','tercero alias_tercero; empresa se deriva desde tercero.'),
('Transaction ClassificationRule ClassificationChange','movimiento categoria regla_clasificacion cambio_clasificacion; categorías mediante FK.'),
('ImportJob y BankSyncJob','importacion_movimiento sincronizacion; se mantienen resultados por intento.'),
('Invoice y InvoiceImport','factura registro_factura parte_factura importacion_factura y resultado_importacion_factura; data se expande y CUFE identifica el documento global.'),
('Obligation y Settlement','obligacion conciliacion; importe_base reemplaza el pendiente mutable y se deriva el saldo restante.'),
('RecurrenceReview RecurrenceOccurrence','revision_recurrencia evidencia_recurrencia ocurrencia_recurrencia; evidence se transforma en filas.'),
('ForecastRun','pronostico parametro_pronostico punto_pronostico y las tres tablas de entradas; evidence y result se descomponen.'),
('AlertEvaluation','evaluacion_alerta alerta factor_alerta; resultados asociados a la ejecución evaluada.'),
('AuditLog BackgroundTask RateLimitBucket','auditoria detalle_auditoria tarea parametro_tarea limite_solicitud; listas y objetos se separan.')],[6,10.5])
p('La migración debe crear catálogos, asignar categorías existentes a sus IDs, expandir los JSON de forma determinista y verificar conteos antes de retirar columnas. El importe base de cada obligación se recupera como pendiente actual más suma de conciliaciones activas; no se utiliza el total de la factura si existen abonos previos. Los cortes se inicializan con balance y balance_date actuales. Las alertas históricas sin vínculo directo a un pronóstico exigen reconstrucción verificable de sus entradas antes de completar la FK; no debe inventarse esa asociación.')

h('Consultas SQL de validación')
h('Pendiente de cobros y pagos',2)
code('CREATE VIEW pendiente_obligacion AS\nSELECT o.id, o.empresa_id, o.direccion, o.vencimiento,\n       o.cancelada, o.importe_base - COALESCE(SUM(\n         CASE WHEN c.revertida_en IS NULL THEN c.importe ELSE 0 END\n       ), 0) AS pendiente\nFROM obligacion o LEFT JOIN conciliacion c ON c.obligacion_id = o.id\nGROUP BY o.id;\n\nSELECT direccion, SUM(pendiente) AS total\nFROM pendiente_obligacion\nWHERE empresa_id = :empresa AND NOT cancelada\nGROUP BY direccion;')
p('Se conserva una fila por obligación y se consideran solo aplicaciones activas. La cancelación excluye la obligación de caja futura sin eliminar su historial.')
h('Saldo consolidado al mismo corte',2)
code('SELECT SUM(cc.saldo) AS saldo_cop\nFROM cuenta c JOIN corte_cuenta cc ON cc.cuenta_id = c.id\nWHERE c.empresa_id = :empresa AND cc.fecha = :fecha\nHAVING COUNT(*) = (SELECT COUNT(*) FROM cuenta\n                   WHERE empresa_id = :empresa);')
p('Si falta el corte de alguna cuenta, la consulta no devuelve un consolidado engañoso. No se suma el historial bancario como sustituto del saldo observado.')
h('Ingresos y egresos por categoría',2)
code('SELECT cat.nombre,\n SUM(CASE WHEN m.importe > 0 THEN m.importe ELSE 0 END) AS ingresos,\n SUM(CASE WHEN m.importe < 0 THEN -m.importe ELSE 0 END) AS egresos\nFROM movimiento m JOIN cuenta c ON c.id = m.cuenta_id\nJOIN categoria cat ON cat.id = m.categoria_id\nWHERE c.empresa_id = :empresa\n  AND m.fecha BETWEEN :desde AND :hasta\nGROUP BY cat.id, cat.nombre ORDER BY cat.nombre;')
h('Control de sobreaplicación y coherencia empresarial',2)
code('SELECT o.id\nFROM obligacion o JOIN conciliacion c ON c.obligacion_id = o.id\nWHERE c.revertida_en IS NULL\nGROUP BY o.id HAVING SUM(c.importe) > o.importe_base;\n\nSELECT c.id FROM conciliacion c\nJOIN obligacion o ON o.id = c.obligacion_id\nJOIN movimiento m ON m.id = c.movimiento_id\nJOIN cuenta a ON a.id = m.cuenta_id\nWHERE o.empresa_id <> a.empresa_id\n   OR (o.direccion = \'in\' AND m.importe <= 0)\n   OR (o.direccion = \'out\' AND m.importe >= 0);')
p('Ambas consultas deben devolver cero filas. También se agrupan las conciliaciones por movimiento para verificar que su suma activa no supere ABS(importe).')
h('Escenario ilustrativo y plan de pruebas')
p('Escenario de prueba con valores ilustrativos: una empresa tiene una cuenta con corte de COP 2 000 000; registra una obligación de pago por COP 600 000 y un egreso bancario de COP 200 000. Una conciliación activa por COP 200 000 deja un pendiente de COP 400 000. La proyección utiliza el corte real y solo el pendiente futuro, sin volver a descontar el egreso histórico. Si se revierte la conciliación, el pendiente regresa a COP 600 000 y la reversión queda auditada.')
tests=[('V01','Insertar dos membresías de igual empresa y usuario','La PK compuesta rechaza la segunda.'),('V02','Reimportar cuenta e ID externo ya registrados','No aparece otro movimiento; se cuenta como duplicado.'),('V03','Usar un tercero de otra empresa en un movimiento','La regla de pertenencia rechaza la operación.'),('V04','Sincronizar una conexión con consentimiento revocado','La operación se rechaza antes de crear movimientos.'),('V05','Abrir dos conexiones activas del mismo proveedor y empresa','La validación concurrente admite una sola.'),('V06','Aplicar COP 200 000 a obligación de COP 600 000','El pendiente calculado es COP 400 000.'),('V07','Repetir la misma solicitud de conciliación','Se recupera la conciliación original sin otra aplicación.'),('V08','Aplicar dos conciliaciones simultáneas que superen el cupo','El bloqueo impide la sobreaplicación.'),('V09','Revertir una conciliación ya registrada','Se conserva la fila y se restituye el pendiente.'),('V10','Registrar el mismo CUFE en una empresa','UQ rechaza el duplicado; otro intento puede referirlo.'),('V11','Confirmar una factura sin ambas partes','La restricción diferida rechaza el COMMIT.'),('V12','Cambiar un movimiento después de un pronóstico','Las entradas observadas y el resultado histórico permanecen iguales.'),('V13','Consultar consolidado con un corte faltante','No se devuelve un saldo consolidado incompleto.'),('V14','Borrar una entidad con evidencias relacionadas','Las FK restringen el borrado.'),('V15','Leer información con rol viewer o desde otra empresa','Solo se permite la lectura de la empresa autorizada; toda escritura se rechaza.')]
grid(['Caso','Acción','Resultado esperado'],tests,[1.5,7.5,7.5])
p('Estos son criterios de aceptación del diseño propuesto. Deben ejecutarse sobre una base aislada después de crear las migraciones y los triggers. La validación estructural del documento no acredita ejecución de estos casos ni comportamiento en producción.')
h('Conclusiones')
p(f'El diseño organiza Horizonte en {len(tables)} relaciones y separa identidad empresarial, fuentes financieras, movimientos, obligaciones y resultados analíticos. El MER expresa los vínculos del negocio y el MR identifica todas las PK, claves candidatas y FK necesarias para reconstruirlos.')
p('La normalización elimina grupos repetidos, dependencias parciales en asociaciones y dependencias transitivas de categorías, conexiones y alias. Los resultados y entradas históricas se almacenan como hechos de una ejecución, lo que preserva explicaciones aun cuando los datos vigentes cambien. La conciliación y las reglas entre empresas requieren control transaccional adicional a las restricciones declarativas.')
p('La adopción del modelo exige una migración controlada del esquema Django actual, validación de la pertenencia empresarial y pruebas de concurrencia. La base de datos resultante proporciona una estructura consistente para consultar caja real, pendientes y escenarios futuros sin confundir documentos con pagos realizados.')
h('Referencias del proyecto')
for tx in ['README.md. Plataforma de Inteligencia de Liquidez para Microempresas. Descripción, alcance, actores y reglas de negocio del repositorio.', 'SPECS.md. Especificaciones del proyecto Horizonte.', 'backend/apps/accounts/models.py. Empresas, membresías, auditoría, cola persistente y límites de solicitudes.', 'backend/apps/banking/models.py. Cuentas, consentimientos, conexiones, comercios, movimientos e importaciones.', 'backend/apps/classify/models.py. Reglas y correcciones de clasificación.', 'backend/apps/invoices/models.py y parser.py. Facturas, importaciones y estructura financiera extraída del XML.', 'backend/apps/forecast/models.py. Obligaciones, conciliaciones, recurrencias, alertas y ejecuciones de pronóstico.', 'docs/TECHNICAL_MANUAL.md y docs/IMPLEMENTATION_STATUS.md. Contexto técnico y separación entre alcance previsto y comportamiento verificado.', 'Proyecto/Plantilla.docx. Plantilla institucional de Universidad de Pamplona.', 'Proyecto/Ejemplos. Diseño de una base de datos para la gestión de la Banda Marcial de la Institución Educativa La Frontera y Proyecto BD2 Heladería. Referencias de estructura y presentación.']:
    p(tx)
p('Fecha de revisión de los archivos del proyecto: 15 de octubre de 2026. Las referencias de ejemplo orientan la presentación; las entidades y reglas financieras proceden del proyecto Horizonte.')

h('Anexo de definición física en PostgreSQL')
p('El siguiente DDL materializa las tablas, PK, FK, claves alternativas y CHECK locales del modelo final en el esquema horizonte_fn3. Se utiliza un esquema separado para diferenciar esta propuesta del esquema Django vigente. No se ejecuta contra la base del proyecto. Las reglas entre filas y entre empresas de la sección de integridad requieren implementar sus triggers antes de utilizar este esquema como sistema operativo.')
ddl=['CREATE SCHEMA IF NOT EXISTS horizonte_fn3;', 'SET search_path TO horizonte_fn3;']
for t in tables:
    lines=[];pks=[f['name'] for f in t['fields'] if 'PK' in f['key']]
    for f in t['fields']:
        is_id=f['name']=='id' and len(pks)==1
        line='  '+f['name']+' '+f['type']+(' GENERATED BY DEFAULT AS IDENTITY' if is_id else '')
        if 'NULL' not in f['key']:line+=' NOT NULL'
        if 'UQ' in f['key']:line+=' UNIQUE'
        lines.append(line)
    lines.append('  PRIMARY KEY ('+', '.join(pks)+')')
    for f in t['fields']:
        if 'FK ' in f['key']:
            target=f['key'].split('FK ')[1];tt=next(x for x in tables if x['name']==target)
            tp=[ff['name'] for ff in tt['fields'] if 'PK' in ff['key']]
            assert len(tp)==1,(target,tp)
            lines.append(f"  FOREIGN KEY ({f['name']}) REFERENCES {target}({tp[0]}) ON DELETE RESTRICT")
    if t['unique']:lines.append('  UNIQUE ('+t['unique']+')')
    if t['checks']:lines.append('  CHECK ('+t['checks']+')')
    stmt='CREATE TABLE '+t['name']+' (\n'+',\n'.join(lines)+'\n);'
    ddl.append(stmt)
    h(t['name'].replace('_',' '),2);code(stmt)
indexes=['CREATE INDEX ix_movimiento_cuenta_fecha ON movimiento(cuenta_id, fecha);', 'CREATE INDEX ix_obligacion_empresa_fecha ON obligacion(empresa_id, vencimiento);', 'CREATE INDEX ix_corte_cuenta_fecha ON corte_cuenta(cuenta_id, fecha DESC);', 'CREATE INDEX ix_pronostico_empresa_fecha ON pronostico(empresa_id, fecha_corte);', 'CREATE INDEX ix_tarea_disponible ON tarea(estado, disponible_en);', 'CREATE INDEX ix_limite_vence ON limite_solicitud(vence_en);']
h('Índices complementarios',2)
for sql in indexes:code(sql)
ddl+=indexes
(WORK/'modelo_fn3.sql').write_text('\n\n'.join(ddl),encoding='utf-8')

# Mark fields to refresh without rewriting the template furniture.
settings=d.settings.element
uf=settings.find(qn('w:updateFields'))
if uf is None:uf=OxmlElement('w:updateFields');settings.append(uf)
uf.set(qn('w:val'),'true')
d.core_properties.author='Adrian Perez Pacheco'
d.core_properties.last_modified_by='Adrian Perez Pacheco'
d.core_properties.title='Diseño de base de datos de Horizonte'
d.core_properties.subject='MER y modelo relacional normalizado a tercera forma normal'
d.core_properties.comments=''
d.save(OUT)
# python-docx may serialize preserve-only parts. Restore them exactly from reference.
editable={'word/document.xml','word/_rels/document.xml.rels','docProps/core.xml','word/settings.xml','[Content_Types].xml'}
with ZipFile(OUT) as fin: parts={n:fin.read(n) for n in fin.namelist()}
for n in baseline:
    if n not in editable:parts[n]=z.read(n)
with ZipFile(OUT,'w',ZIP_DEFLATED) as fout:
    for n,b in parts.items():fout.writestr(n,b)
with ZipFile(OUT) as check:
    changed=[n for n,v in baseline.items() if n in check.namelist() and sha256(check.read(n)).hexdigest()!=v]
    assert set(changed)<=editable,changed
assert sha256(REF.read_bytes()).hexdigest()==reference_hash
print(json.dumps({'output':str(OUT),'tables':len(tables),'foreign_keys':len(relations),'changed_parts':changed},ensure_ascii=False))

