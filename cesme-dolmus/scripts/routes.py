import json, time, math, urllib.request, os
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","data")
BASE="https://router.project-osrm.org/route/v1"

def osrm(profile, pts, tries=4):
    coords=";".join(f"{lon:.6f},{lat:.6f}" for lat,lon in pts)
    url=f"{BASE}/{profile}/{coords}?overview=full&geometries=geojson&steps=false&annotations=false"
    last=None
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"cesme-beach-map/1.0"}),timeout=60) as r:
                d=json.load(r)
            if d.get("code")=="Ok": return d
            last=d
        except Exception as e:
            last=str(e)
        time.sleep(2*(i+1))
    raise RuntimeError(f"OSRM failed: {last}")

def hav(a,b):
    R=6371000.0
    p1,p2=math.radians(a[0]),math.radians(b[0]); dp=p2-p1; dl=math.radians(b[1]-a[1])
    h=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(h))

# ---- verified nodes (user-given, do not change) ----
N={
 "otogar":(38.315831,26.304653),
 "garaj":(38.278321,26.379991),
 "port":(38.255381,26.383059),
 "cark":(38.246365,26.383558),
}
B={
 "elias":(38.245621,26.379708),"moncheri":(38.232598,26.367879),"kali":(38.229575,26.361261),
 "solemare":(38.339365,26.310445),"aura":(38.338151,26.311002),"mano":(38.337926,26.312351),
 "stage":(38.357353,26.304478),"epi":(38.267657,26.278557),
 "flyinn":(38.269178,26.249440),"playa":(38.269195,26.249699),
}
G=json.load(open(os.path.join(OUT,"geocode.json")))
def g(k): 
    r=G[k]; assert r["verified"], k; return (r["lat"],r["lon"])

routes={}
# HAT 1 (geographic corridor order)
h1=[N["otogar"],g("cesme_merkez"),g("devlet_hastanesi"),g("altinyunus"),g("ilica_merkez"),
    g("alacati_merkez"),N["garaj"],N["cark"],B["moncheri"],B["kali"]]
# HAT 2
h2=[N["garaj"],N["port"]]
# HAT 3
h3=[N["otogar"],g("cesme_merkez"),g("migros_dalyan"),g("dalyan_mahallesi"),B["stage"]]
# HAT 4
h4=[N["otogar"],g("cesme_merkez"),g("cesme_limani"),g("ciftlik_merkez"),g("pirlanta_plaji"),
    B["flyinn"],B["epi"]]

for name,pts in [("hat1",h1),("hat2",h2),("hat3",h3),("hat4",h4)]:
    d=osrm("driving",pts)
    r=d["routes"][0]
    routes[name]={"coords":[[round(c[1],5),round(c[0],5)] for c in r["geometry"]["coordinates"]],
                  "distance_m":round(r["distance"]),"duration_s":round(r["duration"]),
                  "legs":[{"d":round(l["distance"]),"t":round(l["duration"])} for l in r["legs"]],
                  "snap_m":[round(w["distance"]) for w in d["waypoints"]],
                  "waypoints":[[round(p[0],6),round(p[1],6)] for p in pts]}
    print(name,routes[name]["distance_m"],"m",routes[name]["duration_s"],"s snaps",routes[name]["snap_m"])
    time.sleep(1)

# ---- Ayayorgi junction: divergence of Otogar->Dalyan vs Otogar->SoleMare ----
a=osrm("driving",[N["otogar"],g("dalyan_mahallesi")])["routes"][0]["geometry"]["coordinates"]
b=osrm("driving",[N["otogar"],B["solemare"]])["routes"][0]["geometry"]["coordinates"]
i=0
while i<min(len(a),len(b)) and abs(a[i][0]-b[i][0])<1e-6 and abs(a[i][1]-b[i][1])<1e-6: i+=1
junc=(round(a[i-1][1],6),round(a[i-1][0],6))
print("AYAYORGI JUNCTION",junc)

# walking leg: junction -> each Ayayorgi beach (foot profile as requested)
walk={}
for k in ("solemare","aura","mano"):
    d=osrm("foot",[junc,B[k]]); r=d["routes"][0]
    walk[k]={"coords":[[round(c[1],5),round(c[0],5)] for c in r["geometry"]["coordinates"]],
             "distance_m":round(r["distance"]),"osrm_duration_s":round(r["duration"])}
    print("walk",k,walk[k]["distance_m"],"m")
    time.sleep(1)

json.dump({"routes":routes,"junction":junc,"walk":walk,"nodes":N,"beaches":B,"stops":G},
          open(os.path.join(OUT,"routes.json"),"w"),ensure_ascii=False)
print("WROTE routes.json")
