from zipfile import ZipFile
from lxml import etree
z=ZipFile('Proyecto/Plantilla.docx'); r=etree.fromstring(z.read('word/document.xml'))
for e in r.xpath('//*[local-name()="anchor"]'):
 ts=e.xpath('.//*[local-name()="t"]/text()')
 if ts: print(ts,e.xpath('./*[local-name()="extent"]/@*'),e.xpath('./*[local-name()="positionV"]/*/text()'))
for e in r.xpath('//*[local-name()="shape"]'):
 ts=e.xpath('.//*[local-name()="t"]/text()')
 if ts: print('VML',ts,e.get('style'))
