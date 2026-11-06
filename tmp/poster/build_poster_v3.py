from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from PIL import Image
import pypdfium2 as pdfium
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/pdf/horizonte-poster-v3.pdf'
W,H=1191,1684
for name,file in [('Body','arial.ttf'),('Bold','arialbd.ttf')]:
    pdfmetrics.registerFont(TTFont(name,'C:/Windows/Fonts/'+file))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='Bold')
c=canvas.Canvas(str(OUT),pagesize=(W,H))
c.setTitle('Horizonte | Póster académico · Dashboard y arquitectura')
GREEN='#173F35'; TEAL='#2A7D66'; INK='#213C36'; MUTED='#566960'; PAPER='#EDF2EF'; GOLD='#B99148'; LINE='#D5E0D9'
def box(x,y,w,h,color,r=0,stroke=None):
    c.setFillColor(HexColor(color)); c.setStrokeColor(HexColor(stroke or color)); c.setLineWidth(.8)
    c.roundRect(x,H-y-h,w,h,r,stroke=int(bool(stroke)),fill=1)
def text(s,x,y,size=17,font='Body',color=INK):
    c.setFillColor(HexColor(color)); c.setFont(font,size); c.drawString(x,H-y-size,s)
def para(s,x,y,w,size=16,color=INK,leading=None,maxh=None):
    st=ParagraphStyle('p',fontName='Body',fontSize=size,leading=leading or size*1.32,textColor=HexColor(color))
    p=Paragraph(s,st); _,h=p.wrap(w,900)
    if maxh is not None and h>maxh: raise ValueError(f'Text exceeds box: {h}>{maxh}: {s[:60]}')
    p.drawOn(c,x,H-y-h); return h
def img(file,x,y,w,h,trim=False):
    im=Image.open(file)
    if trim and im.mode=='RGBA': im=im.crop(im.getchannel('A').getbbox())
    iw,ih=im.size; scale=min(w/iw,h/ih); dw,dh=iw*scale,ih*scale
    c.drawImage(ImageReader(im),x+(w-dw)/2,H-y-h+(h-dh)/2,dw,dh,mask='auto')
def panel(n,title,x,y,w,h,accent=TEAL):
    box(x+2,y+3,w,h,'#DFE7E1',12); box(x,y,w,h,'#FFFFFF',12,LINE)
    box(x,y,w,43,'#E4EEE7',12)
    box(x,y+27,w,16,'#E4EEE7')
    c.setFillColor(HexColor(accent)); c.circle(x+24,H-y-21,14,fill=1,stroke=0)
    text(str(n),x+19,y+10,17,'Bold','#FFFFFF')
    text(title,x+47,y+9,21,'Bold',GREEN)
def bullet(s,x,y,w,size=16,color=TEAL):
    c.setFillColor(HexColor(color)); c.circle(x+3,H-y-9,3,stroke=0,fill=1)
    return para(s,x+15,y,w-15,size)
def down(x,y):
    c.setStrokeColor(HexColor(TEAL)); c.setLineWidth(1.8); c.line(x,H-y,x,H-y-11)
    p=c.beginPath();p.moveTo(x,H-y-13);p.lineTo(x-4,H-y-8);p.lineTo(x+4,H-y-8);p.close();c.setFillColor(HexColor(TEAL));c.drawPath(p,fill=1,stroke=0)

box(0,0,W,H,PAPER)
# Header: product identity and original institutional assets.
box(0,0,W,243,'#FFFFFF')
text('UNIVERSIDAD DE PAMPLONA',38,20,19,'Bold',GREEN)
img(ROOT/'output/assets/horizonte-logo.png',38,58,563,95,trim=True)
text('Inteligencia de liquidez para microempresas',39,170,24,'Bold',GREEN)
text('Proyecto académico de Ingeniería de Software II',40,209,16,color=MUTED)
box(820,27,334,167,'#F5F7F2',12)
img('C:/Users/elcre/Pictures/escudounipamplona.png',842,39,69,101)
img('C:/Users/elcre/Pictures/logo_acreditacion_png.png',934,43,89,93)
img('C:/Users/elcre/Pictures/logo-equaa.png',1042,43,91,93)
text('Desarrollo: Adrian Perez Pacheco',842,158,16,'Bold',GREEN)
box(0,243,W,7,TEAL)
L=37; LW=422; R=482; RW=672

panel(1,'Planteamiento del problema',L,272,LW,170)
para('Los registros dispersos de ingresos, egresos y compromisos dificultan conocer la <b>disponibilidad de caja</b>. Sin una visión temporal, la microempresa puede detectar tarde que los pagos superarán el dinero disponible.',L+17,329,LW-34,16,maxh=108)

panel(2,'Objetivos',L,456,LW,218)
box(L+15,511,LW-30,57,'#F0F6F0',6)
para('<b>General:</b> apoyar la planeación de liquidez mediante una visión integrada de la caja.',L+26,520,LW-52,16,maxh=45)
y=581
for s in ['Centralizar movimientos, saldos y compromisos.','Proyectar escenarios a <b>30, 60 y 90 días</b>.','Mostrar déficits, supuestos y calidad del historial.']:
    h=bullet(s,L+19,y,LW-38,15.5); y+=h+9

panel(3,'Funciones principales',L,688,LW,218)
para('<b>Captura actual:</b> movimientos manuales, CSV/XLSX y facturas XML.',L+18,746,LW-36,15,maxh=42)
box(L+15,792,LW-30,58,'#FAF3E4',6)
para('<b>Open Banking (alcance previsto):</b> registro automático de transacciones. <b>Aún no implementado.</b>',L+24,801,LW-48,14,leading=18,maxh=43)
para('<b>Operación:</b> cobros, pagos y calendario.',L+18,860,LW-36,14.5,maxh=21)
para('<b>Análisis:</b> historial, categorías y alertas.',L+18,884,LW-36,14.5,maxh=21)

panel(4,'Arquitectura del software',L,920,LW,348)
text('Aplicación por capas · API REST · HTTPS',L+17,973,14,'Bold',TEAL)
for y,t,s in [
    (1001,'1  Presentación','React + TypeScript · Vite · Recharts'),
    (1057,'2  API y servicios de negocio','Django + DRF · sesión y reglas financieras'),
    (1113,'3  Persistencia','PostgreSQL · dominio, auditoría y cola')]:
    box(L+17,y,LW-34,45,'#F0F5F1',6,LINE)
    text(t,L+28,y+5,15,'Bold');text(s,L+28,y+25,12.5,color=MUTED)
    if y<1113:down(L+LW/2,y+45)
box(L+17,1172,LW-34,39,'#FAF3E4',6)
para('<b>Worker + cola en BD:</b> importaciones fuera de la petición HTTP.',L+27,1178,LW-54,13,leading=15,maxh=31)
para('<b>Despliegue:</b> Render + PostgreSQL en Supabase.<br/><b>Cliente adicional:</b> Electron para Windows, en línea.',L+18,1222,LW-36,13.5,maxh=39)

panel(5,'Solución desarrollada: dashboard',R,272,RW,996)
text('Vista de PC · Resumen financiero y trayectoria de caja',R+18,327,16,'Bold')
box(R+17,357,RW-34,475,GREEN,10)
img(ROOT/'tmp/poster/dashboard-pc.png',R+25,365,RW-50,459)
text('Captura de la aplicación en ejecución · empresa sintética de demostración',R+19,839,12.5,color=MUTED)
# A real mobile viewport focused on the deficit and chart.
box(R+17,873,193,377,GREEN,19)
img(ROOT/'tmp/poster/dashboard-mobile-focus.png',R+26,883,175,357)
text('Móvil · vista de análisis',R+228,875,19,'Bold')
para('La misma interfaz adapta las tarjetas y el gráfico al ancho del dispositivo.',R+228,909,420,16,maxh=47)
text('¿Cómo se interpreta?',R+228,981,19,'Bold',TEAL)
for y,n,t,s in [
    (1022,'1','Punto de partida','Saldo declarado y fecha de corte.'),
    (1087,'2','Flujos futuros','Compromisos y flujo residual estimado.'),
    (1152,'3','Señal de atención','Primer día con saldo proyectado negativo.')]:
    c.setFillColor(HexColor(TEAL));c.circle(R+241,H-y-13,12,fill=1,stroke=0)
    text(n,R+237,y+3,14,'Bold','#FFFFFF')
    text(t,R+263,y,17,'Bold');para(s,R+263,y+25,382,15,maxh=42)
para('Datos de ejemplo: saldo $8,5 millones COP.<br/>La proyección es orientativa; no es una garantía.',R+228,1222,417,12.5,MUTED,maxh=34)

panel(6,'Calidad y validación',L,1283,LW,277)
for y,t,s in [
    (1338,'Integridad financiera','Importes Decimal, transacciones y controles para evitar duplicidades.'),
    (1400,'Seguridad por empresa','Roles, sesión HttpOnly y protección CSRF; finanzas con acceso autenticado.'),
    (1462,'Evidencia registrada · 30/10/2026','PostgreSQL: 245 pruebas aprobadas y 2 omitidas. Frontend: 8 pruebas y build correctos.')]:
    text(t,L+18,y,16,'Bold',TEAL);para(s,L+18,y+24,LW-36,14.5,maxh=57)
text('La validación predictiva y la aceptación amplia siguen pendientes.',L+18,1536,11.5,color=MUTED)

panel(7,'Conclusiones y alcance',R,1283,RW,155)
para('Horizonte convierte la operación diaria en un panorama de caja con <b>trazabilidad y supuestos visibles</b>. Su arquitectura separa la interfaz, las reglas financieras y la persistencia para facilitar su evolución.',R+18,1337,RW-36,16,maxh=70)
para('<b>Prototipo académico:</b> sin bancos reales, pagos ni transferencias; pronósticos experimentales.',R+18,1404,RW-36,13.5,MUTED,maxh=28)

panel(8,'Fuentes del proyecto',R,1452,RW,108)
para('1. Manual técnico vigente: componentes, seguridad y operación.<br/>2. Actualización funcional del 30/10/2026: saldo histórico y pruebas.<br/>3. Código fuente: dashboard, servicios financieros y cola de trabajos.',R+18,1504,RW-36,13.5,maxh=55)

box(0,1593,W,91,GREEN)
text('HORIZONTE',38,1614,22,'Bold','#FFFFFF')
text('Ver la caja de hoy. Preparar las decisiones de mañana.',233,1620,17,color='#E4EEE7')
text('Universidad de Pamplona · Ingeniería de Software II · Noviembre de 2026',38,1655,12,color='#D1E2D5')
c.showPage();c.save()
pdf=pdfium.PdfDocument(str(OUT)); pdf[0].render(scale=1.2).to_pil().save(ROOT/'output/pdf/horizonte-poster-v3.png')
t=PdfReader(OUT).pages[0].extract_text()
assert 'Adrian Perez Pacheco' in t and 'Open Banking' in t and 'Aún no implementado' in t
print(str(OUT))
