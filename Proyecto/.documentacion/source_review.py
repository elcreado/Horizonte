from pypdf import PdfReader
from pathlib import Path
from docx import Document
from zipfile import ZipFile
from lxml import etree
x=Document('Proyecto/Plantilla.docx')
print('NORMAL',x.styles['Normal'].element.xml)
print('BODY',x.paragraphs[3]._p.xml)
z=ZipFile('Proyecto/Plantilla.docx')
for n in z.namelist():
 if n.startswith(('word/header','word/footer')) and n.endswith('.xml'):
  print(n,etree.fromstring(z.read(n)).xpath('//*[local-name()="t"]/text()'))
for p in Path('Proyecto/Ejemplos').glob('*.pdf'):
 r=PdfReader(p); print(p.name,len(r.pages))
 print('\n'.join(q.extract_text() for q in r.pages[:6]))
