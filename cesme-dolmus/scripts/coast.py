import json, math, os
from collections import defaultdict
HERE=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.join(HERE,"..","data")
raw=json.load(open(os.path.join(OUT,"coastline.json")))
els=[w for w in raw["elements"] if w.get("geometry")]
ways=[[(p["lon"],p["lat"]) for p in w["geometry"]] for w in els]
def key(p): return (round(p[0],7),round(p[1],7))

byStart=defaultdict(list); endKeys=set()
for i,w in enumerate(ways):
    byStart[key(w[0])].append(i); endKeys.add(key(w[-1]))
used=[False]*len(ways); chains=[]
def grow(i):
    used[i]=True; ch=list(ways[i])
    while True:
        nxt=[j for j in byStart[key(ch[-1])] if not used[j]]
        if not nxt: break
        j=nxt[0]; used[j]=True; ch.extend(ways[j][1:])
        if key(ch[-1])==key(ch[0]): break
    return ch
# 1) true heads first (start node is nobody's end node)
for i,w in enumerate(ways):
    if not used[i] and key(w[0]) not in endKeys: chains.append(grow(i))
# 2) remaining = closed loops
for i in range(len(ways)):
    if not used[i]: chains.append(grow(i))
closed=[c for c in chains if key(c[0])==key(c[-1])]
opens=[c for c in chains if key(c[0])!=key(c[-1])]
print("chains",len(chains),"closed",len(closed),"open",len(opens),
      "open sizes",sorted((len(c) for c in opens),reverse=True)[:5])

W=tuple(float(v) for v in os.environ.get("COAST_W","26.215,38.205,26.425,38.375").split(","))
def inside(p): return W[0]-1e-12<=p[0]<=W[2]+1e-12 and W[1]-1e-12<=p[1]<=W[3]+1e-12
def clip_seg(a,b):
    x1,y1=a; x2,y2=b; dx=x2-x1; dy=y2-y1; t0,t1=0.0,1.0
    for p,q in ((-dx,x1-W[0]),(dx,W[2]-x1),(-dy,y1-W[1]),(dy,W[3]-y1)):
        if p==0:
            if q<0: return None
        else:
            r=q/p
            if p<0:
                if r>t1: return None
                if r>t0: t0=r
            else:
                if r<t0: return None
                if r<t1: t1=r
    return ((x1+t0*dx,y1+t0*dy),(x1+t1*dx,y1+t1*dy))
def clip_chain(ch):
    out=[]; cur=[]
    for i in range(len(ch)-1):
        s=clip_seg(ch[i],ch[i+1])
        if s is None:
            if len(cur)>1: out.append(cur)
            cur=[]; continue
        a,b=s
        if not cur: cur=[a,b]
        elif abs(cur[-1][0]-a[0])<1e-9 and abs(cur[-1][1]-a[1])<1e-9: cur.append(b)
        else:
            if len(cur)>1: out.append(cur)
            cur=[a,b]
    if len(cur)>1: out.append(cur)
    return out

rings=[]; pieces=[]
for ch in chains:
    isc = key(ch[0])==key(ch[-1])
    if isc and all(inside(p) for p in ch): rings.append(ch); continue
    for pc in clip_chain(ch):
        if abs(pc[0][0]-pc[-1][0])<1e-9 and abs(pc[0][1]-pc[-1][1])<1e-9: rings.append(pc)
        else: pieces.append(pc)
print("rings",len(rings),"pieces",len(pieces),[len(p) for p in pieces])

def tparam(p):
    x,y=p; tol=1e-7
    if abs(y-W[1])<tol: return (x-W[0])/(W[2]-W[0])
    if abs(x-W[2])<tol: return 1+(y-W[1])/(W[3]-W[1])
    if abs(y-W[3])<tol: return 2+(W[2]-x)/(W[2]-W[0])
    if abs(x-W[0])<tol: return 3+(W[3]-y)/(W[3]-W[1])
    return None
CORN=[(0.0,(W[0],W[1])),(1.0,(W[2],W[1])),(2.0,(W[2],W[3])),(3.0,(W[0],W[3]))]
def border(t0,t1):
    span=(t1-t0)%4.0
    if span<1e-12: span=4.0
    out=[]
    for ct,cp in CORN:
        d=(ct-t0)%4.0
        if 1e-12<d<span-1e-12: out.append((d,cp))
    out.sort(key=lambda z:z[0]); return [p for _,p in out]

P=[]
for pc in pieces:
    ti,to=tparam(pc[0]),tparam(pc[-1])
    if ti is None or to is None:
        print("WARN piece not on border", pc[0], pc[-1]); continue
    P.append({"pts":pc,"ti":ti,"to":to,"used":False})
polys=[]
for st in P:
    if st["used"]: continue
    ring=[]; cur=st
    for _ in range(len(P)+2):
        cur["used"]=True; ring.extend(cur["pts"]); t=cur["to"]
        d_home=(st["ti"]-t)%4.0
        cand=[q for q in P if not q["used"]]
        nxt=min(cand,key=lambda q:(q["ti"]-t)%4.0) if cand else None
        if nxt is None or d_home <= (nxt["ti"]-t)%4.0:
            ring.extend(border(t,st["ti"])); break
        ring.extend(border(t,nxt["ti"])); cur=nxt
    if len(ring)>3: polys.append(ring)

def dp(pts,eps):
    if len(pts)<3: return pts
    import sys; sys.setrecursionlimit(100000)
    def rec(a,b):
        if b<=a+1: return []
        x1,y1=pts[a]; x2,y2=pts[b]; dx=x2-x1; dy=y2-y1; den=math.hypot(dx,dy)
        best=-1.0; bi=a
        for i in range(a+1,b):
            x,y=pts[i]
            d=abs(dy*x-dx*y+x2*y1-y2*x1)/den if den>1e-15 else math.hypot(x-x1,y-y1)
            if d>best: best=d; bi=i
        if best<=eps: return []
        return rec(a,bi)+[bi]+rec(bi,b)
    return [pts[i] for i in [0]+rec(0,len(pts)-1)+[len(pts)-1]]

EPSD=float(os.environ.get("COAST_EPS","0.00025"))
land=[dp(p,EPSD) for p in polys]; land=[p for p in land if len(p)>3]
isl=[dp(r,EPSD) for r in rings]; isl=[r for r in isl if len(r)>3]
print("land polys",[len(p) for p in land],"islands",[len(p) for p in isl])
json.dump({"window":W,
           "land":[[[round(x,5),round(y,5)] for x,y in p] for p in land],
           "islands":[[[round(x,5),round(y,5)] for x,y in p] for p in isl]},
          open(os.path.join(OUT,os.environ.get("COAST_OUT","coast_simpl.json")),"w"))
print("WROTE",os.environ.get("COAST_OUT","coast_simpl.json"))
