from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from hashlib import sha256
import json
from docx import Document
from docx.shared import Pt,Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image,ImageDraw,ImageFont

WORK=Path(__file__).resolve().parent
SOURCE=Path('C:/Users/elcre/Desktop/Documentacion_BD_Horizonte_Adrian_Perez_Pacheco.docx')
OUT=WORK.parent/'Documentacion_BD_Horizonte_Resumen_Adrian_Perez_Pacheco.docx'
all_tables=json.loads((WORK/'schema.json').read_text(encoding='utf-8'))
names=['empresa','usuario','rol','membresia','cuenta','corte_cuenta','categoria','tercero','movimiento','obligacion','conciliacion','factura','parte_factura','registro_factura','factura_obligacion']
ts={t['name']:t for t in all_tables if t['name'] in names}
keep={'usuario':['id','username','password_hash','nombres','apellidos','email'],
      'cuenta':['id','empresa_id','nombre'],
      'movimiento':['id','cuenta_id','externo_id','fecha','importe','descripcion','tercero_id','categoria_id']}
for name,fields in keep.items():ts[name]['fields']=[f for f in ts[name]['fields'] if f['name'] in fields]
ts['cuenta']['purpose']='Identifica cada cuenta bancaria de una empresa.'
ts['usuario']['purpose']='Identifica a las personas que acceden al sistema.'
ts['movimiento']['purpose']='Registra ingresos y egresos bancarios sin duplicarlos.'
source_hash=sha256(SOURCE.read_bytes()).hexdigest()
z=ZipFile(SOURCE);baseline={n:sha256(z.read(n)).hexdigest() for n in z.namelist()}
d=Document(SOURCE);body=d._element.body
for e in list(body)[2:]:
    if e.tag!=qn('w:sectPr'):body.remove(e)
# Keep the institutional cover and replace its subtitle in both representations.
for t in body.xpath('.//w:t'):
    if t.text=='Diseño relacional normalizado a FN3':t.text='Diseño de base de datos en FN3'

def p(text):
    x=d.add_paragraph(text);return x
def h(text,level=1):return d.add_paragraph(text,'Heading '+str(level))
def page():d.add_page_break()
def grid(headers,rows,widths):
    d.paragraphs[-1].paragraph_format.keep_with_next=True
    t=d.add_table(rows=1,cols=len(headers));t.autofit=False
    for c,w in zip(t.columns,widths):c.width=Cm(w)
    for c,txt in zip(t.rows[0].cells,headers):c.text=txt
    for row in rows:
        for c,txt in zip(t.add_row().cells,row):c.text=str(txt)
    for i,row in enumerate(t.rows):
        pr=row._tr.get_or_add_trPr();pr.append(OxmlElement('w:cantSplit'))
        if i==0:pr.append(OxmlElement('w:tblHeader'))
        for c,w in zip(row.cells,widths):
            c.width=Cm(w);cp=c._tc.get_or_add_tcPr();m=OxmlElement('w:tcMar')
            for side in ['top','left','bottom','right']:
                e=OxmlElement('w:'+side);e.set(qn('w:w'),'65');e.set(qn('w:type'),'dxa');m.append(e)
            cp.append(m);sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'E9E9E9' if i==0 else 'FFFFFF');cp.append(sh)
            for pp in c.paragraphs:
                pp.alignment=WD_ALIGN_PARAGRAPH.LEFT
                pp.paragraph_format.space_before=Pt(0);pp.paragraph_format.space_after=Pt(1);pp.paragraph_format.line_spacing=1
                pp.paragraph_format.keep_with_next=i<2
                for r in pp.runs:r.font.name='Arial';r.font.size=Pt(9.5);r.bold=i==0
    borders=OxmlElement('w:tblBorders')
    for side in ['top','left','bottom','right','insideH','insideV']:
        e=OxmlElement('w:'+side);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');borders.append(e)
    t._tbl.tblPr.append(borders)
    return t
def fig(path):
    x=d.add_paragraph();x.alignment=WD_ALIGN_PARAGRAPH.CENTER;x.add_run().add_picture(str(path),width=Cm(16.4))
def small(text):
    x=p(text)
    x.paragraph_format.space_before=Pt(3);x.paragraph_format.space_after=Pt(3)
    for r in x.runs:r.font.size=Pt(9.5)
    return x

# Page 2
h('Introducción y planteamiento del problema')
p('Horizonte es una plataforma de inteligencia de liquidez para microempresas. Su base de datos integra cuentas bancarias, movimientos, facturas y obligaciones para consultar el dinero disponible y los cobros o pagos pendientes. Este trabajo presenta el diseño de su núcleo financiero mediante un modelo entidad relación, un modelo relacional y la normalización hasta tercera forma normal o FN3.')
h('Problema',2)
p('La información financiera puede encontrarse dispersa entre extractos bancarios, facturas y archivos de cálculo. Esta separación dificulta identificar movimientos duplicados, conocer las obligaciones pendientes y relacionar un pago con su documento de origen. Si los mismos datos se repiten en varios registros, una modificación puede producir inconsistencias.')
p('También es necesario diferenciar una factura de un movimiento real de dinero. Emitir una factura no significa haber recibido su valor; el cobro o pago se reconoce al relacionar la obligación con un movimiento bancario mediante una conciliación.')
h('Objetivo general',2)
p('Diseñar una base de datos relacional normalizada hasta FN3 que permita organizar y consultar la información financiera básica de las microempresas que utilizan Horizonte.')
h('Objetivos específicos',2)
for text in ['Identificar las entidades, atributos y relaciones del núcleo financiero.', 'Definir claves primarias, claves foráneas y restricciones de integridad.', 'Representar el MER y transformarlo en un modelo relacional.', 'Eliminar grupos repetidos y dependencias parciales y transitivas.', 'Explicar la relación entre facturas, obligaciones y movimientos conciliados.']:p('• '+text)
h('Justificación',2)
p('El diseño relacional centraliza los datos y permite consultarlos con SQL. La normalización reduce redundancias y las claves foráneas evitan referencias inexistentes. Esto facilita mantener información consistente sobre saldos, ingresos, egresos y compromisos de pago.')

# Page 3
page();h('Alcance y entidades del sistema')
p('El diseño se concentra en la gestión de empresas y usuarios, cuentas y saldos, movimientos, categorías, facturas, obligaciones y conciliaciones. Se trabaja con pesos colombianos COP. La integración bancaria automática, los modelos predictivos, la auditoría técnica y las tareas en segundo plano quedan fuera de este alcance académico.')
grid(['Entidad','Función principal'],[(n,ts[n]['purpose']) for n in names],[4.9,11.6])
h('Requerimientos principales',2)
for text in ['Administrar empresas y sus usuarios con roles de propietario, contador y consulta.', 'Registrar cuentas, cortes de saldo y movimientos de ingreso o egreso.', 'Clasificar movimientos por categoría y asociarlos a un tercero cuando se conozca.', 'Registrar facturas, sus partes y su incorporación en cada empresa.', 'Gestionar obligaciones y conciliar sus abonos parciales o totales.']:p('• '+text)
small('El modelo es una propuesta del núcleo de datos de Horizonte; su adopción requiere ajustar las migraciones del esquema implementado.')

# Pages 4 and 5: every FK shown as a relationship segment.
edges=[]
for name in names:
    t=ts[name];pk=[f['name'] for f in t['fields'] if 'PK' in f['key']]
    for f in t['fields']:
        if 'FK ' in f['key']:
            parent=f['key'].split('FK ')[1]
            maximum='0..1' if 'UQ' in f['key'] or ('PK' in f['key'] and len(pk)==1) else '0..N'
            if name=='parte_factura':maximum='2'
            edges.append((parent,name,'0..1' if 'NULL' in f['key'] else '1',maximum,f['name']))
assert len(edges)==18,len(edges)
def ft(n,b=False):return ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf' if b else 'C:/Windows/Fonts/arial.ttf',n)
def diagram(batch,num):
    im=Image.new('RGB',(1600,1260),'white');dr=ImageDraw.Draw(im)
    for i,(parent,child,a,b,field) in enumerate(batch):
        y=15+i*137
        for x,n in [(12,parent),(1080,child)]:
            dr.rounded_rectangle((x,y,x+507,y+90),radius=8,fill='#F2F2F2',outline='black',width=2)
            label=n.replace('_',' ').upper();fs=26
            while dr.textlength(label,font=ft(fs,True))>485:fs-=1
            dr.text((x+253,y+27),label,font=ft(fs,True),fill='black',anchor='mm')
            pk=', '.join(f['name'] for f in ts[n]['fields'] if 'PK' in f['key'])
            dr.text((x+253,y+64),'PK '+pk,font=ft(20),fill='black',anchor='mm')
        dr.line((519,y+46,1080,y+46),fill='black',width=2)
        dr.text((570,y+70),a,font=ft(26,True),fill='black',anchor='mm')
        dr.text((1025,y+70),b,font=ft(26,True),fill='black',anchor='mm')
        fs=23
        while dr.textlength(field,font=ft(fs))>500:fs-=1
        dr.text((800,y+21),field,font=ft(fs),fill='black',anchor='mm')
    path=WORK/f'mer-resumen-{num}.png';im.save(path);return path
for part in range(2):
    page();h('Modelo entidad relación MER' if part==0 else 'Relaciones de facturación y conciliación')
    p('Cada rectángulo representa una entidad. Los segmentos muestran sus vínculos y cardinalidades; las entidades repetidas son la misma entidad. El atributo sobre cada línea indica cómo se relacionan los registros.' if part==0 else 'Las relaciones completan el modelo del núcleo financiero. La conciliación resuelve el vínculo entre movimientos y obligaciones, mientras registro_factura permite que una empresa incorpore un documento sin duplicar su cabecera fiscal.')
    fig(diagram(edges[part*9:(part+1)*9],part+1))
    small('Lectura: 1 significa exactamente un registro, 0..1 una relación opcional y 0..N cero o muchos registros. Una factura debe tener dos partes: emisor y receptor.' if part==0 else 'La pareja empresa y factura es única. Un registro empresarial puede vincularse a una obligación y cada obligación puede vincularse a un solo registro de factura.')
    if part==0:
        h('Relaciones muchos a muchos',2)
        p('Una empresa puede tener varios usuarios y un usuario participar en varias empresas; membresia resuelve esta relación. Un movimiento puede aplicarse a varias obligaciones y una obligación recibir varios abonos; conciliacion registra cada aplicación.')

# Pages 6-8: compact MR and dictionary for all fifteen tables.
for block in range(3):
    if block==0:page()
    h(['Modelo relacional y diccionario de datos','Movimientos y obligaciones','Facturación y conciliación'][block])
    if block==0:
        small('PK identifica la clave primaria; FK referencia la PK de la entidad indicada; UQ indica unicidad; NULL permite ausencia de valor. Los demás atributos son obligatorios. Las PK compuestas se forman con todos los campos marcados PK. Las tablas usan tipos de PostgreSQL.')
    for name in names[block*5:(block+1)*5]:
        t=ts[name];x=h(name.replace('_',' '),2)
        x.paragraph_format.space_before=Pt(7);x.paragraph_format.space_after=Pt(3)
        small(t['purpose'])
        grid(['Campo','Tipo de dato','Clave y referencia'],[(f['name'],f['type'],f['key'] or 'Obligatorio') for f in t['fields']],[5.6,4.3,6.6])
        if t['unique']:small('UQ adicional: ('+t['unique']+').')
    if block==0:small('password_hash conserva una contraseña protegida por el mecanismo de autenticación; nunca se guarda la contraseña en texto plano.')
    if block==1:small('Un importe positivo indica ingreso y uno negativo egreso. corte_cuenta guarda el saldo observado por fecha. El pendiente de una obligación se calcula restando las conciliaciones activas a importe_base.')
    if block==2:small('CUFE es único globalmente. registro_factura separa la incorporación del documento por empresa. Los nombres y NIT de parte_factura conservan los valores históricos declarados en el XML.')

# Page 9
page();h('Normalización hasta tercera forma normal')
h('Primera forma normal FN1',2)
p('Cada celda contiene un valor atómico y cada fila representa un hecho. Los movimientos de una cuenta se almacenan en filas independientes; los usuarios de una empresa se relacionan mediante membresia. Las partes de una factura se registran como dos filas, sin listas de nombres o documentos dentro de una celda.')
h('Segunda forma normal FN2',2)
p('Cada atributo no clave depende de la clave completa. En membresia la clave es (empresa_id, usuario_id) y el rol corresponde a esa combinación. El nombre del usuario se conserva en usuario, porque no depende de la empresa. En corte_cuenta, saldo depende de la cuenta y de la fecha, no de uno de esos atributos por separado.')
h('Tercera forma normal FN3',2)
p('Se eliminan dependencias transitivas entre atributos no clave. El nombre de la categoría se almacena en categoria y el movimiento guarda su FK. Los datos descriptivos de la empresa no se repiten en cuenta ni movimiento; el movimiento obtiene la empresa a través de su cuenta. Los nombres de los roles se almacenan solamente en rol.')
grid(['Grupo de tablas','Dependencia funcional y verificación'],[
('empresa usuario rol categoria tercero','La PK determina los atributos descriptivos. Los identificadores o nombres declarados UQ también son claves candidatas.'),
('membresia corte_cuenta parte_factura','Los atributos no clave dependen de la combinación completa de la PK. No se repiten datos descriptivos de sus entidades relacionadas.'),
('cuenta movimiento obligacion conciliacion','Cada hecho tiene identidad propia y referencia a sus entidades por FK. Las claves naturales de movimiento y obligacion se mantienen mediante UQ.'),
('factura registro_factura factura_obligacion','CUFE determina la cabecera global. La asociación empresa factura se guarda aparte. factura_obligacion contiene dos claves candidatas, sin repetir empresa o dirección.')],[5.1,11.4])
h('Ejemplo de eliminación de redundancia',2)
p('Una tabla con movimiento_id, categoria_id y nombre_categoria mantendría la dependencia movimiento_id → categoria_id → nombre_categoria. Al separar CATEGORIA(id, nombre) y conservar solo categoria_id en MOVIMIENTO, el nombre se modifica en un único lugar. La unión mediante FK permite recuperar la misma información sin repetirla.')
p('En las 15 tablas del modelo, bajo estas reglas de negocio, los atributos son atómicos, no existen dependencias parciales de atributos no clave y los atributos descriptivos dependen de claves candidatas. Los valores históricos declarados por una factura no se sustituyen por el nombre actual de sus partes.')

# Page 10
page();h('Reglas de integridad y ejemplo de uso')
grid(['Regla','Aplicación'],[
('Identidad y unicidad','No se repiten NIT de empresa, username, CUFE, membresías ni la pareja cuenta e identificador externo de un movimiento.'),
('Pertenencia empresarial','El tercero, la cuenta, la obligación y el registro de factura de una operación deben pertenecer a la misma empresa.'),
('Conciliación','El importe aplicado debe ser positivo y no superar el pendiente de la obligación ni el valor disponible del movimiento. El signo debe corresponder a cobro o pago.'),
('Facturación','Cada factura tiene un emisor y un receptor. La empresa que la registra debe coincidir con una de esas partes.'),
('Trazabilidad','Revertir una conciliación registra revertida_en; los registros relacionados se conservan y las FK restringen el borrado.')],[4,12.5])
h('Ejemplo de conciliación',2)
p('Una empresa tiene una obligación de pago de COP 600 000. Se registra un egreso bancario por COP 200 000 y se concilia con esa obligación. El pendiente queda en COP 400 000. Si se revierte la conciliación, el pendiente vuelve a COP 600 000. La factura respalda el documento comercial; el movimiento demuestra la salida de dinero.')
p('Pendiente = importe base − suma de conciliaciones activas. La operación debe ejecutarse dentro de una transacción, verificando empresa e importes antes de confirmar el abono. Una solicitud repetida se reconoce por la combinación obligacion_id y solicitud_id, sin aplicar dos veces el mismo importe.')
h('Conclusiones',2)
p('El modelo propuesto reúne los datos esenciales de Horizonte en 15 tablas relacionadas. El MER muestra los vínculos del negocio y el modelo relacional define atributos, tipos y claves. La normalización hasta FN3 reduce la repetición de datos y facilita mantener información consistente.')
p('La separación entre facturas, obligaciones y movimientos permite distinguir el documento comercial, el compromiso esperado y el dinero efectivamente recibido o pagado. La conciliación los conecta y permite consultar los saldos pendientes de cada empresa.')
h('Referencias',2)
small('Horizonte. README.md y SPECS.md: descripción y alcance del proyecto. Modelos Django de los módulos accounts, banking, invoices y forecast: entidades y reglas de información financiera. Documentación de base de datos de Horizonte: desarrollo completo del diseño. Plantilla institucional de la Universidad de Pamplona y ejemplos proporcionados para la presentación.')

d.core_properties.author='Adrian Perez Pacheco';d.core_properties.last_modified_by='Adrian Perez Pacheco';d.core_properties.title='Base de datos de Horizonte';d.core_properties.subject='Modelo académico del núcleo financiero en FN3'
d.save(OUT)
editable={'word/document.xml','word/_rels/document.xml.rels','docProps/core.xml','[Content_Types].xml'}
with ZipFile(OUT) as current:parts={n:current.read(n) for n in current.namelist()}
for n in baseline:
    if n not in editable:parts[n]=z.read(n)
with ZipFile(OUT,'w',ZIP_DEFLATED) as final:
    for n,data in parts.items():final.writestr(n,data)
with ZipFile(OUT) as final:
    assert all(sha256(final.read(n)).hexdigest()==v for n,v in baseline.items() if n not in editable)
assert sha256(SOURCE.read_bytes()).hexdigest()==source_hash
(WORK/'brief-schema.json').write_text(json.dumps(list(ts.values()),ensure_ascii=False,indent=2),encoding='utf-8')
(WORK/'artifact-brief.md').write_text('Referencia '+str(SOURCE)+'\nSHA256 '+source_hash+'\nSe conserva portada, sección, estilos, numeración, encabezados y pies del original. Se reemplaza el cuerpo por diez páginas planificadas, con quince tablas del núcleo financiero. Se eliminan SQL extenso, infraestructura, pronósticos y detalles operativos conforme a la solicitud. Se preservan los elementos institucionales y la tipografía de la plantilla.\n',encoding='utf-8')
print(OUT)
