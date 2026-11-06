from zipfile import ZipFile
from lxml import etree
z=ZipFile('Proyecto/Plantilla.docx'); r=etree.fromstring(z.read('word/document.xml')); ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
for p in r.xpath('//w:txbxContent/w:p',namespaces=ns):
 t=p.xpath('.//w:t/text()',namespaces=ns)
 if t: print(repr(t))
print('default',etree.fromstring(z.read('word/styles.xml')).xpath('//*[local-name()="docDefaults"]')[0].xpath('.//*[local-name()="sz"]/@*[local-name()="val"]'))
