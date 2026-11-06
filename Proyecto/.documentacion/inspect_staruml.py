import json
from pathlib import Path
p=Path('C:/Program Files (x86)/StarUML/samples/ERDExample.mdj');d=json.loads(p.read_text(encoding='utf-8-sig'))
def walk(o):
 if isinstance(o,dict):
  yield o
  for v in o.values():yield from walk(v)
 elif isinstance(o,list):
  for v in o:yield from walk(v)
all=list(walk(d));print('root',[(k,v) for k,v in d.items() if k!='ownedElements'])
for typ in ['ERDDataModel','ERDDiagram','ERDEntity','ERDColumn','ERDRelationship','ERDEntityView','ERDRelationshipView']:
 item=next(x for x in all if x.get('_type')==typ)
 print('\nTYPE',typ,json.dumps(item,ensure_ascii=False)[:10500])
