#!/usr/bin/env python3
import json
from pathlib import Path
from update_traffic import REGIONS, load_region_file

OUT=Path('mobile')

def num(o,*keys):
    for k in keys:
        v=o.get(k)
        if isinstance(v,(int,float)) and v==v:return v
    return None

def point(o):
    lat=num(o,'locationY','lat','latitude'); lng=num(o,'locationX','lng','lon','longitude')
    return None if lat is None or lng is None else [round(float(lat),6),round(float(lng),6)]

def line(value):
    if not isinstance(value,list): return None
    r=[]
    for p in value:
        if not isinstance(p,dict): continue
        lat=num(p,'y','lat','latitude'); lng=num(p,'x','lng','lon','longitude')
        if lat is not None and lng is not None:r.append([round(float(lat),6),round(float(lng),6)])
    if len(r)>41:
        step=max(1,len(r)//40); r=r[::step]
        if r[-1]!=r[-1]: pass
    return r or None

def jam(x,i):
    g=line(x.get('line')); p=point(x)
    if not g and p:g=[p]
    if not g:return None
    z={'id':str(x.get('uuid') or x.get('id') or f'jam-{i}'),'p':g[0],'g':g[:41]}
    if x.get('street'):z['s']=str(x['street'])
    for a,b in [('speed','v'),('delay','d'),('length','l'),('level','q')]:
        if isinstance(x.get(a),(int,float)):z[b]=x[a]
    return z

def alert(x,i):
    p=point(x); t=str(x.get('type') or 'OTHER').upper()
    if not p or t=='JAM':return None
    z={'id':str(x.get('id') or x.get('uuid') or f'alert-{i}'),'t':t,'p':p}
    if x.get('subType'):z['st']=str(x['subType'])
    if x.get('street'):z['s']=str(x['street'])
    if x.get('reportDescription'):z['d']=str(x['reportDescription'])
    if isinstance(x.get('timestamp'),(int,float)):z['ts']=int(x['timestamp'])
    return z

def main():
    OUT.mkdir(exist_ok=True); summary={'v':1,'updated_at':None,'regions':{}}; newest=None
    for rid,r in REGIONS.items():
        raw=load_region_file(rid,r)
        js=[jam(x,i) for i,x in enumerate(raw.get('jams',[])) if isinstance(x,dict)]; js=[x for x in js if x]
        al=[alert(x,i) for i,x in enumerate(raw.get('alerts',[])) if isinstance(x,dict)]; al=[x for x in al if x]
        box=[float(r['bottom_left'].split(',')[0]),float(r['bottom_left'].split(',')[1]),float(r['top_right'].split(',')[0]),float(r['top_right'].split(',')[1])]
        data={'v':1,'region':rid,'name':r['name'],'updated_at':raw.get('updated_at'),'status':raw.get('status','error'),'bbox':box,'j':js,'a':al}
        (OUT/f'{rid}.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
        summary['regions'][rid]={'name':r['name'],'status':data['status'],'updated_at':data['updated_at'],'jams':len(js),'alerts':len(al),'bbox':box}
        if data['updated_at'] and (newest is None or data['updated_at']>newest):newest=data['updated_at']
    summary['updated_at']=newest
    (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')

if __name__=='__main__':main()
