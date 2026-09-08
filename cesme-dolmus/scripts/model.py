# -*- coding: utf-8 -*-
"""Ortak veri modeli: rota geometrisi + sefer/ücret/süre tahminleri."""
import json, math, os
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","data")
R=json.load(open(os.path.join(OUT,"routes.json")))
G=json.load(open(os.path.join(OUT,"geocode.json")))

DWELL=1.35        # dolmuş duraklama/trafik çarpanı (OSRM serbest akış süresine)
WALK_MS=1.25      # m/s yaya hızı

def ride(sec): return max(1,round(sec*DWELL/60))
def walkmin(m): return max(1,round(m/WALK_MS/60))

L1=[l["t"] for l in R["routes"]["hat1"]["legs"]]   # 9 bacak
L3=[l["t"] for l in R["routes"]["hat3"]["legs"]]   # 4 bacak
L4=[l["t"] for l in R["routes"]["hat4"]["legs"]]   # 6 bacak

GARAJ_TO_OTOGAR = sum(L1[0:6])          # Otogar<->Garaj (ters yön)
OTOGAR_TO_STAGE = sum(L3[0:4])
OTOGAR_TO_FLYINN= sum(L4[0:5])
OTOGAR_TO_EPI   = sum(L4[0:6])

# Otogar -> Ayayorgi sapağı: hat3 poligonu üzerinde kümülatif mesafe oranıyla
def _m(a,b):
    R6=6371000.0
    p1,p2=math.radians(a[0]),math.radians(b[0]); dp=p2-p1; dl=math.radians(b[1]-a[1])
    h=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R6*math.asin(math.sqrt(h))
co=R["routes"]["hat3"]["coords"]; J=R["junction"]
cum=[0.0]
for i in range(1,len(co)): cum.append(cum[-1]+_m(co[i-1],co[i]))
bi=min(range(len(co)), key=lambda i:_m(co[i],J))
JUNCTION_IDX=bi
OTOGAR_TO_JUNC = R["routes"]["hat3"]["duration_s"]*cum[bi]/cum[-1]

WAIT_H1 = 4    # Hat 1: 7-10 dk arayla -> ~4 dk ortalama bekleme
WAIT_H3 = 15   # Hat 3: 30 dk arayla  -> ~15 dk ortalama bekleme
WAIT_H4 = None # Hat 4 sefer sıklığı verilmedi -> doğrulanmadı

WALK = {k: v["distance_m"] for k,v in R["walk"].items()}

B=R["beaches"]
def beach(i,key,name,loc,route,transfers,ride_s,walk_m,waits,fare,fare_note=None,single=False):
    lat,lng=B[key]
    return {"id":i,"key":key,"ad":name,"yer":loc,"lat":lat,"lng":lng,
            "rota":route,"aktarma":transfers,"aracIci":ride(ride_s),
            "yuruyusDk":(walkmin(walk_m) if walk_m else 0),
            "yuruyusM":(round(walk_m) if walk_m else 0),
            "bekleme":waits,"ucret":fare,"ucretNot":fare_note,"tek":single,
            "hatlar":[h for h in ("hat1","hat2","hat3","hat4") if h in route["hats"]]}

BEACHES=[
 beach(1,"elias","Elias","Çark Plajı / Süzer Sun Dreams",
   {"hats":["hat1"],"metin":["Hat 1 · Alaçatı Dolmuş Garajı → Çark Plajı"]},0,
   L1[6],0,[("Hat 1 (Garaj)",WAIT_H1)],
   {"toplam":85,"kalemler":[("Alaçatı → Çark",85)]},None,True),
 beach(2,"moncheri","Mon Cheri Beach","Alaçatı güney kıyısı (Çark–Bedir yönü)",
   {"hats":["hat1"],"metin":["Hat 1 · Garaj → Çark → Bedir yönü"]},0,
   L1[6]+L1[7],0,[("Hat 1 (Garaj)",WAIT_H1)],
   {"toplam":None,"kalemler":[]},
   "Ara durak tarifesi doğrulanmadı. Hattın doğrulanmış uç ücretleri: Alaçatı–Çark 85 TL, Alaçatı–Bedir 105 TL.",True),
 beach(3,"kali","Kali Beach Club","Alaçatı güney kıyısı (Çark–Bedir yönü)",
   {"hats":["hat1"],"metin":["Hat 1 · Garaj → Çark → Bedir yönü"]},0,
   L1[6]+L1[7]+L1[8],0,[("Hat 1 (Garaj)",WAIT_H1)],
   {"toplam":None,"kalemler":[]},
   "Ara durak tarifesi doğrulanmadı. Hattın doğrulanmış uç ücretleri: Alaçatı–Çark 85 TL, Alaçatı–Bedir 105 TL.",True),
 beach(4,"solemare","Sole & Mare","Ayayorgi Koyu",
   {"hats":["hat1","hat3"],"metin":["Hat 1 · Garaj → Çeşme Otogar","Hat 3 · Otogar → Ayayorgi sapağı","Yürüyüş · sapaktan koya"]},1,
   GARAJ_TO_OTOGAR+OTOGAR_TO_JUNC,WALK["solemare"],[("Hat 1 (Garaj)",WAIT_H1),("Hat 3 (Otogar)",WAIT_H3)],
   {"toplam":None,"kalemler":[("Alaçatı → Çeşme",85)]},
   "Çeşme → Ayayorgi sapağı ara durak ücreti doğrulanmadı (Çeşme–Dalyan tam bilet 75 TL)."),
 beach(5,"aura","Aura Beach Club","Ayayorgi Koyu",
   {"hats":["hat1","hat3"],"metin":["Hat 1 · Garaj → Çeşme Otogar","Hat 3 · Otogar → Ayayorgi sapağı","Yürüyüş · sapaktan koya"]},1,
   GARAJ_TO_OTOGAR+OTOGAR_TO_JUNC,WALK["aura"],[("Hat 1 (Garaj)",WAIT_H1),("Hat 3 (Otogar)",WAIT_H3)],
   {"toplam":None,"kalemler":[("Alaçatı → Çeşme",85)]},
   "Çeşme → Ayayorgi sapağı ara durak ücreti doğrulanmadı (Çeşme–Dalyan tam bilet 75 TL)."),
 beach(6,"mano","Mano del Sol","Ayayorgi Koyu",
   {"hats":["hat1","hat3"],"metin":["Hat 1 · Garaj → Çeşme Otogar","Hat 3 · Otogar → Ayayorgi sapağı","Yürüyüş · sapaktan koya"]},1,
   GARAJ_TO_OTOGAR+OTOGAR_TO_JUNC,WALK["mano"],[("Hat 1 (Garaj)",WAIT_H1),("Hat 3 (Otogar)",WAIT_H3)],
   {"toplam":None,"kalemler":[("Alaçatı → Çeşme",85)]},
   "Çeşme → Ayayorgi sapağı ara durak ücreti doğrulanmadı (Çeşme–Dalyan tam bilet 75 TL)."),
 beach(7,"stage","Stage on the Beach","Dalyanköy",
   {"hats":["hat1","hat3"],"metin":["Hat 1 · Garaj → Çeşme Otogar","Hat 3 · Otogar → Dalyan Mahallesi"]},1,
   GARAJ_TO_OTOGAR+OTOGAR_TO_STAGE,0,[("Hat 1 (Garaj)",WAIT_H1),("Hat 3 (Otogar)",WAIT_H3)],
   {"toplam":160,"kalemler":[("Alaçatı → Çeşme",85),("Çeşme → Dalyan",75)]}),
 beach(8,"epi","Epi Beach House","Altınkum",
   {"hats":["hat1","hat4"],"metin":["Hat 1 · Garaj → Çeşme Otogar","Hat 4 · Otogar → Altınkum Plajı"]},1,
   GARAJ_TO_OTOGAR+OTOGAR_TO_EPI,0,[("Hat 1 (Garaj)",WAIT_H1),("Hat 4 (Otogar)",WAIT_H4)],
   {"toplam":170,"kalemler":[("Alaçatı → Çeşme",85),("Çeşme → Altınkum",85)]}),
 beach(9,"flyinn","Fly-Inn Beach Club","Pamukova / Pırlanta",
   {"hats":["hat1","hat4"],"metin":["Hat 1 · Garaj → Çeşme Otogar","Hat 4 · Otogar → Pırlanta Plajı"]},1,
   GARAJ_TO_OTOGAR+OTOGAR_TO_FLYINN,0,[("Hat 1 (Garaj)",WAIT_H1),("Hat 4 (Otogar)",WAIT_H4)],
   {"toplam":170,"kalemler":[("Alaçatı → Çeşme",85),("Çeşme → Pırlanta",85)]}),
 beach(10,"playa","Playa Tropical","Fly-Inn bitişiği (Pırlanta)",
   {"hats":["hat1","hat4"],"metin":["Hat 1 · Garaj → Çeşme Otogar","Hat 4 · Otogar → Pırlanta Plajı"]},1,
   GARAJ_TO_OTOGAR+OTOGAR_TO_FLYINN,0,[("Hat 1 (Garaj)",WAIT_H1),("Hat 4 (Otogar)",WAIT_H4)],
   {"toplam":170,"kalemler":[("Alaçatı → Çeşme",85),("Çeşme → Pırlanta",85)]}),
]

NODES=[
 {"key":"garaj","ad":"Alaçatı Dolmuş Garajı","not":"Hat 1 ve Hat 2 kalkış noktası","lat":R["nodes"]["garaj"][0],"lng":R["nodes"]["garaj"][1]},
 {"key":"otogar","ad":"Çeşme Otogar","not":"Hat 1 · Hat 3 · Hat 4 aktarma merkezi","lat":R["nodes"]["otogar"][0],"lng":R["nodes"]["otogar"][1]},
 {"key":"port","ad":"Port Alaçatı Marina","not":"Hat 2 shuttle son durak","lat":R["nodes"]["port"][0],"lng":R["nodes"]["port"][1]},
 {"key":"cark","ad":"Çark Plajı","not":"Hat 1 durağı — Elias buradan","lat":R["nodes"]["cark"][0],"lng":R["nodes"]["cark"][1]},
]

HATLAR={
 "hat1":{"ad":"Hat 1 · Çeşme–Ilıca–Alaçatı–Çark–Bedir","renk":"#1D9E75",
   "sefer":["İlk araç 07:15 (yaz tarifesi)","Gün boyu 7–10 dk arayla","21:00 sonrası 10–15 dk","Son araç 00:15"],
   "ucret":["Alaçatı → Çark 85 TL","Alaçatı → Bedir 105 TL","Alaçatı → Çeşme 85 TL"],
   "duraklar":["Çeşme Otogar","Çeşme Merkez (Cumhuriyet Meydanı)","Ilıca Merkez","Devlet Hastanesi","Altınyunus","Alaçatı Çamlık","Alaçatı Merkez","Alaçatı Dolmuş Garajı","Çark Plajı","Bedir Plajı"]},
 "hat2":{"ad":"Hat 2 · Alaçatı Garajı ↔ Port Alaçatı","renk":"#BA7517",
   "sefer":["Garaj'dan 08:15'ten itibaren 2 saatte bir","10:15 · 12:15 · 14:15 · 16:15 · 18:15 · son 20:15","Port'tan 08:30'dan itibaren 2 saatte bir, son 20:30"],
   "ucret":[], "duraklar":["Alaçatı Dolmuş Garajı","Port Alaçatı Marina"]},
 "hat3":{"ad":"Hat 3 · Çeşme–Dalyan","renk":"#7F77DD",
   "sefer":["08:00'den itibaren 30 dk arayla 21:00'a kadar","21:45 · 22:30 · 23:15","Son araç 00:00"],
   "ucret":["Çeşme → Dalyan 75 TL"],
   "duraklar":["Çeşme Otogar","Çeşme Merkez","Migros Dalyan","Atadağ Sitesi","Dalyan Mahallesi"]},
 "hat4":{"ad":"Hat 4 · Çeşme–Pırlanta–Altınkum","renk":"#D85A30",
   "sefer":[], 
   "ucret":["Çeşme → Fener 60 TL","Çeşme → Çiftlik 75 TL","Çeşme → Pırlanta 85 TL","Çeşme → Altınkum 85 TL"],
   "duraklar":["Çeşme Otogar","Çeşme Merkez","Çeşme Limanı","Fener Koyu","Çiftlik Merkez","Pırlanta Plajı","Altınkum Plajı"]},
}

# hangi geocode edilmiş durak hangi hatta
STOP_LINES={
 "hat1":["cesme_merkez","devlet_hastanesi","altinyunus","ilica_merkez","alacati_merkez"],
 "hat3":["cesme_merkez","migros_dalyan","dalyan_mahallesi"],
 "hat4":["cesme_merkez","cesme_limani","ciftlik_merkez","pirlanta_plaji"],
}
STOP_LABEL={"cesme_merkez":"Çeşme Merkez (Cumhuriyet Meydanı)","devlet_hastanesi":"Devlet Hastanesi",
 "altinyunus":"Altınyunus","ilica_merkez":"Ilıca Merkez","alacati_merkez":"Alaçatı Merkez",
 "migros_dalyan":"Migros Dalyan","dalyan_mahallesi":"Dalyan Mahallesi","cesme_limani":"Çeşme Limanı",
 "ciftlik_merkez":"Çiftlik Merkez","pirlanta_plaji":"Pırlanta Plajı","altinkum_plaji":"Altınkum Plajı"}
UNVERIFIED=["alacati_camlik","bedir_plaji","atadag_sitesi","fener_koyu"]
UNVERIFIED_LABEL={"alacati_camlik":"Alaçatı Çamlık (Hat 1)","bedir_plaji":"Bedir Plajı (Hat 1)",
 "atadag_sitesi":"Atadağ Sitesi (Hat 3)","fener_koyu":"Fener Koyu (Hat 4)"}
