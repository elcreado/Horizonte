from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from PIL import Image
import pypdfium2 as pdfium

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/pdf/horizonte-poster.pdf'
W,H=1191,1684
for name,file in [('Body','arial.ttf'),('Bold','arialbd.ttf')]:
    pdfmetrics.registerFont(TTFont(name,'C:/Windows/Fonts/'+file))
c=canvas.Canvas(str(OUT),pagesize=(W,H))
c.setTitle('Horizonte | Inteligencia de liquidez para microempresas')
GREEN='#173F35'; TEAL='#2A7D66'; INK='#213C36'; MUTED='#576B65'; PAPER='#F5F6F0'; GOLD='#B99148'; RED='#761D2B'
def box(x,y,w,h,color,r=0):
    c.setFillColor(HexColor(color)); c.roundRect(x,H-y-h,w,h,r,stroke=0,fill=1)
def text(s,x,y,size=18,font='Body',color=INK):
    c.setFillColor(HexColor(color)); c.setFont(font,size); c.drawString(x,H-y-size,s)
def para(s,x,y,w,size=17,color=INK,leading=None):
    st=ParagraphStyle('p',fontName='Body',fontSize=size,leading=leading or size*1.35,textColor=HexColor(color))
    p=Paragraph(s,st); _,h=p.wrap(w,800); p.drawOn(c,x,H-y-h); return h
def img(file,x,y,w,h):
    im=Image.open(file)
    if im.mode=='RGBA':
        bg=Image.new('RGBA',im.size,'white'); bg.alpha_composite(im); im=bg.convert('RGB')
    iw,ih=im.size; scale=min(w/iw,h/ih); dw,dh=iw*scale,ih*scale
    c.drawImage(ImageReader(im),x+(w-dw)/2,H-y-h+(h-dh)/2,dw,dh,mask='auto')
def heading(n,s,x,y):
    text(n,x,y,15,'Bold',TEAL); text(s,x+35,y-4,24,'Bold')
def arrow(x1,y1,x2,y2,color=TEAL):
    c.setStrokeColor(HexColor(color)); c.setFillColor(HexColor(color)); c.setLineWidth(2)
    c.line(x1,H-y1,x2,H-y2)
    p=c.beginPath(); p.moveTo(x2,H-y2); p.lineTo(x2-8,H-y2+4); p.lineTo(x2-8,H-y2-4); p.close(); c.drawPath(p,fill=1,stroke=0)

box(0,0,W,H,PAPER)
box(0,0,W,119,'#FFFFFF')
img('C:/Users/elcre/Pictures/escudounipamplona.png',44,17,64,84)
text('UNIVERSIDAD DE PAMPLONA',128,28,21,'Bold',RED)
text('Ingeniería de Software II  |  Póster académico',128,61,16,color=MUTED)
img('C:/Users/elcre/Pictures/logo_acreditacion_png.png',923,15,96,88)
img('C:/Users/elcre/Pictures/logo-equaa.png',1040,15,98,88)
box(0,119,W,5,RED)

box(0,124,W,239,GREEN)
text('HORIZONTE',46,143,67,'Bold','#FFFFFF')
text('Inteligencia de liquidez para microempresas',49,223,28,'Bold','#DDEBD5')
para('Una plataforma para reunir movimientos, cobros y pagos, visualizar la caja y anticipar posibles déficits antes de que comprometan la operación.',49,273,1090,21,'#FFFFFF',28)

heading('01','Propósito y experiencia de uso',46,389)
para('Transformar registros financieros dispersos en un panorama comprensible para apoyar la planeación y las decisiones de la microempresa.',46,428,1080,18)
# Actual interface captures, presented as devices.
box(51,499,787,330,'#DDE4DC',13); box(46,493,787,330,GREEN,13)
pc=Image.open(ROOT/'tmp/poster/pc.png'); pc.crop((0,0,pc.width,900)).save(ROOT/'tmp/poster/pc-wide.png')
img(ROOT/'tmp/poster/pc-wide.png',56,503,767,309)
box(391,823,95,20,GREEN,0); box(335,843,208,8,GREEN,4)
box(890,490,248,444,GREEN,23)
img(ROOT/'tmp/poster/mobile.png',900,504,228,416)
text('PC · Interfaz web adaptable',57,870,17,'Bold')
para('Capturas reales del inicio público, ejecutado en local. La tarjeta «Ejemplo» es ilustrativa.',57,899,760,14,MUTED)
text('Móvil',982,944,16,'Bold')

heading('02','Arquitectura de la solución',46,986)
para('Aplicación por capas: el cliente presenta, la API valida y la base de datos conserva el estado.',46,1023,1080,17)
nodes=[(46,1070,245,'PRESENTACIÓN','React + TypeScript','Vite · Recharts'),(331,1070,245,'LÓGICA Y API','Django + DRF','Sesión · reglas de negocio'),(616,1070,245,'PERSISTENCIA','PostgreSQL','Saldos · historial · auditoría')]
for x,y,w,k,a,b in nodes:
    box(x,y,w,113,'#FFFFFF',10); text(k,x+17,y+15,12,'Bold',TEAL); text(a,x+17,y+40,20,'Bold'); text(b,x+17,y+76,13,color=MUTED)
arrow(295,1127,325,1127); arrow(580,1127,610,1127)
box(893,1070,249,113,'#E4EBDD',10)
text('PROCESAMIENTO ASÍNCRONO',908,1085,11,'Bold',TEAL)
text('Worker + cola en BD',908,1111,18,'Bold')
text('Importaciones y tareas largas',908,1147,12,color=MUTED)
arrow(865,1127,887,1127)
para('<b>Alojamiento configurado:</b> Render sirve React y API bajo un mismo origen HTTPS; Supabase aloja PostgreSQL con TLS. El cliente Windows en Electron consume el mismo servidor.',46,1204,1096,16,leading=22)
text('Proyección de caja = saldo al corte + flujo residual estimado + cobros pendientes - pagos pendientes.',46,1254,13,'Bold',TEAL)

heading('03','Del dato a la anticipación',46,1280)
cards=[
 (46,1320,'1  Capturar y organizar','Registro manual e importación de movimientos CSV/XLSX y facturas XML. Categorías, cuentas y trazabilidad por empresa.'),
 (608,1320,'2  Entender y proyectar','Saldo al corte, compromisos y calendario. Historial con cobertura explícita y escenarios de caja a 30, 60 y 90 días.'),
 (46,1436,'3  Proteger la integridad','Roles por empresa, sesión HttpOnly y CSRF. Importes Decimal y transacciones para conservar centavos y evitar duplicidades.'),
 (608,1436,'4  Reconocer los límites','Prototipo académico: sin bancos reales, pagos ni transferencias. Pronósticos experimentales sujetos a la calidad y cobertura de los datos.')]
for x,y,t,b in cards:
    box(x,y,536,102,'#FFFFFF',9); text(t,x+17,y+12,19,'Bold'); para(b,x+17,y+42,502,15,leading=20)

box(46,1566,1096,64,GREEN,9)
text('CONTRIBUCIÓN',63,1578,12,'Bold','#DDEBD5')
para('Conectar la operación diaria con una visión futura de caja, haciendo visibles los supuestos y la procedencia de la información.',219,1579,901,16,'#FFFFFF',21)
text('Fuentes: código y manual técnico de Horizonte; actualización funcional del 30/10/2026.',46,1642,11,color=MUTED)
text('Universidad de Pamplona  ·  Desarrollo: El estudiante  ·  Noviembre de 2026',46,1660,10,color=MUTED)
c.showPage(); c.save()
pdf=pdfium.PdfDocument(str(OUT)); pdf[0].render(scale=1.1).to_pil().save(ROOT/'output/pdf/horizonte-poster.png')
print(OUT)
