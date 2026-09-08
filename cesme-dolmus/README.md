# Çeşme Beach Club & Dolmuş Haritası

10–13 Eylül'de Alaçatı'da araçsız kalan biri için: 10 beach club, bunlara ulaşan
4 dolmuş hattı ve Ayayorgi koyuna inen yürüyüş bacağı.

| Dosya | Ne |
|---|---|
| [`map.html`](map.html) | Leaflet 1.9.4 + OSM tile. Build step yok, çift tıklayınca açılır. |
| [`overview.svg`](overview.svg) | 1600×900 stilize kuşbakışı şematik harita. |
| `scripts/` | Veriyi çeken ve iki çıktıyı üreten pipeline. |
| `data/` | Pipeline'ın ürettiği ham + işlenmiş veri (çıktılar buradan yeniden üretilebilir). |

> Kökteki `README.md` bu deponun GitHub profil sayfası olduğu için üzerine yazılmadı;
> bu iş tamamen `cesme-dolmus/` altında duruyor.

---

## 1. Veri nereden geldi

### 1.1 Beach ve düğüm koordinatları — **verilen, değiştirilmedi**

10 beach club ve 4 düğümün koordinatı görev tanımında Google Places'ten doğrulanmış
olarak verildi. Hiçbiri değiştirilmedi, yuvarlanmadı, yeniden geocode edilmedi.
`scripts/verify.py` bu 14 koordinatı `map.html` içindeki gömülü veriyle tam eşitlik
(`< 1e-9`) olarak karşılaştırır ve hepsi geçer.

Bağımsız bir çapraz kontrol olarak Çeşme Otogar'ı Nominatim'de arattım:
`38.3155933, 26.3048401` döndü — verilen `38.315831, 26.304653` değerinden **~30 m**
uzakta. Yani verilen koordinat seti OSM ile tutarlı.

### 1.2 Ara durak koordinatları — Nominatim ile geocode edildi

`scripts/geocode.py`. Her durak için birden çok sorgu varyantı denendi, sonuçlar
Çeşme yarımadası viewbox'ına (`26.15,38.45 → 26.50,38.15`, `bounded=1`) kısıtlandı
ve her aday, durağın beklenen bölgesine olan mesafeye göre elendi (`anchor_dist_km`
sütunu). Ham çıktı: `data/geocode.json`.

| Durak | Sonuç | Kaynak | Beklenen konuma uzaklık |
|---|---|---|---|
| Çeşme Merkez (Cumhuriyet Meydanı) | 38.324390, 26.302993 | Nominatim (`place=square`) | 0.28 km |
| Ilıca Merkez | 38.308383, 26.360746 | Nominatim (mahalle sınırı) | 0.00 km |
| Devlet Hastanesi | 38.316770, 26.325581 | Nominatim (`amenity=hospital`) | 2.26 km |
| Altınyunus | 38.316302, 26.342478 | Nominatim (mahalle sınırı) | 0.26 km |
| Alaçatı Merkez | 38.284757, 26.374518 | Nominatim (mahalle sınırı) | 0.01 km |
| Migros Dalyan | 38.325697, 26.306759 | **Overpass** (Nominatim boş döndü) | 1.60 km |
| Dalyan Mahallesi | 38.355845, 26.310384 | Nominatim (mahalle sınırı) | 0.39 km |
| Çeşme Limanı | 38.321555, 26.301146 | Nominatim (`leisure=marina`) | 0.29 km |
| Çiftlik Merkez | 38.293880, 26.279401 | Nominatim (mahalle sınırı) | 1.75 km |
| Pırlanta Plajı | 38.285140, 26.249189 | Nominatim (`natural=beach`, way 233554844) | 1.77 km |
| Altınkum Plajı | 38.270241, 26.260099 | Nominatim (`natural=beach`, way 233276444) | 1.64 km |
| Ayayorgi (bölge referansı) | 38.330771, 26.313872 | Nominatim | 0.84 km |

### 1.3 ❌ Geocode **edilemeyen** duraklar — DOĞRULANMADI

Bu dört durak OSM'de yok. Nominatim'de (birden çok sorgu varyantıyla, hem viewbox'lı
hem viewbox'sız) ve Overpass'ta (isim regex'i, geniş ve dar bbox) arandı, hiçbir
eşleşme çıkmadı. **Haritada koordinatı olan nokta olarak gösterilmiyorlar** — uydurma
koordinat konmadı.

| Durak | Hat | Ne bulundu |
|---|---|---|
| **Alaçatı Çamlık** | Hat 1 | Alaçatı çevresinde `Çamlık` adlı hiçbir OSM nesnesi yok. |
| **Bedir Plajı** | Hat 1 | Yarımada genelinde `Bedir` regex'i sadece "Bedirhan Otel"i (38.28615, 26.37956) buluyor — bu bir plaj değil, eşleştirmedim. |
| **Atadağ Sitesi** | Hat 3 | Dalyan çevresinde `Atadağ` adlı OSM nesnesi yok. |
| **Fener Koyu** | Hat 4 | Çeşme güneybatısında `Fener` adlı OSM nesnesi yok. |

İkisi hat ortasında kaldığı için (Atadağ, Fener) polyline zaten oradan geçiyor;
sadece durak işareti çizilmiyor. **Alaçatı Çamlık** da Ilıca–Alaçatı arasında kaldığı
için güzergâhı etkilemiyor. **Bedir Plajı** ise Hat 1'in son durağı — bunun etkisi
aşağıda "Varsayımlar" başlığında.

### 1.4 Rota geometrisi — OSRM

`scripts/routes.py`. `https://router.project-osrm.org/route/v1/driving/...`
(`overview=full`, `geometries=geojson`). Sonuç GeoJSON olarak `map.html` içine gömüldü.
**Çalışma anında tile dışında hiçbir ağ isteği yok** — headless Chromium ile doğrulandı
(bkz. §3).

Waypoint'ler yalnızca §1.1'deki verilen koordinatlar ile §1.2'deki doğrulanmış geocode
sonuçlarından oluşuyor. OSRM her waypoint'i en yakın yola snap'liyor; snap mesafeleri:

| Hat | Snap mesafeleri (m) | Toplam |
|---|---|---|
| Hat 1 | 0, 21, 79, 0, 0, 0, 22, 87, 84, 167 | 21.6 km |
| Hat 2 | 22, 13 | 3.7 km |
| Hat 3 | 0, 21, 1, 2, 48 | 7.3 km |
| Hat 4 | 0, 21, 139, 2, 66, 5, 50 | 18.7 km |

En büyük snap Kali Beach Club'da (167 m) — kıyıdaki kulüp, asfalt orada bitiyor.

### 1.5 Kıyı çizgisi — OSM `natural=coastline`

`scripts/coast.py`. Overpass'tan (`overpass.kumi.systems` aynası; `overpass-api.de`
bu oturumda tünel resetliyordu) `way["natural"="coastline"](38.10,26.10,38.50,26.60)`
→ 143 way, ham hâli `data/coastline_raw.json.gz`.

İşlem zinciri: uç düğümlerden zincirleme birleştirme (yalnızca *gerçek baş* olan
way'lerden başlanarak) → 55 zincir → görüntü penceresine Liang-Barsky ile kırpma →
açık parçaların pencere kenarı boyunca **saat yönünün tersine** (kara solda kalacak
şekilde) kapatılması → **Douglas-Peucker** sadeleştirme.

Çıktılar: `data/coast_simpl.json` (ε ≈ 22 m, doğrulama için) ve
`data/coast_svg.json` (ε ≈ 16 m, `overview.svg` için). Elle hiçbir kıyı şekli
çizilmedi, uydurulmadı.

### 1.6 Sefer saatleri ve ücretler — görev tanımından

Tarife ve sefer bilgisi tamamen görev tanımında verilen resmî güzergâh bilgisinden
alındı. **Hiçbir saat veya ücret uydurulmadı.** Verilmeyenler §2'de "doğrulanmadı"
olarak işaretli ve popup'ta rakam olarak gösterilmiyor.

---

## 2. Ne doğrulandı, ne varsayım

### 2.1 Doğrulanmış (kod tarafından, `scripts/verify.py`)

```
10 plaj + 4 düğüm koordinatı verilen değerlerle birebir aynı ......... GEÇTİ
Rota köşe noktası 1723 / kıyı poligonu dışında 0 ..................... GEÇTİ
   → hiçbir hat denizin üstünden geçmiyor; OSRM waypoint düzeltmesi gerekmedi
overview.svg'de çakışan etiket .................................... 0 (ÇAKIŞMA: yok)
map.html console hatası (tile hariç) ................................. 0
map.html runtime ağ isteği (tile + CDN hariç) ........................ 0
```

Kıyı poligonunun kendisi de sağlaması yapıldı: Alaçatı, Çeşme, Ilıca, Çiftlik ve
Dalyan merkezleri poligonun içinde; açık deniz test noktaları dışında çıkıyor.
10 beach club'ın kıyıya uzaklığı 3.7 m – 141 m arasında — sahil kulüpleri için
beklenen değer.

### 2.2 Varsayımlar — açıkça işaretli

**a) Hat 1 durak sırası coğrafi olarak yeniden dizildi.**
Resmî liste `... Ilıca Merkez > Devlet Hastanesi > Altınyunus > Alaçatı Çamlık ...`
diyor, ama koordinatlar bu sırayla batıdan doğuya *gitmiyor* (Ilıca 26.361, hastane
26.326, Altınyunus 26.342). Verilen sırayla route çekilirse polyline iki kez ileri
geri gidiyor. Polyline geometrisi için koridor sırası kullanıldı:
Otogar → Çeşme Merkez → Devlet Hastanesi → Altınyunus → Ilıca → Alaçatı Merkez → Garaj → Çark.
**Durak isimleri ve sayısı resmî listedeki gibi bırakıldı**, sadece çizim sırası değişti.

**b) Hat 1, Bedir yerine Kali'de bitiyor.**
Bedir Plajı geocode edilemediği için (§1.3) polyline'ı orada bitiremedim. Bunun yerine
Çark'tan sonra hat, kendisinin hizmet ettiği iki verilen koordinata — Mon Cheri ve
Kali'ye — kadar sürdürüldü. Bu ikisi Çark ile Bedir arasında, aynı güney kıyı yolunda.
Yani çizilen geometri gerçek yol, ama hattın **Kali'den Bedir'e kadarki son parçası
haritada yok**.

**c) Hat 4 sonu, durak noktalarının ötesine uzatıldı.**
OSM'in "Pırlanta Plajı" ve "Altınkum Plajı" way'lerinin merkezleri, verilen beach
club koordinatlarından 1.6–1.8 km uzakta (ikisi de uzun kumsal; kulüpler uçlarında).
Polyline'ın plaj marker'larına ulaşması için Hat 4 rotası Pırlanta durağından sonra
Fly-Inn'e ve oradan Epi Beach House'a (Altınkum) kadar uzatıldı. Ara duraklar hâlâ
geocode edilmiş resmî konumlarında işaretli.

**d) Süre tahmini modeli.** Popup'ta gösterilen süre üç parçadan oluşuyor ve
parçalar ayrı ayrı yazılıyor:

- **araç içi** = OSRM serbest akış süresi **× 1.35** (dolmuş duraklamaları + yaz trafiği payı).
  1.35 çarpanı bir varsayımdır, ölçülmüş değil.
- **yürüyüş** = OSRM mesafesi ÷ **1.25 m/s**. Ayayorgi sapağından: Sole & Mare 690 m ≈ 9 dk,
  Aura 654 m ≈ 9 dk, Mano del Sol 868 m ≈ 12 dk. Görev tanımındaki "~10-15 dk" ile uyumlu.
- **bekleme** = sefer sıklığının yarısı. Hat 1 (7–10 dk) → 4 dk; Hat 3 (30 dk) → 15 dk.
  **Hat 4 için sefer sıklığı verilmedi**, o yüzden Hat 4 aktarması olan plajlarda
  bekleme rakam olarak gösterilmiyor; popup "aktarma beklemesi: sefer sıklığı
  doğrulanmadı" diyor.

**e) Ayayorgi sapağı koordinatı hesaplandı, geocode edilmedi.**
`38.334391, 26.306836`. Çeşme Otogar → Dalyan ve Çeşme Otogar → Sole & Mare
rotalarının OSRM geometrileri karşılaştırılıp ayrıştıkları ilk nokta alındı. Yani
sapak, "iki güzergâhın gerçekten ayrıldığı yer" olarak veriden türetildi.

**f) OSRM public demo'da yaya profili yok.** `/route/v1/foot/...` uç noktası cevap
veriyor ama demo sunucu tüm profil adlarında **araç** grafiğini servis ediyor
(ölçüm: 2351 m / 245.8 s ≈ 9.6 m/s). Yürüyüş bacağının *geometrisi* bu yüzden
Ayayorgi bağlantı yolunun araç geometrisi — koya inen yol zaten tek yol olduğu için
izlenen çizgi doğru. *Süre* ise OSRM'den değil, yukarıdaki 1.25 m/s'den hesaplandı.

**g) "Dalyan Mahallesi" durağı mahalle sınırının merkezi.** Gerçek dolmuş son durağı
muhtemelen liman kenarında; Stage on the Beach'e olan ~540 m fark buradan geliyor.

**h) Altınkum, Pırlanta'dan sonra geliyor.** Coğrafi olarak Altınkum Çeşme'ye daha
yakın, ama resmî durak sırası `... Pırlanta Plajı > Altınkum Plajı`. Epi Beach House
için hesaplanan süre bu resmî sıraya uyar, dolayısıyla Fly-Inn'den uzun çıkıyor.

### 2.3 Ücretlerde ne gösteriliyor, ne gösterilmiyor

| Plaj | Popup'ta ücret | Neden |
|---|---|---|
| Elias | **85 TL** | Alaçatı → Çark, verildi |
| Mon Cheri, Kali | *doğrulanmadı* | Çark ile Bedir arasında bir ara durak; ara durak tarifesi verilmedi. Popup notunda hattın doğrulanmış uç ücretleri (Çark 85 TL / Bedir 105 TL) referans olarak yazıyor, toplam rakam verilmiyor. |
| Sole & Mare, Aura, Mano del Sol | *doğrulanmadı* | Alaçatı → Çeşme 85 TL biliniyor; Çeşme → **Ayayorgi sapağı** ara durak ücreti verilmedi (Çeşme–Dalyan tam bilet 75 TL). Toplam uydurulmadı. |
| Stage on the Beach | **160 TL** | 85 (Alaçatı→Çeşme) + 75 (Çeşme→Dalyan) |
| Epi Beach House | **170 TL** | 85 + 85 (Çeşme→Altınkum) |
| Fly-Inn, Playa Tropical | **170 TL** | 85 + 85 (Çeşme→Pırlanta) |

Hat 2 (Port Alaçatı shuttle) için ücret verilmedi; hiçbir yerde ücret gösterilmiyor.
Hat 4 için sefer saati verilmedi; hiçbir yerde sefer saati gösterilmiyor.

---

## 3. `map.html` — yapılan doğrulama

Headless Chromium (Playwright) ile 1280×860 ve 390×780'de açıldı:

- DOM: 10 yuvarlak plaj rozeti, 4 kare düğüm, 14 ara durak, 17 polyline path.
- Console: tile isteği dışında **hata yok**. (Bu konteynerde tarayıcının internet
  erişimi olmadığı için tile'lar `ERR_CONNECTION_RESET` veriyor; gerçek makinede yüklenir.
  Leaflet CDN'i de bu yüzden test sırasında yerel kopyayla değiştirildi — sürüm ve
  SHA-256 birebir aynı dosya.)
- Ağ: sayfa + Leaflet dışında **hiçbir istek yok**. Rota verisi tamamen gömülü.
- Popup, filtre butonu ("tek dolmuş" → sadece 1/2/3 kalıyor) ve fitBounds çalışıyor.

Yakın nokta çözümü: marker cluster **kullanılmadı**. Ayayorgi üçlüsü ve
Fly-Inn/Playa Tropical için rozet piksel olarak kaydırıldı, gerçek konumda küçük bir
çekirdek nokta bırakıldı ve ikisi bir **leader line** ile bağlandı. Kaydırma
`divIcon`'un içindeki SVG ile yapıldığı için her zoom seviyesinde aynı ekran
mesafesinde kalıyor.

## 4. `overview.svg` — yapılan doğrulama

- Kıyı geometrisi §1.5'teki OSM verisinden; elle şekil çizilmedi.
- Etiket yerleşimi greedy bir algoritma: her etiket için 8 yön × 6 yarıçap denenir,
  daha önce yerleşmiş kutularla / pinlerle / panellerle çakışan ve **rota çizgisinin
  üstüne düşen** adaylar elenir; hiçbiri olmazsa rota kaçınması gevşetilir.
  Öncelik sırası: plaj etiketleri → düğüm etiketleri → bölge etiketleri.
- Bitişte tüm kutular çift döngüyle karşılaştırılıyor; çıktı **`ÇAKIŞMA: yok`**.
- Bölge etiketleri: Alaçatı, Port Alaçatı, Ayayorgi Koyu, Dalyan, Altınkum–Pırlanta,
  Çeşme, Ilıca.

---

## 5. Yeniden üretmek

```bash
cd cesme-dolmus/scripts
python3 geocode.py                       # Nominatim  -> ../data/geocode.json
python3 routes.py                        # OSRM       -> ../data/routes.json
COAST_W="26.215,38.205,26.425,38.375" COAST_EPS=0.00025 COAST_OUT=coast_simpl.json python3 coast.py
COAST_W="26.155,38.2206,26.485,38.3663" COAST_EPS=0.00018 COAST_OUT=coast_svg.json  python3 coast.py
python3 gen_map.py ../map.html
python3 gen_svg.py ../overview.svg
cd ../.. && python3 cesme-dolmus/scripts/verify.py
```

`coast.py` Overpass'tan ham kıyıyı `../data/coastline.json` olarak bekler; sıkıştırılmış
kopya `data/coastline_raw.json.gz` içinde (`gunzip -c` ile açın).

## 6. Kaynaklar ve lisans

- Kıyı çizgisi ve durak konumları: © OpenStreetMap katkıcıları, **ODbL**.
  Nominatim ve Overpass API üzerinden alındı.
- Güzergâh geometrisi: [OSRM](https://project-osrm.org/) public demo sunucusu
  (OSM verisi üzerinde), **ODbL**.
- Tile: OpenStreetMap Standard.
- Beach club ve düğüm koordinatları: görev tanımıyla verildi (Google Places kaynaklı).
- Sefer saatleri ve ücretler: görev tanımıyla verilen resmî güzergâh bilgisi.
  **Yolculuktan önce güncel tarifeyi teyit edin.**
