# -*- coding: utf-8 -*-
import json,re,sys,math
H=open("cesme-dolmus/map.html",encoding="utf-8").read()
m=re.search(r"const D = (\{.*?\});\n",H,re.S); D=json.loads(m.group(1))
VER={"Elias":(38.245621,26.379708),"Mon Cheri Beach":(38.232598,26.367879),
 "Kali Beach Club":(38.229575,26.361261),"Sole & Mare":(38.339365,26.310445),
 "Aura Beach Club":(38.338151,26.311002),"Mano del Sol":(38.337926,26.312351),
 "Stage on the Beach":(38.357353,26.304478),"Epi Beach House":(38.267657,26.278557),
 "Fly-Inn Beach Club":(38.269178,26.249440),"Playa Tropical":(38.269195,26.249699)}
NOD={"Alaçatı Dolmuş Garajı":(38.278321,26.379991),"Çeşme Otogar":(38.315831,26.304653),
 "Port Alaçatı Marina":(38.255381,26.383059),"Çark Plajı":(38.246365,26.383558)}
ok=True
for b in D["plajlar"]:
    e=VER.pop(b["ad"])
    same = abs(b["lat"]-e[0])<1e-9 and abs(b["lng"]-e[1])<1e-9
    ok &= same; print(("OK  " if same else "FARK")+f' plaj {b["id"]:>2}. {b["ad"]:<20} {b["lat"]},{b["lng"]}')
for n in D["dugumler"]:
    e=NOD.pop(n["ad"])
    same = abs(n["lat"]-e[0])<1e-9 and abs(n["lng"]-e[1])<1e-9
    ok &= same; print(("OK  " if same else "FARK")+f' düğüm {n["ad"]:<24} {n["lat"]},{n["lng"]}')
print("Eksik plaj:",list(VER),"eksik düğüm:",list(NOD))
ok &= not VER and not NOD
print("Hat sayısı:",len(D["hatlar"]),"| rota feature:",len(D["rotalar"]["features"]),
      "| yürüyüş feature:",sum(1 for f in D["rotalar"]["features"] if f["properties"]["tip"]=="yuruyus"))
# karada mı?
C=json.load(open("cesme-dolmus/data/coast_simpl.json"))
def pip(pt,poly):
    x,y=pt; ins=False
    for i in range(len(poly)):
        x1,y1=poly[i]; x2,y2=poly[(i+1)%len(poly)]
        if (y1>y)!=(y2>y) and x < x1+(y-y1)*(x2-x1)/(y2-y1): ins=not ins
    return ins
tot=bad=0
for f in D["rotalar"]["features"]:
    for lon,lat in f["geometry"]["coordinates"]:
        tot+=1
        if not any(pip((lon,lat),p) for p in C["land"]): bad+=1
print(f"Rota köşe noktası: {tot}, kıyı poligonu dışında: {bad}")
ok &= bad==0
S=open("cesme-dolmus/overview.svg",encoding="utf-8").read()
print("SVG 1600x900:", 'width="1600" height="900"' in S)
print("SVG'de 10 pin:", S.count('stroke-width="3"/></g>'))
print("\nSONUÇ:", "TÜM KONTROLLER GEÇTİ" if ok else "HATA VAR")
sys.exit(0 if ok else 1)
