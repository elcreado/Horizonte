from pathlib import Path
from docx import Document
from docx.shared import Cm,Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
w=Path('Proyecto'); src=w/'Documentacion_BD_Horizonte_Resumen_Adrian_Perez_Pacheco.docx';d=Document(src)
body=d._element.body; els=list(body)
text=lambda e: ''.join(e.itertext())
start=next(i for i,e in enumerate(els) if e.tag==qn('w:p') and ''.join(e.xpath('.//w:t/text()'))=='Modelo entidad relación MER')
end=next(i for i,e in enumerate(els) if e.tag==qn('w:p') and ''.join(e.xpath('.//w:t/text()'))=='Modelo relacional y diccionario de datos')
# Keep the leading and trailing page breaks, replacing the two previous diagram pages.
while start>0 and not ''.join(els[start-1].xpath('.//w:t/text()')) and not els[start-1].xpath('.//w:br'): start-=1
for e in els[start:end-1]:body.remove(e)
anchor=els[end]
new=[]
def add(t='',style=None):
 p=d.add_paragraph(t,style);new.append(p._p);p.paragraph_format.space_after=Pt(5);return p
def pic(label,pattern):
 add(label,'Heading 2');p=add();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
 path=next((w/'Modelos_Horizonte_StarUML'/'jpg').glob(pattern));p.add_run().add_picture(str(path),width=Cm(16.4))
def page():
 p=d.add_paragraph();p.add_run().add_break(__import__('docx').enum.text.WD_BREAK.PAGE);new.append(p._p)
add('Modelos de datos en StarUML','Heading 1')
add('El MER presenta las entidades y sus cardinalidades. El MR incorpora atributos, tipos de datos y claves del modelo normalizado en FN3. Las vistas de detalle amplían las relaciones del modelo general.')
pic('Modelo entidad relación general','01*General*')
pic('Modelo relacional general','02*General*')
add('Leyenda: PK clave primaria; FK clave foránea; U unicidad; N permite nulo. Círculo: opcional; barra: uno; pata de cuervo: varios. Línea continua: relación identificadora; discontinua: no identificadora.')
page();add('Relaciones de acceso y movimientos','Heading 1')
pic('Acceso empresarial','02*Acceso*')
pic('Cuentas y movimientos','02*Cuentas*')
add('Membresía relaciona empresas, usuarios y roles. Cada cuenta pertenece a una empresa y reúne sus cortes de saldo y movimientos. El tercero es opcional en el movimiento; la categoría clasifica la operación.')
page();add('Relaciones de facturación y conciliación','Heading 1')
pic('Facturas y obligaciones','02*Facturas*')
pic('Conciliación de abonos','02*Conciliacion*')
add('Cada factura tiene dos partes: emisor y receptor. Su registro empresarial se vincula a una obligación. La conciliación relaciona movimientos con obligaciones y registra cada abono aplicado por un usuario. Las reglas de igual empresa y límites de importe se verifican adicionalmente.')
# move new nodes before the preserved break preceding the dictionary
for e in new:body.remove(e)
for e in new:els[end-1].addprevious(e)
out=w/'Documentacion_BD_Horizonte_Resumen_StarUML_Adrian_Perez_Pacheco.docx';d.save(out);print(out.resolve())
