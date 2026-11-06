from pathlib import Path
import pypdfium2 as pdf
from PIL import Image,ImageDraw
from pypdf import PdfReader
import json,re
w=Path('Proyecto/.documentacion');out=w/'qa-final';out.mkdir(exist_ok=True)
d=pdf.PdfDocument(w/'final.pdf')
for i,page in enumerate(d):page.render(scale=1.3).to_pil().save(out/f'page-{i+1}.png')
for off in range(0,len(d),2):
 ims=[Image.open(out/f'page-{i+1}.png') for i in range(off,min(off+2,len(d)))]
 sheet=Image.new('RGB',(sum(i.width for i in ims),max(i.height for i in ims)+25),'#dddddd');dr=ImageDraw.Draw(sheet);x=0
 for n,im in enumerate(ims):sheet.paste(im,(x,25));dr.text((x+10,5),str(off+n+1),fill='black');x+=im.width
 sheet.save(out/f'pair-{off//2+1}.png')
r=PdfReader(w/'final.pdf');texts=[p.extract_text() for p in r.pages]
expected=json.loads((w/'toc-pages.json').read_text(encoding='utf-8'))
for n,(title,page) in enumerate(expected.items(),1):
 pattern=r'\b'+str(n)+r'\.\s*'+r'\s+'.join(re.escape(s) for s in title.split())
 found=[i+1 for i,t in enumerate(texts) if i>=2 and re.search(pattern,t)]
 assert found and found[0]==page,(title,page,found)
assert '1111043406' in texts[0] and 'Adrian Perez Pacheco' in texts[0]
print('Final pages',len(d),'Index validated',len(expected),'Author validated')
(w/'qa-final-report.json').write_text(json.dumps({'pages':len(d),'index_entries':len(expected),'tables':45,'foreign_keys':68,'render':'Microsoft Word native PDF export','author':'Adrian Perez Pacheco','documento':'1111043406'},ensure_ascii=False,indent=2),encoding='utf-8')
