# -*- coding: utf-8 -*-
"""overview.svg — stilize kuşbakışı şematik harita.
Kıyı geometrisi: OSM natural=coastline (Overpass), Douglas-Peucker ile sadeleştirildi.
Rota geometrisi: OSRM. Elle şekil uydurulmadı."""
import json, math, os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
import model as M
OUT=os.path.join(HERE,"..","data")
C=json.load(open(os.path.join(OUT,"coast_svg.json")))
R=M.R; G=M.G
DEST=sys.argv[1] if len(sys.argv)>1 else "/home/user/efekaravul/overview.svg"

W,H = 1600,900
WIN = C["window"]           # xmin,ymin,xmax,ymax  (lon/lat)
LAT0 = (WIN[1]+WIN[3])/2
KX = math.cos(math.radians(LAT0))
X0,X1 = WIN[0]*KX, WIN[2]*KX
Y0,Y1 = WIN[1], WIN[3]
def P(lat,lon):
    return ((lon*KX-X0)/(X1-X0)*W, (1-(lat-Y0)/(Y1-Y0))*H)

def dp(pts,eps):
    if len(pts)<3: return pts
    sys.setrecursionlimit(200000)
    def rec(a,b):
        if b<=a+1: return []
        x1,y1=pts[a]; x2,y2=pts[b]; dx=x2-x1; dy=y2-y1; den=math.hypot(dx,dy)
        best=-1.0; bi=a
        for i in range(a+1,b):
            x,y=pts[i]
            d=abs(dy*x-dx*y+x2*y1-y2*x1)/den if den>1e-12 else math.hypot(x-x1,y-y1)
            if d>best: best=d; bi=i
        if best<=eps: return []
        return rec(a,bi)+[bi]+rec(bi,b)
    return [pts[i] for i in [0]+rec(0,len(pts)-1)+[len(pts)-1]]

def path(pts,close=False,r=1):
    d="M"+" L".join(f"{x:.{r}f},{y:.{r}f}" for x,y in pts)
    return d+(" Z" if close else "")

# ---------- kara ----------
land_px=[dp([P(y,x) for x,y in poly],0.7) for poly in C["land"]]
land_px=[p for p in land_px if len(p)>3]
isl_px =[dp([P(y,x) for x,y in poly],0.7) for poly in C["islands"]]
isl_px =[p for p in isl_px if len(p)>3]
LAND_D=" ".join(path(p,True) for p in land_px+isl_px)

# ---------- kumsal yayları (plajların yakınındaki kıyı parçaları) ----------
def near_arcs(lat,lon,radius_m=650):
    out=[]
    for poly in C["land"]:
        idx=[i for i,(x,y) in enumerate(poly)
             if math.hypot((x-lon)*111320*KX,(y-lat)*110540)<radius_m]
        if not idx: continue
        run=[idx[0]]
        for i in idx[1:]:
            if i==run[-1]+1: run.append(i)
            else:
                if len(run)>1: out.append([P(poly[j][1],poly[j][0]) for j in run])
                run=[i]
        if len(run)>1: out.append([P(poly[j][1],poly[j][0]) for j in run])
    return out
SAND=[]
for b in M.BEACHES: SAND += near_arcs(b["lat"],b["lng"])
SAND_D=" ".join(path(a) for a in SAND)

# ---------- rotalar ----------
ROUTE_D={}
for h in ("hat1","hat2","hat3","hat4"):
    ROUTE_D[h]=path(dp([P(c[0],c[1]) for c in R["routes"][h]["coords"]],0.9))
WALK_D=[path(dp([P(c[0],c[1]) for c in v["coords"]],0.9)) for v in R["walk"].values()]

# ---------- etiket yerleşimi ----------
ROUTE_PTS=[]
for h in ("hat1","hat2","hat3","hat4"):
    ROUTE_PTS += dp([P(c[0],c[1]) for c in R["routes"][h]["coords"]],2.5)
for v in R["walk"].values():
    ROUTE_PTS += dp([P(c[0],c[1]) for c in v["coords"]],2.5)
def rota_var(b,pad=4):
    x,y,w,h=b
    return any(x-pad<=px<=x+w+pad and y-pad<=py<=y+h+pad for px,py in ROUTE_PTS)

PANELS=[]   # (x,y,w,h) rezerve alanlar
def rect(x,y,w,h): return (x,y,w,h)
def hit(a,b,pad=3):
    return not (a[0]+a[2]+pad<b[0] or b[0]+b[2]+pad<a[0] or
                a[1]+a[3]+pad<b[1] or b[1]+b[3]+pad<a[1])
TITLE=rect(34,26,470,104)
LEGEND=rect(1206,558,364,306)
SCALE=rect(40,806,250,60)
PANELS += [TITLE,LEGEND,SCALE]

BOLGE=[("ALAÇATI",38.2848,26.3745,"merkez"),("PORT ALAÇATI",38.2554,26.3831,"marina"),
       ("AYAYORGİ KOYU",38.3382,26.3110,"koy"),("DALYAN",38.3558,26.3050,"köy"),
       ("ALTINKUM – PIRLANTA",38.2685,26.2640,"kumsallar"),("ÇEŞME",38.3240,26.3030,"merkez"),
       ("ILICA",38.3084,26.3607,"merkez")]

PIN_R=15.5
PIN_OFF={"solemare":(-46,-34),"aura":(-60,4),"mano":(14,46),
         "flyinn":(-46,-14),"playa":(12,42)}
pins=[]
for b in M.BEACHES:
    ax,ay=P(b["lat"],b["lng"]); ox,oy=PIN_OFF.get(b["key"],(0,0))
    pins.append({"b":b,"px":(ax+ox,ay+oy),"anchor":(ax,ay),"kaydi":(ox,oy)!=(0,0)})
for p in pins:
    PANELS.append(rect(p["px"][0]-PIN_R,p["px"][1]-PIN_R,PIN_R*2,PIN_R*2))

# pusula
COMPASS=rect(W-136,54,92,92); PANELS.append(COMPASS)

# yürüyüş etiketi (Ayayorgi sapağı yanında)
JX,JY=P(*R["junction"])
WALK_TXT="yürüyüş ~10-15 dk"
WALK_W=len(WALK_TXT)*6.6+10; WALK_H=20
WALK_POS=None
for dx,dy,an in ((-16,34,"end"),(-16,54,"end"),(20,54,"start"),(20,-26,"start"),(-16,-26,"end"),(20,80,"start")):
    cx,cy=JX+dx,JY+dy
    bx = cx if an=="start" else cx-WALK_W
    bb=rect(bx,cy-WALK_H/2,WALK_W,WALK_H)
    if not any(hit(bb,q) for q in PANELS):
        WALK_POS={"x":cx,"y":cy,"anchor":an,"box":bb}; break
if WALK_POS is None:
    WALK_POS={"x":JX-16,"y":JY+34,"anchor":"end","box":rect(JX-16-WALK_W,JY+24,WALK_W,WALK_H)}
PANELS.append(WALK_POS["box"])

DIRS=[(1,0),(0.71,-0.71),(0,-1),(-0.71,-0.71),(-1,0),(-0.71,0.71),(0,1),(0.71,0.71)]
RADII=[26,40,58,80,108,140]
placed=[]
for p in sorted(pins,key=lambda q:q["b"]["id"]):
    b=p["b"]; txt=f'{b["id"]}. {b["ad"]}'
    tw=len(txt)*8.4+16; th=26
    px,py=p["px"]; best=None
    for kacin in (True,False):
        for r in RADII:
            for dx,dy in DIRS:
                cx,cy=px+dx*(r+PIN_R), py+dy*(r+PIN_R)
                anchor = "start" if dx>0.3 else ("end" if dx<-0.3 else "middle")
                bx = cx if anchor=="start" else (cx-tw if anchor=="end" else cx-tw/2)
                by = cy-th/2
                if bx<12 or bx+tw>W-12 or by<12 or by+th>H-12: continue
                if any(hit((bx,by,tw,th),q) for q in PANELS+[q["box"] for q in placed]): continue
                if kacin and rota_var((bx,by,tw,th),2): continue
                best={"txt":txt,"anchor":anchor,"cx":cx,"cy":cy,"box":rect(bx,by,tw,th),
                      "lead":r>28,"px":px,"py":py,"id":b["id"]}
                break
            if best: break
        if best: break
    if best is None:
        best={"txt":txt,"anchor":"start","cx":px+34,"cy":py-30,
              "box":rect(px+34,py-42,tw,th),"lead":True,"px":px,"py":py,"id":b["id"]}
    placed.append(best)
for q in placed: PANELS.append(q["box"])

# düğüm etiketleri
node_lbls=[]
NODE_CAND=[(15,5,"start"),(-15,5,"end"),(15,-14,"start"),(-15,-14,"end"),
           (15,24,"start"),(-15,24,"end"),(0,-22,"middle"),(0,30,"middle"),
           (-30,-24,"end"),(30,-24,"start"),(-30,26,"end"),(30,26,"start"),
           (0,-40,"middle"),(0,46,"middle"),(-46,6,"end"),(46,6,"start"),
           (-46,-34,"end"),(-46,40,"end"),(0,-58,"middle"),(0,64,"middle")]
for n in M.NODES:
    x,y=P(n["lat"],n["lng"])
    tw=len(n["ad"])*7.3+12; th=21; got=None
    for kacin in (True,False):
        for dx,dy,an in NODE_CAND:
            cx,cy=x+dx,y+dy
            bx = cx if an=="start" else (cx-tw if an=="end" else cx-tw/2)
            bb=rect(bx,cy-th/2,tw,th)
            if bx<10 or bx+tw>W-10: continue
            if any(hit(bb,q) for q in PANELS): continue
            if kacin and rota_var(bb,2): continue
            got={"ad":n["ad"],"x":cx,"y":cy,"anchor":an,"box":bb}; break
        if got: break
    if got is None:
        got={"ad":n["ad"],"x":x+15,"y":y+5,"anchor":"start","box":rect(x+15,y-5,tw,th)}
    node_lbls.append(got); PANELS.append(got["box"])
    PANELS.append(rect(x-10,y-10,20,20))

# bölge etiketleri — greedy yerleşim
import math as _m
BOLGE_DIR=[(_m.cos(_m.radians(a)),_m.sin(_m.radians(a))) for a in range(-90,270,22)]
bolge_items=[]
for ad,la,lo,alt in BOLGE:
    x,y=P(la,lo); w=len(ad)*12.3+20; h=42; got=None
    for kacin in (True,False):
        for r in (34,48,64,82,102,124):
            for dx,dy in BOLGE_DIR:
                cx,cy=x+dx*r, y+dy*r
                bb=rect(cx-w/2,cy-17,w,h)
                if bb[0]<10 or bb[0]+w>W-10 or bb[1]<10 or bb[1]+h>H-10: continue
                if any(hit(bb,q) for q in PANELS): continue
                if kacin and rota_var(bb): continue
                got={"ad":ad,"alt":alt,"x":cx,"y":cy,"box":bb}; break
            if got: break
        if got: break
    if got is None:
        got={"ad":ad,"alt":alt,"x":x,"y":y-34,"box":rect(x-w/2,y-50,w,h)}
    bolge_items.append(got); PANELS.append(got["box"])

# çakışma doğrulaması
clash=[]
allb=[(f'etiket {q["id"]}',q["box"]) for q in placed] \
   + [(f'bölge {q["ad"]}',q["box"]) for q in bolge_items] \
   + [(f'düğüm {q["ad"]}',q["box"]) for q in node_lbls] \
   + [("başlık",TITLE),("lejant",LEGEND),("ölçek",SCALE),("pusula",COMPASS),
      ("yürüyüş etiketi",WALK_POS["box"])] \
   + [(f'pin {p["b"]["id"]}',rect(p["px"][0]-PIN_R,p["px"][1]-PIN_R,PIN_R*2,PIN_R*2)) for p in pins]
for i in range(len(allb)):
    for j in range(i+1,len(allb)):
        if hit(allb[i][1],allb[j][1],0): clash.append((allb[i][0],allb[j][0]))
print("ÇAKIŞMA:", clash if clash else "yok")

# ---------- SVG ----------
HAT=M.HATLAR
def esc(s): return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
S=[]
A=S.append
A(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
  f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Georgia, \'Iowan Old Style\', serif">')
A('<title>Çeşme Yarımadası — Beach Club ve Dolmuş Hatları</title>')
A('<desc>Kıyı çizgisi OpenStreetMap natural=coastline verisinden (Overpass API) alınmış, '
  'Douglas-Peucker ile sadeleştirilmiştir. Dolmuş güzergâh geometrisi OSRM ile üretilmiştir.</desc>')
A('<defs>')
A('<linearGradient id="deniz" x1="0" y1="0" x2="0.3" y2="1">'
  '<stop offset="0" stop-color="#C9E1F8"/><stop offset="0.55" stop-color="#B5D4F4"/>'
  '<stop offset="1" stop-color="#9CC3EC"/></linearGradient>')
A('<linearGradient id="kara" x1="0.2" y1="0" x2="0.8" y2="1">'
  '<stop offset="0" stop-color="#EFE6C9"/><stop offset="0.6" stop-color="#E3D8B4"/>'
  '<stop offset="1" stop-color="#D3C79E"/></linearGradient>')
A('<filter id="kagit" x="-2%" y="-2%" width="104%" height="104%">'
  '<feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="4" seed="7" result="n"/>'
  '<feColorMatrix in="n" type="saturate" values="0"/>'
  '<feComponentTransfer><feFuncA type="linear" slope="0.055"/></feComponentTransfer></filter>')
A('<filter id="golge" x="-60%" y="-60%" width="220%" height="220%">'
  '<feDropShadow dx="0" dy="1.6" stdDeviation="1.8" flood-color="#1c2a36" flood-opacity="0.38"/></filter>')
A('<filter id="karaGolge" x="-10%" y="-10%" width="120%" height="120%">'
  '<feDropShadow dx="2" dy="3" stdDeviation="4" flood-color="#2c4257" flood-opacity="0.30"/></filter>')
A('</defs>')

# deniz
A(f'<rect width="{W}" height="{H}" fill="url(#deniz)"/>')
# sığ su halkaları
for wdt,col,op in ((34,"#A8CDEF",.55),(22,"#BEDBF6",.65),(11,"#D3E7FA",.8)):
    A(f'<path d="{LAND_D}" fill="none" stroke="{col}" stroke-width="{wdt}" '
      f'stroke-opacity="{op}" stroke-linejoin="round"/>')
# kara
A(f'<g filter="url(#karaGolge)"><path d="{LAND_D}" fill="url(#kara)" fill-rule="evenodd" '
  f'stroke="#9AA07A" stroke-width="1.6" stroke-linejoin="round"/></g>')
# iç doku çizgileri (zeytinlik hissi)
A(f'<path d="{LAND_D}" fill="none" stroke="#B9B489" stroke-width="7" stroke-opacity="0.35" '
  f'stroke-linejoin="round"/>')
# kumsallar
A(f'<path d="{SAND_D}" fill="none" stroke="#E8C368" stroke-width="7" stroke-linecap="round" '
  f'stroke-opacity="0.95"/>')
A(f'<path d="{SAND_D}" fill="none" stroke="#F3DFA6" stroke-width="3" stroke-linecap="round"/>')

# bölge etiketleri
A('<g text-anchor="middle">')
for it in bolge_items:
    A(f'<text x="{it["x"]:.1f}" y="{it["y"]:.1f}" font-size="15" letter-spacing="2.6" '
      f'fill="#6B6644" stroke="#EFE6C9" stroke-width="3.6" paint-order="stroke" '
      f'font-weight="bold">{esc(it["ad"])}</text>')
    A(f'<text x="{it["x"]:.1f}" y="{it["y"]+14:.1f}" font-size="10.5" letter-spacing="1.4" '
      f'fill="#8A8462" stroke="#EFE6C9" stroke-width="3" paint-order="stroke" '
      f'font-style="italic">{esc(it["alt"])}</text>')
A('</g>')

# rotalar
A('<g fill="none" stroke-linecap="round" stroke-linejoin="round">')
for h in ("hat1","hat2","hat3","hat4"):
    A(f'<path d="{ROUTE_D[h]}" stroke="#FFFFFF" stroke-width="11" stroke-opacity="0.85"/>')
for h in ("hat1","hat2","hat3","hat4"):
    A(f'<path d="{ROUTE_D[h]}" stroke="{HAT[h]["renk"]}" stroke-width="6"/>')
for d in WALK_D:
    A(f'<path d="{d}" stroke="#FFFFFF" stroke-width="9" stroke-opacity="0.85"/>')
    A(f'<path d="{d}" stroke="#2F3B45" stroke-width="4" stroke-dasharray="1.5,9"/>')
A('</g>')

# yürüyüş etiketi
A(f'<text x="{WALK_POS["x"]:.1f}" y="{WALK_POS["y"]+4.5:.1f}" text-anchor="{WALK_POS["anchor"]}" '
  f'font-size="12.5" font-style="italic" fill="#2F3B45" stroke="#DCEBFA" stroke-width="3.6" '
  f'paint-order="stroke">{WALK_TXT}</text>')

# düğümler (kare)
for n in M.NODES:
    x,y=P(n["lat"],n["lng"])
    A(f'<g filter="url(#golge)"><rect x="{x-8:.1f}" y="{y-8:.1f}" width="16" height="16" rx="2.5" '
      f'fill="#1F2C38" stroke="#FFFFFF" stroke-width="2.6"/></g>')
for q in node_lbls:
    A(f'<text x="{q["x"]:.1f}" y="{q["y"]+4.5:.1f}" text-anchor="{q["anchor"]}" font-size="12.5" '
      f'fill="#26333F" stroke="#EFE6C9" stroke-width="3.2" paint-order="stroke" '
      f'font-weight="bold">{esc(q["ad"])}</text>')

# leader line + etiketler + pinler
A('<g>')
for q in placed:
    if q["lead"]:
        A(f'<line x1="{q["px"]:.1f}" y1="{q["py"]:.1f}" x2="{q["cx"]:.1f}" y2="{q["cy"]:.1f}" '
          f'stroke="#FFFFFF" stroke-width="3.4"/>'
          f'<line x1="{q["px"]:.1f}" y1="{q["py"]:.1f}" x2="{q["cx"]:.1f}" y2="{q["cy"]:.1f}" '
          f'stroke="#B3392F" stroke-width="1.5"/>')
A('</g>')
for p in pins:
    if p["kaydi"]:
        ax,ay=p["anchor"]; bx,by=p["px"]
        A(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}" stroke="#FFFFFF" stroke-width="3.4"/>'
          f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}" stroke="#B3392F" stroke-width="1.5"/>'
          f'<circle cx="{ax:.1f}" cy="{ay:.1f}" r="3.4" fill="#FFFFFF" stroke="#B3392F" stroke-width="2"/>')
for p in pins:
    x,y=p["px"]; b=p["b"]; tek=b["tek"]
    col="#1D9E75" if tek else "#C8362F"
    A(f'<g filter="url(#golge)"><circle cx="{x:.1f}" cy="{y:.1f}" r="{PIN_R}" fill="{col}" '
      f'stroke="#FFFFFF" stroke-width="3"/></g>'
      f'<text x="{x:.1f}" y="{y+5.2:.1f}" text-anchor="middle" font-size="14.5" font-weight="bold" '
      f'fill="#FFFFFF" font-family="Helvetica, Arial, sans-serif">{b["id"]}</text>')
for q in placed:
    A(f'<text x="{q["cx"]:.1f}" y="{q["cy"]+4.6:.1f}" text-anchor="{q["anchor"]}" font-size="14" '
      f'fill="#20303C" stroke="#F2EAD3" stroke-width="4" paint-order="stroke" '
      f'font-weight="bold">{esc(q["txt"])}</text>')

# başlık
A(f'<g><text x="{TITLE[0]}" y="{TITLE[1]+34}" font-size="34" font-weight="bold" fill="#1F3346">'
  f'ÇEŞME YARIMADASI</text>'
  f'<text x="{TITLE[0]+2}" y="{TITLE[1]+62}" font-size="17" font-style="italic" fill="#2F5570">'
  f'10 beach club &amp; 4 dolmuş hattı — araçsız rehber</text>'
  f'<text x="{TITLE[0]+2}" y="{TITLE[1]+88}" font-size="12.5" fill="#4C6F88">'
  f'Kıyı: OpenStreetMap coastline · Güzergâh: OSRM · 10–13 Eylül</text></g>')

# pusula
A(f'<g transform="translate({COMPASS[0]+COMPASS[2]/2},{COMPASS[1]+COMPASS[3]/2})" opacity="0.9">'
  f'<circle r="34" fill="#EAF3FC" fill-opacity="0.55" stroke="#5B87A8" stroke-width="1.2"/>'
  f'<path d="M0,-27 L7,0 L0,27 L-7,0 Z" fill="#1F3346"/>'
  f'<path d="M0,-27 L7,0 L-7,0 Z" fill="#C8362F"/>'
  f'<text y="-38" text-anchor="middle" font-size="13" font-weight="bold" fill="#1F3346">K</text></g>')

# ölçek
mpp = (WIN[2]-WIN[0])*111320*KX / W          # metre / piksel
bar = 5000/mpp
A(f'<g transform="translate({SCALE[0]},{SCALE[1]})">'
  f'<rect x="-8" y="-6" width="{bar+22:.0f}" height="46" rx="6" fill="#EAF3FC" fill-opacity="0.72" stroke="#7FA6C1" stroke-width="1"/>'
  f'<rect x="0" y="12" width="{bar/2:.1f}" height="8" fill="#1F3346"/>'
  f'<rect x="{bar/2:.1f}" y="12" width="{bar/2:.1f}" height="8" fill="#FFFFFF" stroke="#1F3346" stroke-width="1"/>'
  f'<text x="0" y="8" font-size="11" fill="#1F3346">0</text>'
  f'<text x="{bar:.1f}" y="8" text-anchor="middle" font-size="11" fill="#1F3346">5 km</text></g>')

# lejant
lx,ly,lw,lh=LEGEND
A(f'<g transform="translate({lx},{ly})">')
A(f'<rect width="{lw}" height="{lh}" rx="12" fill="#FBF6E7" fill-opacity="0.95" stroke="#B9AE84" stroke-width="1.4"/>')
A(f'<text x="20" y="30" font-size="14" font-weight="bold" letter-spacing="2.4" fill="#6B6644">LEJANT</text>')
yy=54
for h in ("hat1","hat2","hat3","hat4"):
    A(f'<line x1="20" y1="{yy}" x2="58" y2="{yy}" stroke="{HAT[h]["renk"]}" stroke-width="6" stroke-linecap="round"/>')
    A(f'<text x="70" y="{yy+4.5}" font-size="12.5" fill="#33404B">{esc(HAT[h]["ad"])}</text>')
    yy+=26
A(f'<line x1="20" y1="{yy}" x2="58" y2="{yy}" stroke="#2F3B45" stroke-width="4" stroke-dasharray="1.5,9" stroke-linecap="round"/>')
A(f'<text x="70" y="{yy+4.5}" font-size="12.5" fill="#33404B">Yürüyüş ~10-15 dk (Ayayorgi sapağı → koy)</text>')
yy+=30
A(f'<circle cx="34" cy="{yy}" r="11" fill="#C8362F" stroke="#fff" stroke-width="2.4"/>'
  f'<text x="34" y="{yy+4}" text-anchor="middle" font-size="11" font-weight="bold" fill="#fff" '
  f'font-family="Helvetica,Arial,sans-serif">1</text>'
  f'<text x="70" y="{yy+4.5}" font-size="12.5" fill="#33404B">Beach club (numaralı)</text>')
yy+=26
A(f'<circle cx="34" cy="{yy}" r="11" fill="#1D9E75" stroke="#fff" stroke-width="2.4"/>'
  f'<text x="34" y="{yy+4}" text-anchor="middle" font-size="11" font-weight="bold" fill="#fff" '
  f'font-family="Helvetica,Arial,sans-serif">1</text>'
  f'<text x="70" y="{yy+4.5}" font-size="12.5" fill="#33404B">Alaçatı’dan tek dolmuşla</text>')
yy+=26
A(f'<rect x="26" y="{yy-8}" width="16" height="16" rx="2.5" fill="#1F2C38" stroke="#fff" stroke-width="2.4"/>'
  f'<text x="70" y="{yy+4.5}" font-size="12.5" fill="#33404B">Düğüm (garaj / otogar / marina)</text>')
yy+=26
A(f'<line x1="20" y1="{yy}" x2="58" y2="{yy}" stroke="#E8C368" stroke-width="7" stroke-linecap="round"/>'
  f'<text x="70" y="{yy+4.5}" font-size="12.5" fill="#33404B">Kumsal</text>')
A(f'<text x="20" y="{lh-14}" font-size="10.5" fill="#8A8462">Süre/ücret tahminidir · doğrulanmayan '
  f'duraklar için README</text>')
A('</g>')

A(f'<rect width="{W}" height="{H}" filter="url(#kagit)" fill="#8a7f5a" opacity="0.5" '
  f'style="mix-blend-mode:multiply" pointer-events="none"/>')
A('</svg>')
open(DEST,"w",encoding="utf-8").write("\n".join(S))
print("WROTE",DEST,os.path.getsize(DEST),"bytes")
