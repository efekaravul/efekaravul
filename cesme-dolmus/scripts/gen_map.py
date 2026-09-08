# -*- coding: utf-8 -*-
import json, os, sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import model as M
R=M.R; G=M.G
OUTHTML=sys.argv[1] if len(sys.argv)>1 else "/home/user/efekaravul/map.html"

def fc():
    feats=[]
    for h in ("hat1","hat2","hat3","hat4"):
        r=R["routes"][h]
        feats.append({"type":"Feature","properties":{"hat":h,"tip":"dolmus"},
          "geometry":{"type":"LineString","coordinates":[[c[1],c[0]] for c in r["coords"]]}})
    for k,v in R["walk"].items():
        feats.append({"type":"Feature","properties":{"hat":"hat3","tip":"yuruyus","hedef":k},
          "geometry":{"type":"LineString","coordinates":[[c[1],c[0]] for c in v["coords"]]}})
    return {"type":"FeatureCollection","features":feats}

stops={}
for h,keys in M.STOP_LINES.items():
    stops[h]=[{"ad":M.STOP_LABEL[k],"lat":G[k]["lat"],"lng":G[k]["lon"]} for k in keys]
stops["hat1"].append({"ad":"Çark Plajı","lat":R["nodes"]["cark"][0],"lng":R["nodes"]["cark"][1]})
stops["hat2"]=[]

OFFSETS={"solemare":[-56,-38],"aura":[-64,6],"mano":[30,42],
         "flyinn":[-56,-12],"playa":[24,46],"elias":[-34,-26]}

DATA={"hatlar":{k:{"ad":v["ad"],"renk":v["renk"],"sefer":v["sefer"],"ucret":v["ucret"],
                   "duraklar":v["duraklar"]} for k,v in M.HATLAR.items()},
      "rotalar":fc(),"plajlar":M.BEACHES,"dugumler":M.NODES,"duraklar":stops,
      "offsets":OFFSETS,"sapak":R["junction"],
      "dogrulanmayan":[M.UNVERIFIED_LABEL[k] for k in M.UNVERIFIED]}

HTML = r"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5">
<title>Çeşme Beach Club &amp; Dolmuş Haritası</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css"
      integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin=""/>
<style>
  :root{
    --bg:#0f1720; --panel:#ffffff; --ink:#16222c; --muted:#5b6b78;
    --line:#dfe6ec; --accent:#0f6f9c;
    --h1:#1D9E75; --h2:#BA7517; --h3:#7F77DD; --h4:#D85A30;
  }
  *{box-sizing:border-box}
  html,body{height:100%;margin:0}
  body{font:14px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;color:var(--ink);background:var(--bg)}
  #ust{position:absolute;top:0;left:0;right:0;z-index:1200;display:flex;gap:10px;align-items:center;
       flex-wrap:wrap;padding:8px 12px;background:rgba(15,23,32,.94);color:#eef4f8;
       box-shadow:0 1px 0 rgba(255,255,255,.08)}
  #ust h1{font-size:15px;margin:0;font-weight:650;letter-spacing:.2px;white-space:nowrap}
  #ust .alt{font-size:11.5px;color:#9fb3c2;white-space:nowrap}
  #filtre{margin-left:auto;border:1px solid #35505f;background:#17242f;color:#dcebf4;
          padding:7px 13px;border-radius:999px;cursor:pointer;font:inherit;font-size:12.5px;font-weight:600}
  #filtre:hover{background:#1e3340}
  #filtre[aria-pressed="true"]{background:#1D9E75;border-color:#1D9E75;color:#04231a}
  #map{position:absolute;top:0;left:0;right:0;bottom:0;background:#a8cfe8}
  .leaflet-top.leaflet-left{margin-top:52px}

  /* --- plaj rozeti + leader line --- */
  .poi{position:relative;width:0;height:0}
  .poi svg{position:absolute;left:-90px;top:-90px;width:180px;height:180px;overflow:visible;pointer-events:none}
  .rozet{position:absolute;transform:translate(-50%,-50%);width:26px;height:26px;border-radius:50%;
         background:#c8362f;color:#fff;border:2.5px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.45);
         display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px;cursor:pointer}
  .rozet.tek{background:#1D9E75}
  .cekirdek{position:absolute;transform:translate(-50%,-50%);width:7px;height:7px;border-radius:50%;
            background:#fff;border:2px solid #c8362f;box-shadow:0 0 0 1px rgba(0,0,0,.25)}
  .dugum{width:20px;height:20px;background:#16222c;border:2.5px solid #fff;border-radius:3px;
         box-shadow:0 1px 4px rgba(0,0,0,.45);display:flex;align-items:center;justify-content:center}
  .dugum i{width:6px;height:6px;background:#fff;display:block}
  .durak{width:11px;height:11px;border-radius:50%;background:#fff;border:2.5px solid #7a8a96;
         box-shadow:0 1px 2px rgba(0,0,0,.3)}
  .gizli{display:none !important}

  /* --- popup --- */
  .leaflet-popup-content{margin:12px 14px;width:270px !important}
  .pp h3{margin:0 0 2px;font-size:15px}
  .pp .yer{color:var(--muted);font-size:11.5px;margin-bottom:9px}
  .pp table{width:100%;border-collapse:collapse;font-size:12.5px}
  .pp td{padding:3.5px 0;vertical-align:top;border-top:1px solid var(--line)}
  .pp td:first-child{color:var(--muted);width:88px;padding-right:8px}
  .pp .yol{margin:0;padding-left:15px;font-size:12px}
  .pp .yol li{margin:1px 0}
  .pp .not{margin-top:8px;padding:6px 8px;background:#fff6e5;border-left:3px solid #e0a52a;
           font-size:11.5px;color:#5c4708;border-radius:0 3px 3px 0}
  .pp b.sure{font-size:14px}
  .pp .dg{color:#a4620b;font-weight:600}

  /* --- lejant --- */
  #lejant{position:absolute;right:10px;bottom:22px;z-index:1100;background:var(--panel);
          border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,.3);padding:10px 12px;max-width:250px}
  #lejant h4{margin:0 0 7px;font-size:12px;letter-spacing:.4px;text-transform:uppercase;color:var(--muted)}
  #lejant .sat{display:flex;align-items:center;gap:8px;margin:4px 0;font-size:12px}
  #lejant .cizgi{width:26px;height:0;border-top:4px solid;border-radius:2px;flex:none}
  #lejant .kesik{border-top:3px dashed #444}
  #lejant .ayr{border-top:1px solid var(--line);margin:8px 0 6px}
  #lejant .mk{width:26px;display:flex;justify-content:center;flex:none}
  #lejant .mini-r{width:18px;height:18px;border-radius:50%;background:#c8362f;color:#fff;border:2px solid #fff;
                  box-shadow:0 0 0 1px rgba(0,0,0,.2);font-size:10px;font-weight:700;display:flex;align-items:center;justify-content:center}
  #lejant .mini-k{width:15px;height:15px;background:#16222c;border:2px solid #fff;border-radius:2px;box-shadow:0 0 0 1px rgba(0,0,0,.2)}
  #lejant .mini-d{width:11px;height:11px;border-radius:50%;background:#fff;border:2.5px solid #7a8a96}
  #lejant button{margin-top:8px;width:100%;border:1px solid var(--line);background:#f6f8fa;border-radius:5px;
                 padding:5px;font:inherit;font-size:11.5px;cursor:pointer;color:var(--muted)}
  #lejant.kapali .govde{display:none}
  .leaflet-control-layers{font-size:13px}
  .leaflet-control-layers-list{padding:2px 4px}
  @media (max-width:640px){
    #ust h1{font-size:13.5px;white-space:normal}
    #ust .alt{display:none}
    #filtre{font-size:11.5px;padding:6px 10px}
    #lejant{right:6px;bottom:18px;max-width:190px;padding:8px 9px;font-size:11px}
    #lejant .sat{font-size:11px;margin:3px 0}
    .leaflet-popup-content{width:220px !important}
    .leaflet-top.leaflet-left{margin-top:66px}
    .leaflet-control-layers-expanded{font-size:11.5px;max-width:calc(100vw - 70px)}
  }
</style>
</head>
<body>
<div id="ust">
  <h1>Çeşme Beach Club &amp; Dolmuş Haritası</h1>
  <span class="alt">10 beach club · 4 dolmuş hattı · araçsız ulaşım</span>
  <button id="filtre" type="button" aria-pressed="false">Alaçatı'dan tek dolmuşla gidilenler</button>
</div>
<div id="map"></div>
<div id="lejant">
  <h4>Lejant</h4>
  <div class="govde" id="lejantGovde"></div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"
        integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
<script>
/* ------------------------------------------------------------------
   VERİ — build sırasında gömüldü. Çalışma anında tile dışında hiçbir
   ağ isteği yapılmaz. Rota geometrisi: OSRM (router.project-osrm.org).
   ------------------------------------------------------------------ */
const D = __DATA__;

const map = L.map('map', { zoomControl:true, scrollWheelZoom:true, tap:true });
L.control.scale({imperial:false}).addTo(map);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom:19, attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> katkıcıları · rotalar: OSRM'
}).addTo(map);

/* ---------- katmanlar ---------- */
const katman = {}, plajKatman = {};
['hat1','hat2','hat3','hat4'].forEach(h => katman[h] = L.layerGroup());

D.rotalar.features.forEach(f => {
  const h = f.properties.hat, yur = f.properties.tip === 'yuruyus';
  const pts = f.geometry.coordinates.map(c => [c[1], c[0]]);
  if (!yur) {
    L.polyline(pts, {color:'#ffffff', weight:8, opacity:.55, lineCap:'round', lineJoin:'round',
                     interactive:false}).addTo(katman[h]);
    L.polyline(pts, {color:D.hatlar[h].renk, weight:4.5, opacity:1, lineCap:'round', lineJoin:'round'})
      .bindTooltip(D.hatlar[h].ad, {sticky:true}).addTo(katman[h]);
  } else {
    L.polyline(pts, {color:'#ffffff', weight:7, opacity:.5, interactive:false}).addTo(katman[h]);
    L.polyline(pts, {color:'#2f3b45', weight:3, dashArray:'2,7', lineCap:'round'})
      .bindTooltip('Yürüyüş ~10-15 dk · Ayayorgi sapağı → koy', {sticky:true}).addTo(katman[h]);
  }
});

/* ara duraklar */
Object.keys(D.duraklar).forEach(h => D.duraklar[h].forEach(s => {
  L.marker([s.lat, s.lng], {icon:L.divIcon({className:'', html:'<div class="durak"></div>',
      iconSize:[11,11], iconAnchor:[5.5,5.5]}), keyboard:false})
   .bindTooltip(s.ad + ' — ' + D.hatlar[h].ad.split(' · ')[0], {direction:'top'})
   .addTo(katman[h]);
}));

/* Ayayorgi sapağı (Hat 3 iniş noktası) */
L.marker(D.sapak, {icon:L.divIcon({className:'', html:'<div class="durak" style="border-color:#2f3b45"></div>',
    iconSize:[11,11], iconAnchor:[5.5,5.5]})})
 .bindTooltip('Ayayorgi sapağı — burada in, koya yürü', {direction:'top'}).addTo(katman.hat3);

['hat1','hat2','hat3','hat4'].forEach(h => katman[h].addTo(map));

/* ---------- düğümler (kare marker) ---------- */
const dugumKatman = L.layerGroup().addTo(map);
D.dugumler.forEach(n => {
  L.marker([n.lat, n.lng], {icon:L.divIcon({className:'', html:'<div class="dugum"><i></i></div>',
      iconSize:[20,20], iconAnchor:[10,10]}), zIndexOffset:400})
   .bindPopup('<div class="pp"><h3>'+n.ad+'</h3><div class="yer">'+n.not+'</div></div>')
   .bindTooltip(n.ad, {direction:'top', offset:[0,-10]})
   .addTo(dugumKatman);
});

/* ---------- plajlar (numaralı yuvarlak + offset & leader line) ---------- */
function dk(n){ return n + ' dk'; }
function popupHTML(b){
  const bek = b.bekleme.filter(x => x[1] !== null).reduce((a,x)=>a+x[1], 0);
  const bilinmeyen = b.bekleme.some(x => x[1] === null);
  const toplam = b.aracIci + b.yuruyusDk + bek;
  let h = '<div class="pp"><h3>'+b.id+'. '+b.ad+'</h3><div class="yer">'+b.yer+'</div>';
  h += '<ol class="yol">'+b.rota.metin.map(t=>'<li>'+t+'</li>').join('')+'</ol>';
  h += '<table>';
  h += '<tr><td>Süre</td><td><b class="sure">≈ '+dk(toplam)+'</b><br>'
     + '<span style="color:#5b6b78;font-size:11.5px">'+dk(b.aracIci)+' araç içi'
     + (b.yuruyusDk ? ' · '+dk(b.yuruyusDk)+' yürüyüş ('+b.yuruyusM+' m)' : '')
     + (bek ? ' · '+dk(bek)+' bekleme' : '')
     + '</span>'
     + (bilinmeyen ? '<br><span class="dg">+ aktarma beklemesi: sefer sıklığı doğrulanmadı</span>' : '')
     + '</td></tr>';
  h += '<tr><td>Aktarma</td><td>'+(b.aktarma===0 ? 'Yok — tek dolmuş' : b.aktarma+' (Çeşme Otogar)')+'</td></tr>';
  h += '<tr><td>Ücret</td><td>'
     + (b.ucret.toplam !== null
        ? '<b>'+b.ucret.toplam+' TL</b><br><span style="color:#5b6b78;font-size:11.5px">'
          + b.ucret.kalemler.map(k=>k[0]+' '+k[1]+' TL').join(' + ')+'</span>'
        : '<span class="dg">doğrulanmadı</span>'
          + (b.ucret.kalemler.length ? '<br><span style="color:#5b6b78;font-size:11.5px">'
             + b.ucret.kalemler.map(k=>k[0]+' '+k[1]+' TL').join(' + ')+' + ?</span>' : ''))
     + '</td></tr>';
  h += '</table>';
  if (b.ucretNot) h += '<div class="not">'+b.ucretNot+'</div>';
  return h + '</div>';
}

const plajMarker = {};
D.plajlar.forEach(b => {
  const off = D.offsets[b.key] || [0,0];
  const dx = off[0], dy = off[1], var_ = Math.hypot(dx,dy) > 4;
  const svg = var_
    ? '<svg><line x1="90" y1="90" x2="'+(90+dx)+'" y2="'+(90+dy)+'" stroke="#ffffff" stroke-width="3.5"/>'
      + '<line x1="90" y1="90" x2="'+(90+dx)+'" y2="'+(90+dy)+'" stroke="#c8362f" stroke-width="1.6"/></svg>'
    : '';
  const cek = var_ ? '<div class="cekirdek" style="left:0;top:0"></div>' : '';
  const html = '<div class="poi">'+svg+cek
    + '<div class="rozet'+(b.tek?' tek':'')+'" style="left:'+dx+'px;top:'+dy+'px">'+b.id+'</div></div>';
  const m = L.marker([b.lat, b.lng], {
      icon: L.divIcon({className:'', html:html, iconSize:[0,0], iconAnchor:[0,0]}),
      zIndexOffset: 600 + b.id
    })
    .bindPopup(popupHTML(b), {maxWidth:300, autoPanPadding:[24,60]})
    .bindTooltip(b.id+'. '+b.ad, {direction:'top', offset:[dx, dy-18]});
  plajMarker[b.key] = m;
  b.hatlar.forEach(h => { (plajKatman[h] = plajKatman[h] || []).push(m); });
  m.addTo(map);
});

/* ---------- katman kontrolü (sol üst) ---------- */
const kontrol = {};
['hat1','hat2','hat3','hat4'].forEach(h => {
  const c = D.hatlar[h].renk;
  kontrol['<span style="display:inline-block;width:22px;height:4px;background:'+c
    +';border-radius:2px;vertical-align:middle;margin-right:6px"></span>'+D.hatlar[h].ad] = katman[h];
});
kontrol['<span style="display:inline-block;width:11px;height:11px;background:#16222c;border:2px solid #fff;'
  +'box-shadow:0 0 0 1px #999;vertical-align:middle;margin-right:8px"></span>Düğümler (garaj, otogar, marina)'] = dugumKatman;
const DAR = window.matchMedia('(max-width:640px)').matches;
L.control.layers(null, kontrol, {collapsed:DAR, position:'topleft'}).addTo(map);

/* ---------- lejant ---------- */
(function(){
  let h = '';
  ['hat1','hat2','hat3','hat4'].forEach(k => {
    h += '<div class="sat"><span class="cizgi" style="border-color:'+D.hatlar[k].renk+'"></span>'
       + '<span>'+D.hatlar[k].ad.replace(' · ', '<br>')+'</span></div>';
  });
  h += '<div class="sat"><span class="cizgi kesik"></span><span>Yürüyüş ~10-15 dk<br>(Ayayorgi sapağı → koy)</span></div>';
  h += '<div class="ayr"></div>';
  h += '<div class="sat"><span class="mk"><span class="mini-r">1</span></span><span>Beach club (numaralı)</span></div>';
  h += '<div class="sat"><span class="mk"><span class="mini-r" style="background:#1D9E75">1</span></span><span>Alaçatı\'dan tek dolmuş</span></div>';
  h += '<div class="sat"><span class="mk"><span class="mini-k"></span></span><span>Düğüm (garaj / otogar / marina)</span></div>';
  h += '<div class="sat"><span class="mk"><span class="mini-d"></span></span><span>Ara durak</span></div>';
  h += '<div style="margin-top:8px;font-size:10.5px;color:#5b6b78;line-height:1.35">'
     + 'Süre ve ücretler tahminidir. Doğrulanmayan duraklar: '+D.dogrulanmayan.join(', ')+'.</div>';
  document.getElementById('lejantGovde').innerHTML = h;
  const b = document.createElement('button');
  b.type = 'button'; b.textContent = 'Lejantı gizle';
  b.onclick = function(){
    const el = document.getElementById('lejant');
    el.classList.toggle('kapali');
    b.textContent = el.classList.contains('kapali') ? 'Lejantı göster' : 'Lejantı gizle';
  };
  document.getElementById('lejant').appendChild(b);
  if (window.matchMedia('(max-width:640px)').matches) b.click();
})();

/* ---------- filtre ---------- */
const btn = document.getElementById('filtre');
btn.addEventListener('click', function(){
  const acik = btn.getAttribute('aria-pressed') !== 'true';
  btn.setAttribute('aria-pressed', acik ? 'true' : 'false');
  D.plajlar.forEach(b => {
    const m = plajMarker[b.key];
    if (acik && !b.tek) { map.removeLayer(m); }
    else if (!map.hasLayer(m)) { m.addTo(map); }
  });
  if (acik) {
    map.closePopup();
    map.fitBounds(L.latLngBounds(D.plajlar.filter(b=>b.tek).map(b=>[b.lat,b.lng])
      .concat([[D.dugumler[0].lat, D.dugumler[0].lng]])), {padding:PAD});
  } else {
    map.fitBounds(TUM, {padding:PAD});
  }
});

/* ---------- ilk görünüm: 14 noktanın tamamı ---------- */
const PAD = DAR ? [26,26] : [60,60];
const TUM = L.latLngBounds(
  D.plajlar.map(b=>[b.lat,b.lng]).concat(D.dugumler.map(n=>[n.lat,n.lng]))
);
map.fitBounds(TUM, {padding:PAD});
window.addEventListener('resize', () => map.invalidateSize());
</script>
</body>
</html>
"""

html = HTML.replace("__DATA__", json.dumps(DATA, ensure_ascii=False, separators=(',',':')))
open(OUTHTML,"w",encoding="utf-8").write(html)
print("WROTE",OUTHTML,len(html),"bytes")
