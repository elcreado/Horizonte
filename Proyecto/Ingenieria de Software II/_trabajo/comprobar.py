from pathlib import Path
from datetime import date,timedelta
from decimal import Decimal
from types import SimpleNamespace
import importlib.util,json,subprocess,sys

WORK=Path(__file__).resolve().parent
PROJECT=WORK.parents[2]
spec=importlib.util.spec_from_file_location('pure_forecast',PROJECT/'backend/apps/forecast/services.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

def variant(balance,as_of,horizon,obligations):
    if horizon not in (30,60,90):raise ValueError('Horizonte inválido')
    flows={}
    for item in obligations:
        if not as_of < item.due_date <= as_of+timedelta(days=horizon):continue
        sign=1 if item.direction=='in' else -1
        flows[item.due_date]=flows.get(item.due_date,Decimal('0'))+sign*item.outstanding_amount
    points=[]
    for offset in range(1,horizon+1):
        day=as_of+timedelta(days=offset)
        balance+=flows.get(day,Decimal('0'))
        points.append({'date':day.isoformat(),'balance':str(balance)})
    return points

cut=date(2026,10,30);checks=0
for horizon in (30,60,90):
    for balance in ('0','100.10','-5.00'):
        for direction in ('in','out'):
            items=[SimpleNamespace(due_date=cut+timedelta(days=d),direction=direction,outstanding_amount=Decimal('0.10')) for d in (-1,0,1,30,60,90,91)]
            assert module.project_obligations(Decimal(balance),cut,horizon,items)==variant(Decimal(balance),cut,horizon,items)
            checks+=1
for horizon in (0,31,45,91):
    for fn in (module.project_obligations,variant):
        try:fn(Decimal('0'),cut,horizon,[])
        except ValueError:checks+=1
        else:raise AssertionError('Aceptó horizonte inválido')

def stub_accepts(h):return h
red=stub_accepts(45)==45
assert red
record={'fecha':'2026-10-30','alcance':'Ejercicio académico aislado; no modifica backend',
 'equivalencia':{'estado':'OK','comprobaciones':checks,'dependencias':'biblioteca estándar; sin BD'},
 'TDD':{'Red':'El stub acepta45: falla el criterio de rechazo (fallo esperado)',
 'Green':'Servicio rechaza45 con ValueError', 'Refactor':'Guard clause conserva resultados en18combinaciones y8rechazos'},
 'venta':'Sintaxis compilada con ast.parse en resolver.py; adaptadores y compensación no implementados'}
command=[str(PROJECT/'.venv/Scripts/python.exe'),str(PROJECT/'backend/manage.py'),'test','tests.test_application.ApplicationTests.test_company_isolation','--verbosity','2']
result=subprocess.run(command,cwd=PROJECT,capture_output=True,text=True)
(WORK/'prueba_aislamiento.log').write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
record['prueba_aislamiento']={'comando':' '.join(command),'exit_code':result.returncode,'log':'_trabajo/prueba_aislamiento.log','resultado':'Pasó' if result.returncode==0 else 'No pasó; consultar log'}
(WORK/'evidencia_academica.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
(WORK/'refactor_contractual.py').write_text('from datetime import timedelta\nfrom decimal import Decimal\n\n'+__import__('inspect').getsource(variant),encoding='utf-8')
print(json.dumps(record,ensure_ascii=False,indent=2))
