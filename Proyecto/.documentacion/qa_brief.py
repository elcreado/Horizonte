from pathlib import Path
from pypdf import PdfReader
import pypdfium2 as pdf
from PIL import Image,ImageDraw
w=Path('Proyecto/.documentacion');out=w/'qa-resumen-v1';out.mkdir(exist_ok=True);d=pdf.PdfDocument(w/'resumen-v1.pdf');r=PdfReader(w/'resumen-v1.pdf')
for i,page in enumerate(d):
 page.render(scale=1.3).to_pil().save(out/f'page-{i+1}.png')
 t=r.pages[i].extract_text();print(i+1,len(t),t[300:410].replace('\n',' / '),t[-110:].replace('\n',' / '))
for off in range(0,len(d),2):
 ims=[Image.open(out/f'page-{i+1}.png') for i in range(off,min(off+2,len(d)))];sheet=Image.new('RGB',(sum(im.width for im in ims),max(im.height for im in ims)+25),'#ddd');x=0;draw=ImageDraw.Draw(sheet)
 for j,im in enumerate(ims):sheet.paste(im,(x,25));draw.text((x+5,5),str(off+j+1),fill='black');x+=im.width
 sheet.save(out/f'pair-{off//2+1}.png')
(w/'resumen-v1.txt').write_text('\n\n'.join('PAGE '+str(i+1)+'\n'+p.extract_text() for i,p in enumerate(r.pages)),encoding='utf-8')
