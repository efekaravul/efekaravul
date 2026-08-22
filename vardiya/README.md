# Vardiya · 3425 IST-Nişantaşı · Kasa

Kasa ekibinin bir sonraki ay için **vardiya isteklerini toplayan** telefon
uygulaması. Planı yazmaz — istekleri toplar, eksikleri kontrol eder ve şefe
derli toplu gösterir. App Store / Play Store yok: **tek bir link**, telefonda
"Ana Ekrana Ekle" ile ikon gibi durur.

```
çalışan                              şef
──────────────────────────────       ──────────────────────────────
gün gün istek (izin/ders/saat)  ──▶  günlere göre talep listesi
haftalık müsaitlik              ──▶  müsaitlik ızgarası + ay matrisi
ders programı fotoğrafı         ──▶  yalnızca şefe açık
                                ──▶  kim gönderdi / kim göndermedi
izin kararını görür             ◀──  izin talebine onay / ret
```

## Herkes telefonundan nasıl girecek?

1. Uygulama bir kez yayınlanır, sabit bir adresi olur
   (ör. `https://efekaravul.github.io/`).
2. Linki WhatsApp kasa grubuna at; mola odasına da QR afişi as:
   `pip install segno && python3 scripts/qr.py <adres> > afis.svg` → yazdır.
3. Çalışan linke girer → **listeden ismine dokunur** (kişisel şifre yok).
   Oturum telefonda kalır, bir daha isim sormaz.
4. iPhone'da Paylaş ⬆ → **Ana Ekrana Ekle**, Android'de menü → **Uygulamayı
   yükle**. Artık tam ekran açılır, adres çubuğu görünmez.
5. Şef aynı linkten **Yönetici** sekmesine geçip mağaza kodunu girer.
   İzin nedenleri ve ders programları yalnızca o girişte görünür.

Uygulama kabuğu servis çalışanıyla önbelleğe alınır: mağazada internet
zayıfken de açılır, kayıt için bağlantı gerekir.

## Ekranlar

**Çalışan** · Günler (gün gün istek + neden) · Haftalık müsaitlik (ders
programına göre sabit) · Ders programı (fotoğraf/PDF). Yazdıkça taslak olarak
kaydedilir; "Şefe gönder" ancak eksik yoksa aktif olur.

**Şef** · Talepler (güne göre sıralı, izin taleplerine onay/ret) · Kim
gönderdi (bekleyenler üstte) · Ay matrisi (kim hangi gün çalışamıyor) ·
Müsaitlik ızgarası · Kalıplar (referans) · Ayarlar (yönetici kodu).

## Kurulum

### 1. Supabase (ortak veritabanı, ücretsiz)

1. [supabase.com](https://supabase.com) → yeni proje.
2. **SQL Editor** → `db/01_sema.sql` içeriğini yapıştır, çalıştır.
3. Aynı yerde `db/02_kadro.sql` → kadroyu ve şef kodunu (`3425`) kurar.
4. **Project Settings → API** → `Project URL` ve `anon public` anahtarını al.
5. İlk yönetici girişinden sonra **Ayarlar → Kodu değiştir** ile şef kodunu yenile.

Tablolar RLS ile tamamen kapalıdır; anon anahtarı yalnızca `db/01_sema.sql`
içindeki fonksiyonları çağırabilir ve her çağrı geçerli bir oturum token'ı
ister. Anahtar tarayıcıya gitse bile kimse doğrudan tablo okuyamaz.

### 2. Yerelde çalıştırma

```bash
cp .env.ornek .env      # Supabase bilgilerini yaz
npm install
npm run dev             # http://localhost:5173
npm test                # form kurallarının testleri
```

`.env` yoksa uygulama **demo modunda** açılır: veriler yalnızca o tarayıcıda
durur, örnek talepler yüklüdür. Kurulumu bitirmeden arayüzü gezmek için yeterli.

### 3. Yayın (GitHub Pages)

`.github/workflows/vardiya-yayin.yml` `main` dalına her `vardiya/**` push'unda
testleri koşar, derler ve Pages'e atar. Bir kereye mahsus:

- Depo → **Settings → Pages → Source: GitHub Actions**
- Depo → **Settings → Secrets and variables → Actions**
  - `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` (secret)
  - `VITE_MAGAZA` (variable, isteğe bağlı)

## Form kuralları (`src/lib/kurallar.js`)

| Kural | Davranış |
|---|---|
| Aylık izin hakkı 4 gün | çalışan uyarılır, şef "kota aşan" sayacında görür |
| Hafta sonu izni | neden yazılmadan gönderilemez |
| Saat kısıtı | en az bir saat seçilmeli; en erken < en geç olmalı |
| Ders / haftalık kısıt | ders programı yüklenmeden gönderilemez |
| İzin reddedilirse | o gün matriste tekrar "çalışabilir" görünür |

Kalıplar sekmesindeki vardiya saatleri ve mola kuralı Ağustos export'undan
alınmış referans bilgisidir; uygulama bunlarla hesap yapmaz, çalışan saat
kısıtını neye göre yazacağını bilsin diye durur.

## Dosya düzeni

```
db/                 Supabase şeması + kadro tohumu
src/data/           mağaza sabitleri, talep tipleri, kalıplar
src/lib/            tarih, form kuralları (+test), sunucu ve demo veri katmanı
src/ekranlar/       Giriş · Çalışan · Yönetici
src/parcalar/       ortak arayüz parçaları
scripts/ikon.py     ana ekran ikonları
scripts/qr.py       mola odası QR afişi
```
