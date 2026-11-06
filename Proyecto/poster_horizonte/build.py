from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import textwrap

ROOT=Path(__file__).resolve().parent
S=2
im=Image.new('RGB',(1588*S,2246*S),'#f2f6fb');d=ImageDraw.Draw(im)
NAVY='#09294d';INK='#173450';MUTED='#52677b';TEAL='#087f8c'
FONT=Path('C:/Windows/Fonts')
def font(sz,bold=False):return ImageFont.truetype(str(FONT/('arialbd.ttf' if bold else 'arial.ttf')),round(sz*S))
def rect(box,fill,outline=None,r=18,width=1):
 d.rounded_rectangle(tuple(round(v*S) for v in box),radius=r*S,fill=fill,outline=outline,width=width*S)
def text(x,y,s,size=26,fill=INK,bold=False):d.text((x*S,y*S),s,font=font(size,bold),fill=fill)
def lines(x,y,s,w,size=26,fill=INK,bold=False,leading=1.24):
 f=font(size,bold);yy=y
 for para in s.split('\n'):
  current=''
  for word in para.split():
   candidate=(current+' '+word).strip()
   if d.textlength(candidate,font=f)>w*S and current:
    text(x,yy,current,size,fill,bold);yy+=size*leading;current=word
   else:current=candidate
  if current:text(x,yy,current,size,fill,bold);yy+=size*leading
 return yy
def card(x,y,w,h,n,title,color):
 rect((x,y,x+w,y+h),'white','#cfdae5',18)
 rect((x,y,x+w,y+68),color,None,18)
 d.rectangle((x*S,(y+42)*S,(x+w)*S,(y+68)*S),fill=color)
 d.ellipse(((x+18)*S,(y+16)*S,(x+54)*S,(y+52)*S),fill='white')
 text(x+28,y+19,str(n),24,color,True);text(x+68,y+19,title,27,'white',True)
def arrow(points,color=TEAL):
 p=[(int(x*S),int(y*S)) for x,y in points];d.line(p,fill=color,width=4*S)
 x,y=points[-1];px,py=points[-2]
 if y>py:tri=[(x,y),(x-8,y-13),(x+8,y-13)]
 elif y<py:tri=[(x,y),(x-8,y+13),(x+8,y+13)]
 elif x>px:tri=[(x,y),(x-13,y-8),(x-13,y+8)]
 else:tri=[(x,y),(x+13,y-8),(x+13,y+8)]
 d.polygon([(int(a*S),int(b*S)) for a,b in tri],fill=color)
def node(x,y,w,h,title,body):
 rect((x,y,x+w,y+h),'#eaf4f7','#8cbac5',14,2)
 text(x+18,y+12,title,25,NAVY,True)
 lines(x+18,y+48,body,w-36,22,INK,leading=1.18)

# Cabecera institucional
d.rectangle((0,0,1588*S,298*S),fill=NAVY)
text(44,24,'UNIVERSIDAD DE PAMPLONA · SEDE VILLA DEL ROSARIO',27,'#c2dcea',True)
text(44,68,'HORIZONTE',74,'white',True)
text(44,158,'SaaS de inteligencia de liquidez para microempresas',35,'#84d4da',True)
text(44,215,'Estudiante: Adrian Perez Pacheco  |  Profesor: Miguel Eduardo Posada Haddad',24,'white')
text(44,252,'Ingeniería de Software II · Ingeniería de Sistemas · Facultad de Ingeniería y Arquitecturas',23,'#c2dcea')

L=44;LW=548;R=620;RW=924
card(L,326,LW,225,1,'Problema y usuarios','#cc4668')
lines(L+24,410,'La caja dispersa dificulta anticipar pagos y faltantes. Horizonte reúne movimientos y compromisos.',LW-48,26)
text(L+24,513,'Propietarios, contadores y usuarios de consulta.',21,MUTED)

card(L,573,LW,254,2,'Objetivo y alcance','#178763')
lines(L+24,655,'Apoyar decisiones de caja a 30, 60 y 90 días con saldos, cobros y pagos explicables. SaaS multiempresa para Villa del Rosario, Cúcuta y Norte de Santander.',LW-48,26)
text(L+24,789,'Solo lectura financiera: no transfiere dinero.',22,'#08724e',True)

card(L,849,LW,255,3,'Metodología de trabajo','#1385a9')
lines(L+24,930,'Scrum adaptado a un estudiante: Adrian asume producto, facilitación y desarrollo. Backlog, objetivos de sprint y revisión de incrementos con evidencia.',LW-48,26)
text(L+24,1062,'Sprints de dos semanas propuestos.',23,MUTED,True)

card(L,1126,LW,565,4,'Funciones del SaaS','#7253b6')
items=['Sesión, empresas y roles de acceso.', 'Ingresos y egresos manuales; reintentos sin duplicar movimientos.', 'Importación CSV/XLSX/XML y fuente bancaria simulada (Mock Bank).', 'Categorías, correcciones y reglas por empresa.', 'Cuentas por cobrar y pagar; conciliación de abonos.', 'Pagos mensuales y recurrencias.', 'Resumen, saldo histórico y alertas de déficit.']
yy=1208
for i in items:
 text(L+24,yy,'•',26,'#7253b6',True)
 yy=lines(L+48,yy,i,LW-72,25,leading=1.18)+14
assert yy<1685,yy

card(L,1713,LW,317,5,'Seguridad e integridad','#b78713')
lines(L+24,1795,'Membresías y permisos por empresa. Sesión Django + CSRF. Montos Decimal, deduplicación y auditoría de operaciones. Importar historial no vuelve a sumar el saldo del corte.',LW-48,26)
text(L+24,1985,'Datos sintéticos para el entorno académico.',22,MUTED,True)

card(R,326,RW,704,6,'Arquitectura técnica','#1565aa')
text(R+24,408,'MONOLITO MODULAR · ENTORNO LOCAL DOCKER',22,MUTED,True)
node(R+28,450,RW-56,104,'Cliente web','React + TypeScript + Vite · interfaz de operación y análisis')
arrow([(R+RW/2,554),(R+RW/2,591)])
text(R+RW/2+20,560,'HTTP / JSON + sesión',21,MUTED)
node(R+28,595,RW-56,138,'API Django REST Framework','accounts · banking · classify · invoices · forecast\nAutorización por empresa, validación y servicios financieros')
arrow([(R+240,733),(R+240,790)])
arrow([(R+694,733),(R+694,790)])
node(R+28,795,406,124,'PostgreSQL','Empresas, movimientos,\nobligaciones y auditoría')
node(R+468,795,428,80,'Redis · cola de trabajos','Despacho asíncrono')
arrow([(R+682,875),(R+682,908)])
node(R+468,912,428,80,'Celery · workers','Importación y procesamiento')
arrow([(R+468,951),(R+245,951),(R+245,920)])
text(R+30,969,'Persistencia y consultas mediante ORM',22,MUTED)

card(R,1052,RW,448,7,'Flujo de datos y motor de liquidez','#16897d')
steps=[('01  Capturar e importar','Manual, CSV/XLSX, XML UBL y Mock Bank.'),('02  Normalizar y conciliar','Clasificar, deduplicar y vincular cobros/pagos sin doble conteo.'),('03  Calcular y explicar','Saldo disponible + compromisos; proyección a 30/60/90 días.')]
yy=1134
for title,body in steps:
 text(R+28,yy,title,27,NAVY,True);yy=lines(R+28,yy+35,body,RW-56,25)+16
rect((R+24,yy,R+RW-24,yy+91),'#fff3d9',None,12)
lines(R+40,yy+12,'Modelo híbrido y P10/P50/P90 experimentales: falta validación independiente y calibración. No se presenta precisión predictiva demostrada.',RW-80,22,'#715209')

card(R,1522,RW,285,8,'Verificación y límites','#7650af')
text(R+28,1605,'245',54,NAVY,True);text(R+161,1611,'pruebas backend PostgreSQL aprobadas',25,NAVY,True)
text(R+161,1650,'de 247; 2 omitidas · registro local del 30/10/2026',22,MUTED)
lines(R+28,1697,'Frontend: 8 pruebas y build aprobados. Ruff/formato: 210 archivos. Falta ampliar aceptación con usuarios, seguridad, carga y disponibilidad. Estas pruebas no certifican producción.',RW-56,24)

card(R,1829,RW,201,9,'Aporte y siguiente paso','#bb8422')
lines(R+28,1911,'Unificar la caja y explicar faltantes con datos trazables. Siguiente paso: completar aceptación web y evaluar el pronóstico con microempresas y datos autorizados.',RW-56,26)

# Pie con trazabilidad y alcance
d.rectangle((0,2060*S,1588*S,2246*S),fill=NAVY)
text(44,2090,'Fuente: código y docs/IMPLEMENTATION_STATUS.md · corte técnico 30/10/2026',24,'white',True)
text(44,2130,'Repositorio: github.com/elcreado/Horizonte',25,'#a9d5e3')
lines(44,2172,'Prototipo académico SaaS · Presupuesto inicial 0 USD · Validación externa y despliegue actual pendientes de acreditar.',1500,22,'#c2dcea')
im.save(ROOT/'Horizonte_poster_tecnico.png',optimize=True)
preview=im.copy();preview.thumbnail((794,1123));preview.save(ROOT/'Horizonte_preview.jpg',quality=92)
print(ROOT/'Horizonte_poster_tecnico.png')
