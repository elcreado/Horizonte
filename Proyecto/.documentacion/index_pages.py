from pypdf import PdfReader
from pathlib import Path
import re,json
w=Path('Proyecto/.documentacion');r=PdfReader(w/'final-v2.pdf')
texts=[p.extract_text() for p in r.pages]
names=['Introducción','Planteamiento del problema','Justificación','Objetivos','Alcance y contexto de implementación','Mapa de módulos y requerimientos de datos','Reglas de negocio e integridad','Modelo entidad relación MER','Modelo relacional inicial y proceso de normalización','Modelo relacional final en FN3','Diccionario de datos y verificación por tabla','Diseño físico y estrategia transaccional','Correspondencia con la implementación existente','Consultas SQL de validación','Escenario ilustrativo y plan de pruebas','Conclusiones','Referencias del proyecto','Anexo de definición física en PostgreSQL']
found={}
for n,title in enumerate(names,1):
 pattern=r'\b'+str(n)+r'\.\s*'+r'\s+'.join(re.escape(s) for s in title.split())
 matches=[i+1 for i,t in enumerate(texts) if i>=2 and re.search(pattern,t)]
 assert matches,(n,title)
 found[title]=matches[0]
print(found)
(w/'toc-pages.json').write_text(json.dumps(found,ensure_ascii=False),encoding='utf-8')
