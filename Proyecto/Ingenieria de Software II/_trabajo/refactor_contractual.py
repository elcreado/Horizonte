from datetime import timedelta
from decimal import Decimal

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
