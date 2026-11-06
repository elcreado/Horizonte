import pypdfium2 as pdf
from PIL import Image,ImageDraw
from pathlib import Path
from pypdf import PdfReader
w=Path('Proyecto/.documentacion'); out=w/'qa-v1';out.mkdir(exist_ok=True)
d=pdf.PdfDocument(w/'final-v1.pdf'); reader=PdfReader(w/'final-v1.pdf')
for i,page in enumerate(d):
 im=page.render(scale=1.3).to_pil();im.save(out/f'page-{i+1}.png')
for off in range(0,len(d),8):
 sheet=Image.new('RGB',(1200,900),'#dddddd');dr=ImageDraw.Draw(sheet)
 for j in range(off,min(off+8,len(d))):
  im=Image.open(out/f'page-{j+1}.png');im.thumbnail((285,410));x=(j-off)%4*300;y=(j-off)//4*450;sheet.paste(im,(x,y+25));dr.text((x+10,y+5),str(j+1),fill='black')
 sheet.save(out/f'sheet-{off//8+1}.png')
for i,p in enumerate(reader.pages):
 t=p.extract_text();print(i+1,len(t),t[:95].replace('\n',' / '))
(w/'extracted-v1.txt').write_text('\n\n'.join(f'PAGE {i+1}\n'+p.extract_text() for i,p in enumerate(reader.pages)),encoding='utf-8')
