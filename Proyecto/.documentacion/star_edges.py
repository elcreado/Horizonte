import json
from pathlib import Path
s=json.loads(Path('C:/Program Files (x86)/StarUML/samples/ERDExample.mdj').read_text(encoding='utf-8-sig'))
def walk(o):
 if isinstance(o,dict):
  yield o
  for v in o.values():yield from walk(v)
 elif isinstance(o,list):
  for v in o:yield from walk(v)
a=list(walk(s));r=next(x for x in a if x.get('_type')=='ERDRelationshipView');print(json.dumps(r,indent=2))
