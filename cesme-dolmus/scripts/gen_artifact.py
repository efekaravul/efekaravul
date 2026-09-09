# -*- coding: utf-8 -*-
"""Telefon için private Artifact sürümü: OSM tile yerine kendi vektör zemini."""
import json, math, os, sys
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,HERE)
import model as M
R=M.R; G=M.G
C=json.load(open(os.path.join(HERE,"..","data","coast_svg.json"),encoding="utf-8"))
LEAFLET_CSS=open(os.path.join(HERE,"..","vendor","leaflet-1.9.4.css"),encoding="utf-8").read()
DEST=sys.argv[1] if len(sys.argv)>1 else os.path.join(HERE,"..","artifact.html")

# --- kumsal yayları (plaj çevresi kıyı parçaları) ---
KX=math.cos(math.radians(38.29))
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
                if len(run)>1: out.append([[poly[j][1],poly[j][0]] for j in run])
                run=[i]
        if len(run)>1: out.append([[poly[j][1],poly[j][0]] for j in run])
    return out
SAND=[]
for b in M.BEACHES: SAND += near_arcs(b["lat"],b["lng"])

stops={}
for h,keys in M.STOP_LINES.items():
    stops[h]=[{"ad":M.STOP_LABEL[k],"lat":G[k]["lat"],"lng":G[k]["lon"]} for k in keys]
stops["hat1"].append({"ad":"Çark Plajı","lat":R["nodes"]["cark"][0],"lng":R["nodes"]["cark"][1]})
stops["hat2"]=[]

feats=[]
for h in ("hat1","hat2","hat3","hat4"):
    feats.append({"hat":h,"tip":"dolmus","c":[[c[0],c[1]] for c in R["routes"][h]["coords"]]})
for k,v in R["walk"].items():
    feats.append({"hat":"hat3","tip":"yuruyus","c":[[c[0],c[1]] for c in v["coords"]]})

DATA={
 "hatlar":{k:{"ad":v["ad"],"kisa":v["ad"].split(" · ")[0],"uzun":v["ad"].split(" · ")[1],
              "renk":v["renk"],"sefer":v["sefer"],"ucret":v["ucret"],"duraklar":v["duraklar"]}
           for k,v in M.HATLAR.items()},
 "rotalar":feats,"plajlar":M.BEACHES,"dugumler":M.NODES,"duraklar":stops,
 "kara":C["land"],"adalar":C["islands"],"kumsal":SAND,
 "offsets":{"solemare":[-56,-38],"aura":[-64,6],"mano":[30,42],
            "flyinn":[-56,-12],"playa":[24,46],"elias":[-34,-26]},
 "sapak":R["junction"],
 "dogrulanmayan":[M.UNVERIFIED_LABEL[k] for k in M.UNVERIFIED],
}

HTML = r"""<title>Alaçatı Dolmuş Rehberi</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700&family=Instrument+Serif:ital@0;1&display=swap">
<style>
__LEAFLET__
/* ===================== tokenlar ===================== */
:root{
  --ground:#EDF1F2; --surface:#FFFFFF; --surface-2:#F7F9F9;
  --ink:#16262B; --ink-2:#33474D; --muted:#5D7176; --faint:#8FA3A8;
  --rule:#D3DCDE; --rule-soft:#E3EAEB;
  --sea:#B7D6EE; --sea-deep:#9FC5E4; --sea-shallow:#CFE4F6;
  --land:#E2DBC0; --land-edge:#B3AE8A; --sand:#E5C06A;
  --uyari:#8A5406; --uyari-bg:#FBF0DA; --uyari-kenar:#E4C176;
  --h1:#1D9E75; --h2:#BA7517; --h3:#7F77DD; --h4:#D85A30;
  --yaya:#3A4B52;
  --pin:#C0392E; --pin-tek:#1D9E75;
  --golge:0 1px 2px rgba(18,38,44,.10), 0 6px 20px -8px rgba(18,38,44,.22);
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --ground:#0E181B; --surface:#16242A; --surface-2:#1B2E34;
    --ink:#E6EFF0; --ink-2:#C3D4D7; --muted:#93A9AE; --faint:#6C8288;
    --rule:#26383E; --rule-soft:#1F2F35;
    --sea:#16303F; --sea-deep:#102432; --sea-shallow:#1D3E50;
    --land:#3B4231; --land-edge:#5A6349; --sand:#A8873B;
    --uyari:#E9C784; --uyari-bg:#2E2413; --uyari-kenar:#5B4718;
    --pin:#D9564A;
    --golge:0 1px 2px rgba(0,0,0,.4), 0 8px 24px -10px rgba(0,0,0,.7);
  }
}
:root[data-theme="dark"]{
  --ground:#0E181B; --surface:#16242A; --surface-2:#1B2E34;
  --ink:#E6EFF0; --ink-2:#C3D4D7; --muted:#93A9AE; --faint:#6C8288;
  --rule:#26383E; --rule-soft:#1F2F35;
  --sea:#16303F; --sea-deep:#102432; --sea-shallow:#1D3E50;
  --land:#3B4231; --land-edge:#5A6349; --sand:#A8873B;
  --uyari:#E9C784; --uyari-bg:#2E2413; --uyari-kenar:#5B4718;
  --pin:#D9564A;
  --golge:0 1px 2px rgba(0,0,0,.4), 0 8px 24px -10px rgba(0,0,0,.7);
}

*{box-sizing:border-box}
body{
  margin:0; background:var(--ground); color:var(--ink);
  font-family:Archivo,"Helvetica Neue",Arial,sans-serif; font-size:15px; line-height:1.45;
  -webkit-text-size-adjust:100%;
}
.wrap{max-width:1360px;margin:0 auto;padding:0 14px 40px}

/* ===================== başlık ===================== */
header{padding:22px 0 14px}
.eyebrow{font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);
         font-weight:600;margin:0 0 6px}
h1{font-family:"Instrument Serif",Georgia,serif;font-weight:400;font-size:clamp(30px,7vw,46px);
   line-height:1.02;margin:0;letter-spacing:-.01em;text-wrap:balance}
h1 em{font-style:italic;color:var(--h1)}
.altbaslik{margin:8px 0 0;color:var(--ink-2);max-width:60ch;font-size:14.5px}

/* ===================== kontroller ===================== */
.kontroller{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:16px 0 12px}
.cip{border:1px solid var(--rule);background:var(--surface);color:var(--ink-2);
     border-radius:999px;padding:7px 13px;font:inherit;font-size:13px;font-weight:500;
     cursor:pointer;display:inline-flex;align-items:center;gap:7px;line-height:1;
     transition:background .13s,border-color .13s,color .13s}
.cip:hover{border-color:var(--faint)}
.cip:focus-visible{outline:2px solid var(--h1);outline-offset:2px}
.cip .sr{width:16px;height:4px;border-radius:2px;flex:none}
.cip[data-hat][aria-pressed="false"]{opacity:.45}
.cip[data-hat][aria-pressed="false"] .sr{opacity:.3}
.cip.tek[aria-pressed="true"]{background:var(--h1);border-color:var(--h1);color:#fff}
.segment{display:inline-flex;border:1px solid var(--rule);border-radius:999px;
         background:var(--surface);overflow:hidden;margin-left:auto}
.segment button{border:0;background:transparent;color:var(--muted);font:inherit;font-size:12.5px;
                font-weight:600;padding:7px 13px;cursor:pointer}
.segment button[aria-pressed="true"]{background:var(--ink);color:var(--ground)}
.segment button:focus-visible{outline:2px solid var(--h1);outline-offset:-2px}

/* ===================== düzen ===================== */
.duzen{display:grid;grid-template-columns:1fr;gap:16px}
@media (min-width:940px){
  .duzen{grid-template-columns:minmax(0,1.15fr) minmax(390px,.85fr);align-items:start}
  .haritaSar{position:sticky;top:14px}
}

/* ===================== harita ===================== */
.haritaSar{background:var(--surface);border:1px solid var(--rule);border-radius:14px;
           overflow:hidden;box-shadow:var(--golge)}
#map{height:min(46vh,430px);background:var(--sea)}
@media (min-width:940px){#map{height:min(78vh,700px)}}
.leaflet-container{background:var(--sea);font-family:Archivo,sans-serif;font-size:13px}
.leaflet-bar a{background:var(--surface);color:var(--ink);border-bottom-color:var(--rule)}
.leaflet-bar a:hover{background:var(--surface-2);color:var(--ink)}
.leaflet-control-attribution{background:color-mix(in srgb,var(--surface) 85%,transparent);
  color:var(--muted);font-size:10.5px}
.leaflet-control-attribution a{color:var(--muted)}
.leaflet-popup-content-wrapper,.leaflet-popup-tip{background:var(--surface);color:var(--ink);
  box-shadow:var(--golge)}
.leaflet-popup-content{margin:13px 15px;width:236px!important;line-height:1.42}
.leaflet-popup-close-button{color:var(--muted)!important}

.poi{position:relative;width:0;height:0}
.poi svg{position:absolute;left:-90px;top:-90px;width:180px;height:180px;overflow:visible;
         pointer-events:none}
.rozet{position:absolute;transform:translate(-50%,-50%);width:25px;height:25px;border-radius:50%;
       background:var(--pin);color:#fff;border:2.5px solid var(--surface);
       box-shadow:0 1px 5px rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center;
       font-weight:700;font-size:12.5px;cursor:pointer;font-variant-numeric:tabular-nums}
.rozet.tek{background:var(--pin-tek)}
.rozet.vurgu{outline:3px solid var(--ink);outline-offset:2px}
.cekirdek{position:absolute;transform:translate(-50%,-50%);width:7px;height:7px;border-radius:50%;
          background:var(--surface);border:2px solid var(--pin)}
.dugum{width:19px;height:19px;background:var(--ink);border:2.5px solid var(--surface);border-radius:3px;
       box-shadow:0 1px 4px rgba(0,0,0,.35);display:flex;align-items:center;justify-content:center}
.dugum i{width:5px;height:5px;background:var(--surface);display:block}
.durak{width:10px;height:10px;border-radius:50%;background:var(--surface);
       border:2.5px solid var(--faint)}

.pp h3{margin:0 0 2px;font-size:15px;font-weight:600}
.pp .yer{color:var(--muted);font-size:11px;margin-bottom:8px;letter-spacing:.02em}
.pp ol{margin:0 0 9px;padding-left:15px;font-size:12px;color:var(--ink-2)}
.pp .kv{display:flex;justify-content:space-between;gap:10px;padding:4px 0;
        border-top:1px solid var(--rule-soft);font-size:12.5px}
.pp .kv span:first-child{color:var(--muted)}
.pp .kv b{font-variant-numeric:tabular-nums}

/* ===================== liste ===================== */
.liste{display:flex;flex-direction:column;gap:9px}
.kart{background:var(--surface);border:1px solid var(--rule);border-radius:12px;
      padding:12px 13px;display:grid;grid-template-columns:auto 1fr;gap:11px;
      cursor:pointer;text-align:left;font:inherit;color:inherit;width:100%;
      box-shadow:var(--golge);transition:border-color .14s,transform .14s}
.kart:hover{border-color:var(--faint)}
.kart:focus-visible{outline:2px solid var(--h1);outline-offset:2px}
.kart[aria-current="true"]{border-color:var(--ink);transform:translateY(-1px)}
.no{width:29px;height:29px;border-radius:50%;background:var(--pin);color:#fff;font-weight:700;
    font-size:13px;display:flex;align-items:center;justify-content:center;flex:none;
    font-variant-numeric:tabular-nums}
.no.tek{background:var(--pin-tek)}
.kbas{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap}
.kbas h3{margin:0;font-size:15.5px;font-weight:600;letter-spacing:-.005em}
.kbas .yer{font-size:11.5px;color:var(--muted)}
.serit{display:flex;gap:3px;margin:7px 0 9px}
.serit i{height:4px;border-radius:2px;display:block}
.veri{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}
.veri div{border-left:2px solid var(--rule-soft);padding-left:8px}
.veri dt{font-size:9.5px;letter-spacing:.13em;text-transform:uppercase;color:var(--faint);
         font-weight:600;margin:0 0 2px}
.veri dd{margin:0;font-size:14px;font-weight:600;font-variant-numeric:tabular-nums;line-height:1.2}
.veri dd small{display:block;font-size:10.5px;font-weight:400;color:var(--muted);
               letter-spacing:0;margin-top:2px;line-height:1.3}
.rozetDg{display:inline-block;background:var(--uyari-bg);color:var(--uyari);
         border:1px solid var(--uyari-kenar);border-radius:4px;padding:1px 5px;
         font-size:10.5px;font-weight:600;letter-spacing:.01em}
.kirilim{margin-top:9px;font-size:11.5px;color:var(--muted);border-top:1px dashed var(--rule);
         padding-top:7px;display:flex;flex-direction:column;gap:1px}
.kirilim .bacak{color:var(--ink-2)}
.kirilim .sayac{margin-top:3px;font-variant-numeric:tabular-nums}

/* ===================== alt bilgi ===================== */
.notlar{margin-top:22px;border-top:1px solid var(--rule);padding-top:16px;
        display:grid;gap:14px;grid-template-columns:1fr}
@media (min-width:760px){.notlar{grid-template-columns:1fr 1fr}}
.notlar h2{font-family:"Instrument Serif",Georgia,serif;font-weight:400;font-size:20px;margin:0 0 6px}
.notlar p,.notlar li{font-size:12.5px;color:var(--ink-2);margin:0 0 6px}
.notlar ul{margin:0;padding-left:16px}
.notlar .uy{background:var(--uyari-bg);border:1px solid var(--uyari-kenar);color:var(--uyari);
            border-radius:9px;padding:11px 13px}
.notlar .uy strong{display:block;margin-bottom:4px;font-size:12.5px}
.tarife{width:100%;border-collapse:collapse;font-size:12px;margin-top:4px}
.tarife th,.tarife td{text-align:left;padding:4px 8px 4px 0;border-bottom:1px solid var(--rule-soft);
                      vertical-align:top}
.tarife th{color:var(--faint);font-size:9.5px;letter-spacing:.12em;text-transform:uppercase;font-weight:600}
.tarife td:last-child{font-variant-numeric:tabular-nums;white-space:nowrap}
.kunye{margin-top:18px;font-size:11px;color:var(--faint);border-top:1px solid var(--rule-soft);
       padding-top:12px}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
</style>

<div class="wrap">
<header>
  <p class="eyebrow">10–13 Eylül · Alaçatı · araç yok</p>
  <h1>Çeşme'de <em>dolmuşla</em> beach club</h1>
  <p class="altbaslik">10 kulüp, 4 dolmuş hattı ve Ayayorgi'ye inen yürüyüş. Süreler
     Alaçatı Dolmuş Garajı'ndan hesaplandı. Bir kulübe dokun, harita oraya gitsin.</p>
</header>

<div class="kontroller" id="kontroller"></div>

<div class="duzen">
  <div class="haritaSar"><div id="map"></div></div>
  <div class="liste" id="liste"></div>
</div>

<div class="notlar" id="notlar"></div>
<p class="kunye">Kıyı çizgisi ve durak konumları © OpenStreetMap katkıcıları (ODbL), Nominatim
   ve Overpass API üzerinden. Güzergâh geometrisi OSRM. Harita karosu yok — zemin, OSM kıyı
   verisinden çizildi, bu yüzden sokak isimleri görünmez.</p>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"></script>
<script>
const D = __DATA__;
const HK = ['hat1','hat2','hat3','hat4'];
const acik = {hat1:true,hat2:true,hat3:true,hat4:true};
let tekMod = false, sira = 'sure', secili = null;

/* ---------- süre/ücret yardımcıları ---------- */
function bekleme(b){ return b.bekleme.filter(x=>x[1]!==null).reduce((a,x)=>a+x[1],0); }
function bilinmez(b){ return b.bekleme.some(x=>x[1]===null); }
function toplam(b){ return b.aracIci + b.yuruyusDk + bekleme(b); }

/* ---------- harita ---------- */
const map = L.map('map',{zoomControl:true,minZoom:10,maxZoom:15,scrollWheelZoom:false,
                         attributionControl:true});
map.attributionControl.setPrefix(false).addAttribution('© OpenStreetMap · OSRM');

const cs = getComputedStyle(document.documentElement);
const tok = n => cs.getPropertyValue(n).trim();

/* zemin: OSM kıyı çizgisinden çizilen kara + adalar + kumsallar */
const zemin = L.layerGroup().addTo(map);
function boya(){
  zemin.clearLayers();
  const kara = tok('--land'), kenar = tok('--land-edge'),
        sig = tok('--sea-shallow'), kum = tok('--sand');
  D.kara.concat(D.adalar).forEach(p => {
    const ll = p.map(c=>[c[1],c[0]]);
    L.polygon(ll,{color:sig,weight:14,opacity:.85,fill:false,interactive:false}).addTo(zemin);
    L.polygon(ll,{color:kenar,weight:1.4,fillColor:kara,fillOpacity:1,interactive:false}).addTo(zemin);
  });
  D.kumsal.forEach(a => L.polyline(a,{color:kum,weight:5,opacity:.95,lineCap:'round',
                                      interactive:false}).addTo(zemin));
}
boya();
matchMedia('(prefers-color-scheme: dark)').addEventListener('change',boya);

const katman = {};
HK.forEach(h => katman[h] = L.layerGroup().addTo(map));
D.rotalar.forEach(f => {
  if (f.tip === 'dolmus'){
    L.polyline(f.c,{color:'#fff',weight:8,opacity:.5,interactive:false}).addTo(katman[f.hat]);
    L.polyline(f.c,{color:D.hatlar[f.hat].renk,weight:4.5,lineCap:'round',lineJoin:'round'})
     .bindTooltip(D.hatlar[f.hat].ad,{sticky:true}).addTo(katman[f.hat]);
  } else {
    L.polyline(f.c,{color:'#fff',weight:7,opacity:.45,interactive:false}).addTo(katman[f.hat]);
    L.polyline(f.c,{color:tok('--yaya'),weight:3,dashArray:'2,7',lineCap:'round'})
     .bindTooltip('Yürüyüş ~10-15 dk · Ayayorgi sapağı → koy',{sticky:true}).addTo(katman[f.hat]);
  }
});
Object.keys(D.duraklar).forEach(h => D.duraklar[h].forEach(s =>
  L.marker([s.lat,s.lng],{icon:L.divIcon({className:'',html:'<div class="durak"></div>',
    iconSize:[10,10],iconAnchor:[5,5]}),keyboard:false})
   .bindTooltip(s.ad,{direction:'top'}).addTo(katman[h])));
L.marker(D.sapak,{icon:L.divIcon({className:'',
    html:'<div class="durak" style="border-color:var(--yaya)"></div>',
    iconSize:[10,10],iconAnchor:[5,5]})})
 .bindTooltip('Ayayorgi sapağı — burada in, koya yürü',{direction:'top'}).addTo(katman.hat3);

D.dugumler.forEach(n =>
  L.marker([n.lat,n.lng],{icon:L.divIcon({className:'',html:'<div class="dugum"><i></i></div>',
    iconSize:[19,19],iconAnchor:[9.5,9.5]}),zIndexOffset:400})
   .bindTooltip(n.ad,{direction:'top',offset:[0,-10]})
   .bindPopup('<div class="pp"><h3>'+n.ad+'</h3><div class="yer">'+n.not+'</div></div>')
   .addTo(map));

function popupHTML(b){
  const bek = bekleme(b), bil = bilinmez(b);
  let h = '<div class="pp"><h3>'+b.id+'. '+b.ad+'</h3><div class="yer">'+b.yer+'</div>';
  h += '<ol>'+b.rota.metin.map(t=>'<li>'+t+'</li>').join('')+'</ol>';
  h += '<div class="kv"><span>Süre</span><b>≈ '+toplam(b)+' dk</b></div>';
  h += '<div class="kv"><span>Aktarma</span><b>'+(b.aktarma?b.aktarma+' · Çeşme Otogar':'yok')+'</b></div>';
  h += '<div class="kv"><span>Ücret</span><b>'+(b.ucret.toplam!==null?b.ucret.toplam+' TL':
        '<span class="rozetDg">doğrulanmadı</span>')+'</b></div>';
  if (bil) h += '<div class="kv"><span>Not</span><b style="font-weight:400;font-size:11.5px">'
              + 'Hat 4 sefer sıklığı doğrulanmadı</b></div>';
  return h+'</div>';
}

const marker = {};
D.plajlar.forEach(b => {
  const o = D.offsets[b.key] || [0,0], dx=o[0], dy=o[1], kay = Math.hypot(dx,dy) > 4;
  const svg = kay ? '<svg><line x1="90" y1="90" x2="'+(90+dx)+'" y2="'+(90+dy)+
      '" stroke="var(--surface)" stroke-width="3.5"/><line x1="90" y1="90" x2="'+(90+dx)+
      '" y2="'+(90+dy)+'" stroke="var(--pin)" stroke-width="1.5"/></svg>' : '';
  const cek = kay ? '<div class="cekirdek" style="left:0;top:0"></div>' : '';
  const m = L.marker([b.lat,b.lng],{
      icon:L.divIcon({className:'',iconSize:[0,0],iconAnchor:[0,0],
        html:'<div class="poi">'+svg+cek+'<div class="rozet'+(b.tek?' tek':'')+
             '" data-key="'+b.key+'" style="left:'+dx+'px;top:'+dy+'px">'+b.id+'</div></div>'}),
      zIndexOffset:600+b.id})
    .bindPopup(popupHTML(b),{maxWidth:270,autoPanPadding:[20,40]})
    .bindTooltip(b.id+'. '+b.ad,{direction:'top',offset:[dx,dy-17]});
  m.on('popupopen',()=>vurgula(b.key,false));
  marker[b.key] = m; m.addTo(map);
});

const TUM = L.latLngBounds(D.plajlar.map(b=>[b.lat,b.lng])
              .concat(D.dugumler.map(n=>[n.lat,n.lng])));
const dar = () => matchMedia('(max-width:939px)').matches;
function sigdir(bnds){ map.fitBounds(bnds,{padding: dar()?[26,26]:[46,46]}); }
sigdir(TUM);

/* ---------- kontroller ---------- */
const kn = document.getElementById('kontroller');
kn.innerHTML =
  '<button class="cip tek" id="tekBtn" type="button" aria-pressed="false">'
+ '<span class="sr" style="background:var(--pin-tek)"></span>Alaçatı\'dan tek dolmuşla</button>'
+ HK.map(h=>'<button class="cip" type="button" data-hat="'+h+'" aria-pressed="true">'
+ '<span class="sr" style="background:'+D.hatlar[h].renk+'"></span>'+D.hatlar[h].kisa+'</button>').join('')
+ '<div class="segment" role="group" aria-label="Sıralama">'
+ '<button type="button" data-sira="sure" aria-pressed="true">Süreye göre</button>'
+ '<button type="button" data-sira="no" aria-pressed="false">Numaraya göre</button></div>';

kn.querySelectorAll('[data-hat]').forEach(btn => btn.addEventListener('click',()=>{
  const h = btn.dataset.hat, yeni = !acik[h];
  acik[h] = yeni; btn.setAttribute('aria-pressed', yeni);
  yeni ? katman[h].addTo(map) : map.removeLayer(katman[h]);
}));
kn.querySelectorAll('[data-sira]').forEach(btn => btn.addEventListener('click',()=>{
  sira = btn.dataset.sira;
  kn.querySelectorAll('[data-sira]').forEach(b=>b.setAttribute('aria-pressed', b===btn));
  ciz();
}));
document.getElementById('tekBtn').addEventListener('click',e=>{
  tekMod = !tekMod; e.currentTarget.setAttribute('aria-pressed',tekMod);
  D.plajlar.forEach(b=>{
    if (tekMod && !b.tek) map.removeLayer(marker[b.key]);
    else if (!map.hasLayer(marker[b.key])) marker[b.key].addTo(map);
  });
  map.closePopup();
  sigdir(tekMod ? L.latLngBounds(D.plajlar.filter(b=>b.tek).map(b=>[b.lat,b.lng])
                    .concat([[D.dugumler[0].lat,D.dugumler[0].lng]])) : TUM);
  ciz();
});

/* ---------- liste ---------- */
function serit(b){
  return '<div class="serit">'+b.hatlar.map(h=>'<i style="background:'+D.hatlar[h].renk
       + ';width:'+(b.hatlar.length>1?28:56)+'px"></i>').join('')
       + (b.yuruyusDk?'<i style="background:var(--yaya);width:16px;opacity:.55"></i>':'')+'</div>';
}
function kartHTML(b){
  const bek = bekleme(b), bil = bilinmez(b);
  const kir = [b.aracIci+' dk araç içi']
    .concat(bek?[bek+' dk bekleme']:[])
    .concat(b.yuruyusDk?[b.yuruyusDk+' dk yürüyüş ('+b.yuruyusM+' m)']:[]).join(' · ');
  return '<button class="kart" type="button" data-key="'+b.key+'"'
    + (secili===b.key?' aria-current="true"':'')+'>'
    + '<span class="no'+(b.tek?' tek':'')+'">'+b.id+'</span><span>'
    + '<span class="kbas"><h3>'+b.ad+'</h3><span class="yer">'+b.yer+'</span></span>'
    + serit(b)
    + '<dl class="veri">'
    + '<div><dt>Süre</dt><dd>'+toplam(b)+' dk'+(bil?'<small>+ aktarma beklemesi doğrulanmadı</small>':'')+'</dd></div>'
    + '<div><dt>Aktarma</dt><dd>'+(b.aktarma?b.aktarma:'yok')
    + (b.aktarma?'<small>Çeşme Otogar</small>':'<small>tek dolmuş</small>')+'</dd></div>'
    + '<div><dt>Ücret</dt><dd>'+(b.ucret.toplam!==null
        ? b.ucret.toplam+' TL'+(b.ucret.kalemler.length>1
            ? '<small>'+b.ucret.kalemler.map(k=>k[0]+' '+k[1]).join('<br>+ ')+'</small>' : '')
        : '<span class="rozetDg">doğrulanmadı</span>')+'</dd></div>'
    + '</dl>'
    + '<span class="kirilim">'+b.rota.metin.map(t=>'<span class="bacak">'+t+'</span>').join('')
    + '<span class="sayac">'+kir+'</span></span>'
    + '</span></button>';
}
function ciz(){
  const list = D.plajlar.filter(b=>!tekMod||b.tek)
    .slice().sort((a,b)=> sira==='sure' ? toplam(a)-toplam(b) || a.id-b.id : a.id-b.id);
  document.getElementById('liste').innerHTML = list.map(kartHTML).join('');
  document.querySelectorAll('.kart').forEach(k => k.addEventListener('click',()=>sec(k.dataset.key)));
}
function vurgula(key,kaydir){
  secili = key;
  document.querySelectorAll('.kart').forEach(k =>
    k.setAttribute('aria-current', k.dataset.key===key));
  document.querySelectorAll('.rozet').forEach(r =>
    r.classList.toggle('vurgu', r.dataset.key===key));
  if (kaydir){
    const el = document.querySelector('.kart[data-key="'+key+'"]');
    if (el) el.scrollIntoView({block:'nearest',behavior:'smooth'});
  }
}
function sec(key){
  const b = D.plajlar.find(x=>x.key===key);
  map.setView([b.lat,b.lng], 14, {animate:true});
  marker[key].openPopup();
  vurgula(key,false);
  if (dar()) document.getElementById('map').scrollIntoView({block:'center',behavior:'smooth'});
}
ciz();

/* ---------- notlar ---------- */
document.getElementById('notlar').innerHTML =
  '<div><h2>Hatlar ve tarife</h2>'
+ HK.map(h=>{const t=D.hatlar[h];
    return '<p style="margin-top:10px"><b style="color:'+t.renk+'">'+t.kisa+'</b> — '+t.uzun+'<br>'
    + '<span style="color:var(--muted);font-size:11.5px">'+t.duraklar.join(' › ')+'</span></p>'
    + '<table class="tarife"><tr><th>Sefer</th><td>'
    + (t.sefer.length?t.sefer.join('<br>'):'<span class="rozetDg">doğrulanmadı</span>')+'</td></tr>'
    + '<tr><th>Ücret</th><td>'
    + (t.ucret.length?t.ucret.join('<br>'):'<span class="rozetDg">doğrulanmadı</span>')+'</td></tr></table>';
  }).join('')
+ '</div>'
+ '<div><div class="uy"><strong>Bu duraklar OpenStreetMap\'te bulunamadı</strong>'
+ D.dogrulanmayan.join(' · ')+'. Koordinat uydurulmadı; haritada nokta olarak yoklar. '
+ 'Bedir Plajı bulunamadığı için Hat 1 çizgisi Kali Beach Club\'da bitiyor.</div>'
+ '<h2 style="margin-top:16px">Süre nasıl hesaplandı</h2>'
+ '<ul><li><b>Araç içi</b>: OSRM serbest akış süresi × 1.35 (dolmuş duraklamaları payı — varsayım).</li>'
+ '<li><b>Yürüyüş</b>: OSRM mesafesi ÷ 1.25 m/s. Ayayorgi sapağından 654–868 m.</li>'
+ '<li><b>Bekleme</b>: sefer sıklığının yarısı. Hat 1 → 4 dk, Hat 3 → 15 dk. '
+ 'Hat 4\'ün sefer sıklığı verilmediği için o hattın beklemesi hesaba katılmadı.</li>'
+ '<li>Mon Cheri, Kali ve Ayayorgi üçlüsünde ücret <b>ara durak tarifesi</b> gerektiriyor; '
+ 'verilmediği için rakam gösterilmiyor.</li></ul>'
+ '<p style="color:var(--muted)">Yolculuktan önce güncel tarifeyi teyit et.</p></div>';
</script>
"""

html = (HTML.replace("__LEAFLET__", LEAFLET_CSS)
            .replace("__DATA__", json.dumps(DATA, ensure_ascii=False, separators=(',',':'))))
open(DEST,"w",encoding="utf-8").write(html)
print("WROTE",DEST,len(html),"bytes")
