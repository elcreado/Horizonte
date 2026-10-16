import json,uuid,heapq,math
from pathlib import Path
W=Path(__file__).resolve().parent
OUT=W.parent/'Modelos_Horizonte_StarUML';OUT.mkdir(exist_ok=True)
schema=json.loads((W/'brief-schema.json').read_text(encoding='utf-8'))
ts={t['name']:t for t in schema}
def uid():return uuid.uuid4().hex
def ref(x):return {'$ref':x if isinstance(x,str) else x['_id']}
def obj(typ,parent=None,**kw):
 x={'_type':typ,'_id':uid()}
 if parent:x['_parent']=ref(parent)
 x.update(kw);return x
root=obj('Project',name='Horizonte MER y MR del núcleo financiero',author='Adrian Perez Pacheco',documentation='Modelos correspondientes al documento resumido. 15 entidades, 18 relaciones. FN3. Cardinalidades en notación pata de cuervo. Cada tabla y relación es editable. Las vistas de detalle reutilizan las entidades del modelo general.',ownedElements=[])
edge_specs=[]
for t in schema:
 for f in t['fields']:
  if 'FK ' in f['key']:
   parent=f['key'].split('FK ')[1]
   pks=[ff for ff in t['fields'] if 'PK' in ff['key']]
   edge_specs.append((parent,t['name'],f,'0..1' if 'NULL' in f['key'] else '1','0..1' if 'UQ' in f['key'] or ('PK' in f['key'] and len(pks)==1) else '0..*'))
verbs={('empresa','membresia'):'tiene miembros',('usuario','membresia'):'participa',('rol','membresia'):'define permisos',('empresa','cuenta'):'posee',('cuenta','corte_cuenta'):'registra saldo',('empresa','tercero'):'reconoce',('cuenta','movimiento'):'registra',('tercero','movimiento'):'se identifica en',('categoria','movimiento'):'clasifica',('empresa','obligacion'):'asume',('obligacion','conciliacion'):'recibe abonos',('movimiento','conciliacion'):'se aplica en',('usuario','conciliacion'):'registra abono',('factura','parte_factura'):'declara dos partes',('empresa','registro_factura'):'incorpora',('factura','registro_factura'):'se registra en',('registro_factura','factura_obligacion'):'vincula',('obligacion','factura_obligacion'):'respalda'}
general={'usuario':(0,0),'membresia':(1,0),'rol':(2,0),'tercero':(3,0),'empresa':(1,1),'cuenta':(2,1),'corte_cuenta':(3,1),'factura':(0,2),'registro_factura':(1,2),'movimiento':(3,2),'categoria':(4,2),'parte_factura':(0,3),'factura_obligacion':(1,3),'obligacion':(2,3),'conciliacion':(3,3)}
details=[('Acceso empresarial',{'empresa':(0,1),'membresia':(1,1),'usuario':(1,0),'rol':(2,1)}),('Cuentas y movimientos',{'empresa':(0,0),'cuenta':(1,0),'corte_cuenta':(2,0),'tercero':(0,1),'movimiento':(1,1),'categoria':(2,1)}),('Facturas y obligaciones',{'empresa':(0,0),'registro_factura':(1,0),'factura':(2,0),'obligacion':(0,1),'factura_obligacion':(1,1),'parte_factura':(2,1)}),('Conciliacion de abonos',{'usuario':(0,0),'obligacion':(1,0),'movimiento':(2,0),'conciliacion':(1,1)})]
styles={'visible':True,'enabled':True,'lineColor':'#263238','fillColor':'#ffffff','fontColor':'#17212B','font':'Arial;14;0','showShadow':False,'autoResize':False}
def view(typ,parent,**kw):return obj(typ,parent,**styles,**kw)
def color(n):
 if n in ['empresa','usuario','rol','membresia']:return '#E8F0FA'
 if n in ['cuenta','corte_cuenta','tercero','categoria','movimiento']:return '#FFF3D9'
 if n in ['factura','parte_factura','registro_factura']:return '#E9F5EB'
 return '#F0EAF7'

def route(rects,source,target,used,ports):
 a=rects[source];b=rects[target];ac=(a[0]+a[2]/2,a[1]+a[3]/2);bc=(b[0]+b[2]/2,b[1]+b[3]/2)
 dx=bc[0]-ac[0];dy=bc[1]-ac[1]
 sidea=('R' if dx>0 else 'L') if abs(dx)>abs(dy) else ('B' if dy>0 else 'T')
 sideb={'R':'L','L':'R','B':'T','T':'B'}[sidea]
 def port(n,side):
  x,y,w,h=rects[n];ct=ports.get((n,side),0);ports[(n,side)]=ct+1
  offset=([0,-40,40,-80,80,-120,120][ct%7])
  if side in 'LR':
   yy=round((y+h/2+max(-h/2+20,min(h/2-20,offset)))/20)*20
   return ((x if side=='L' else x+w,yy),(x-20 if side=='L' else x+w+20,yy))
  xx=round((x+w/2+offset)/20)*20
  return ((xx,y if side=='T' else y+h),(xx,y-20 if side=='T' else y+h+20))
 pa,start=port(source,sidea);pb,end=port(target,sideb)
 bounds=(max(x+w for x,y,w,h in rects.values())+120,max(y+h for x,y,w,h in rects.values())+120)
 def blocked(pt):
  x,y=pt
  return any(rx-9<=x<=rx+rw+9 and ry-9<=y<=ry+rh+9 for rx,ry,rw,rh in rects.values())
 startstate=(start[0],start[1],-1);cost={startstate:0};prev={};q=[(0,0,startstate)];last=None;serial=0
 while q:
  _,g,s=heapq.heappop(q)
  if g!=cost.get(s):continue
  x,y,di=s
  if (x,y)==end:last=s;break
  for ndi,(sx,sy) in enumerate([(20,0),(0,20),(-20,0),(0,-20)]):
   v=(x+sx,y+sy)
   if not(0<=v[0]<=bounds[0] and 0<=v[1]<=bounds[1]) or blocked(v):continue
   ng=g+20+(18 if di not in [-1,ndi] else 0)+used.get(v,0)*28
   ns=(*v,ndi)
   if ng<cost.get(ns,10**12):
    cost[ns]=ng;prev[ns]=s;serial+=1;heur=abs(v[0]-end[0])+abs(v[1]-end[1]);heapq.heappush(q,(ng+heur,ng,ns))
 if last is None:raise RuntimeError(('no route',source,target,start,end))
 pts=[]
 while last!=startstate:pts.append(last[:2]);last=prev[last]
 pts.append(start);pts.reverse()
 for pt in pts:used[pt]=used.get(pt,0)+1
 pts=[pa]+pts+[pb];simp=[pts[0]]
 for i in range(1,len(pts)-1):
  if (pts[i][0]-pts[i-1][0])*(pts[i+1][1]-pts[i][1])!=(pts[i][1]-pts[i-1][1])*(pts[i+1][0]-pts[i][0]):simp.append(pts[i])
 simp.append(pts[-1]);return simp

for conceptual in [True,False]:
 model=obj('ERDDataModel',root,name='01 MER conceptual' if conceptual else '02 MR normalizado FN3',ownedElements=[]);root['ownedElements'].append(model)
 entities={};cols={};rels=[]
 for t in schema:
  n=t['name'];entity=obj('ERDEntity',model,name=n.upper(),documentation=t['purpose']+(' Clave candidata adicional ('+t['unique']+').' if t['unique'] else ''),columns=[],ownedElements=[]);entities[n]=entity;model['ownedElements'].append(entity)
  if not conceptual:
   for f in t['fields']:
    c=obj('ERDColumn',entity,name=f['name'],type=f['type'],length='',primaryKey='PK' in f['key'],foreignKey='FK ' in f['key'],nullable='NULL' in f['key'],unique='UQ' in f['key'],documentation=f['desc']);entity['columns'].append(c);cols[(n,f['name'])]=c
 for a,b,f,ca,cb in edge_specs:
  if not conceptual:
   pk=next(ff for ff in ts[a]['fields'] if 'PK' in ff['key']);cols[(b,f['name'])]['referenceTo']=ref(cols[(a,pk['name'])])
  r=obj('ERDRelationship',entities[b],name=verbs[(a,b)] if conceptual else f['name'],identifying=('PK' in f['key']) and not conceptual)
  r['end1']=obj('ERDRelationshipEnd',r,reference=ref(entities[a]),name='0..1' if ca=='0..1' else '1',cardinality=ca)
  r['end2']=obj('ERDRelationshipEnd',r,reference=ref(entities[b]),name='0..1' if cb=='0..1' else '0..N',cardinality=cb)
  if b=='parte_factura':r['end2'].update(name='2 partes',cardinality='1..*');r['documentation']='Exactamente un emisor y un receptor por factura. Restricción adicional de negocio.'
  entities[b]['ownedElements'].append(r);rels.append((a,b,r))
 for ix,(label,positions) in enumerate([('General',general)]+details):
  diagram=obj('ERDDiagram',model,name=('MER ' if conceptual else 'MR ')+label,visible=True,defaultDiagram=(conceptual and ix==0),ownedViews=[]);model['ownedElements'].append(diagram)
  views={};rects={};width=280 if conceptual else 400;gx=460 if conceptual else 600;gy=240 if conceptual else 440
  for n,(cx,cy) in positions.items():
   x=120+cx*gx;y=100+cy*gy;height=60 if conceptual else 40+len(ts[n]['fields'])*20
   rects[n]=(x,y,width,height)
   v=view('ERDEntityView',diagram,model=ref(entities[n]),left=x,top=y,width=width,height=height,subViews=[]);v['fillColor']=color(n)
   lab=view('LabelView',v,left=x+5,top=y+5,width=width-10,height=20,text=n.upper(),horizontalAlignment=2,verticalAlignment=5);lab['font']='Arial;15;1'
   comp=view('ERDColumnCompartmentView',v,model=ref(entities[n]),left=x+5,top=y+30,width=width-10,height=height-30,subViews=[])
   if not conceptual:
    for j,c in enumerate(entities[n]['columns']):comp['subViews'].append(view('ERDColumnView',comp,model=ref(c),left=x+10,top=y+35+j*20,width=width-20,height=18))
   v['subViews']=[lab,comp];v['nameLabel']=ref(lab);v['columnCompartment']=ref(comp);views[n]=v;diagram['ownedViews'].append(v)
  used={};ports={}
  selected=[(a,b,r) for a,b,r in rels if a in positions and b in positions]
  selected.sort(key=lambda e:abs(positions[e[0]][0]-positions[e[1]][0])+abs(positions[e[0]][1]-positions[e[1]][1]))
  for a,b,r in selected:
   pts=route(rects,a,b,used,ports);edge=view('ERDRelationshipView',diagram,model=ref(r),tail=ref(views[a]),head=ref(views[b]),lineStyle=2,points=';'.join(str(x)+':'+str(y) for x,y in pts),subViews=[])
   for nm,pos,alpha,dist,text in [('nameLabel',1,math.pi/2,14,r['name']),('tailNameLabel',2,math.pi/6,35,r['end1']['name']),('headNameLabel',0,-math.pi/6,35,r['end2']['name'])]:
    l=view('EdgeLabelView',edge,hostEdge=ref(edge),edgePosition=pos,alpha=alpha,distance=dist,text=text,left=0,top=0,width=0,height=14,horizontalAlignment=2,verticalAlignment=5)
    l['font']='Arial;12;0';edge['subViews'].append(l);edge[nm]=ref(l)
   diagram['ownedViews'].append(edge)

path=OUT/'Horizonte_MER_MR_FN3.mdj';path.write_text(json.dumps(root,ensure_ascii=False,indent=2),encoding='utf-8')
# Verify identities and references before opening the native project.
ids=set();references=[]
def check(o):
 if isinstance(o,dict):
  if '_id' in o:
   assert o['_id'] not in ids;ids.add(o['_id'])
  if '$ref' in o:references.append(o['$ref'])
  for v in o.values():check(v)
 elif isinstance(o,list):
  for v in o:check(v)
check(root);assert all(r in ids for r in references)
(OUT/'LEEME.txt').write_text('HORIZONTE\nAdrian Perez Pacheco\n\nAbrir Horizonte_MER_MR_FN3.mdj en StarUML.\n01 MER conceptual: entidades y cardinalidades.\n02 MR normalizado FN3: atributos, tipos, PK, FK y UQ individuales.\nCada modelo incluye vista general y cuatro detalles conectados.\nLas entidades de las vistas de detalle son las mismas del modelo general.\n\nLeyenda: pata de cuervo = varios; círculo = opcional; barra = uno.\nRelación identificadora continua: la FK forma parte de la PK.\nRelación no identificadora discontinua: la FK no forma parte de la PK.\nLa leyenda 2 partes exige emisor y receptor en cada factura.\n\nClaves alternativas compuestas:\nMEMBRESIA: empresa_id, usuario_id (PK).\nCORTE_CUENTA: cuenta_id, fecha (PK).\nPARTE_FACTURA: factura_id, papel (PK).\nTERCERO: empresa_id, nombre_normalizado (UQ).\nMOVIMIENTO: cuenta_id, externo_id (UQ).\nOBLIGACION: empresa_id, referencia (UQ).\nCONCILIACION: obligacion_id, solicitud_id (UQ).\nREGISTRO_FACTURA: empresa_id, factura_id (UQ).\n\nLas comprobaciones de igual empresa, límites de conciliación y exactamente dos partes son reglas adicionales; una FK por sí sola no las impone.\n',encoding='utf-8')
print(json.dumps({'file':str(path),'diagrams':10,'entities_per_model':15,'relationships_per_model':18,'references_validated':len(references)}))

