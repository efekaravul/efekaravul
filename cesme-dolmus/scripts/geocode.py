import json, time, urllib.parse, urllib.request, math, os
UA = "cesme-beach-map/1.0 (efekaravul@gmail.com)"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "geocode.json")

# (key, [candidate queries in priority order], expected_anchor(lat,lon), max_km)
STOPS = [
 ("cesme_merkez", ["Cumhuriyet Meydanı, Çeşme, İzmir","Çeşme Cumhuriyet Meydanı","Çeşme Merkez, İzmir"], (38.3235,26.3060), 3.0),
 ("ilica_merkez", ["Ilıca Mahallesi, Çeşme, İzmir","Ilıca, Çeşme"], (38.3084,26.3607), 4.0),
 ("devlet_hastanesi", ["Çeşme Devlet Hastanesi, Çeşme, İzmir","Çeşme Devlet Hastanesi"], (38.31,26.35), 6.0),
 ("altinyunus", ["Altınyunus, Çeşme, İzmir","Altınyunus Mahallesi, Çeşme","Altın Yunus, Çeşme"], (38.315,26.345), 7.0),
 ("alacati_camlik", ["Çamlık Mahallesi, Alaçatı, Çeşme, İzmir","Alaçatı Çamlık, Çeşme"], (38.283,26.371), 5.0),
 ("alacati_merkez", ["Alaçatı Mahallesi, Çeşme, İzmir","Alaçatı, Çeşme, İzmir"], (38.2848,26.3745), 4.0),
 ("bedir_plaji", ["Bedir Plajı, Alaçatı, Çeşme","Bedir Beach, Alaçatı","Bedir Plajı, Çeşme, İzmir"], (38.24,26.39), 8.0),
 ("migros_dalyan", ["Migros, Dalyan, Çeşme, İzmir","Dalyan Migros, Çeşme","Migros Çeşme Dalyan"], (38.34,26.31), 6.0),
 ("atadag_sitesi", ["Atadağ Sitesi, Dalyan, Çeşme","Atadağ, Çeşme, İzmir","Atadağ Mahallesi, Çeşme"], (38.348,26.308), 6.0),
 ("dalyan_mahallesi", ["Dalyan Mahallesi, Çeşme, İzmir","Dalyanköy, Çeşme"], (38.355,26.306), 6.0),
 ("cesme_limani", ["Çeşme Limanı, Çeşme, İzmir","Çeşme Marina, Çeşme","Çeşme Liman, İzmir"], (38.324,26.300), 4.0),
 ("fener_koyu", ["Fener Koyu, Çeşme, İzmir","Çeşme Feneri, Çeşme","Fener, Çeşme, İzmir"], (38.28,26.26), 12.0),
 ("ciftlik_merkez", ["Çiftlik Mahallesi, Çeşme, İzmir","Çiftlikköy, Çeşme, İzmir","Çiftlik, Çeşme"], (38.28,26.27), 10.0),
 ("pirlanta_plaji", ["Pırlanta Plajı, Çeşme, İzmir","Pırlanta Beach, Çeşme","Pırlanta Plajı, Çiftlik, Çeşme"], (38.2692,26.2494), 5.0),
 ("altinkum_plaji", ["Altınkum Plajı, Çeşme, İzmir","Altınkum Beach, Çeşme","Altınkum, Çeşme, İzmir"], (38.2677,26.2786), 5.0),
 ("ayayorgi_sapagi", ["Ayayorgi, Çeşme, İzmir","Ayayorgi Koyu, Çeşme","Ayayorgi Bay, Çeşme"], (38.338,26.311), 6.0),
]
VIEWBOX = "26.15,38.45,26.50,38.15"  # left,top,right,bottom

def hav(a,b):
    R=6371.0
    p1,p2=math.radians(a[0]),math.radians(b[0])
    dp=p2-p1; dl=math.radians(b[1]-a[1])
    h=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(h))

def q(query):
    url="https://nominatim.openstreetmap.org/search?"+urllib.parse.urlencode(
        {"q":query,"format":"json","limit":"5","countrycodes":"tr",
         "viewbox":VIEWBOX,"bounded":"1","addressdetails":"1"})
    req=urllib.request.Request(url, headers={"User-Agent":UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)

res={}
for key,queries,anchor,maxkm in STOPS:
    picked=None
    for qq in queries:
        try: rows=q(qq)
        except Exception as e:
            print("ERR",key,qq,e); rows=[]
        time.sleep(1.2)
        for row in rows:
            lat,lon=float(row["lat"]),float(row["lon"])
            d=hav(anchor,(lat,lon))
            if d<=maxkm:
                picked={"key":key,"query":qq,"lat":round(lat,6),"lon":round(lon,6),
                        "display_name":row["display_name"],"osm_type":row.get("osm_type"),
                        "osm_id":row.get("osm_id"),"class":row.get("class"),"type":row.get("type"),
                        "anchor_dist_km":round(d,3),"verified":True}
                break
        if picked: break
    if not picked:
        picked={"key":key,"query":queries[0],"lat":None,"lon":None,"verified":False,
                "note":"Nominatim'de doğrulanabilir sonuç bulunamadı"}
    print(json.dumps(picked,ensure_ascii=False))
    res[key]=picked

json.dump(res,open(OUT,"w"),ensure_ascii=False,indent=1)
print("\nWROTE",OUT)
