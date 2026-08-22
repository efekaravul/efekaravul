/* ====================== mağaza sabitleri ve form kuralları ==================
   Bu uygulama vardiya YAZMAZ; çalışanlardan gelen istekleri toplar ve şefe
   derli toplu gösterir. Planlama mağazanın kendi sisteminde yapılır.      */

/* 3425 IST-Nişantaşı · kasa kadrosu (20.08.2026 export'u).
   Sunucuya bağlanılamadığında ve demo modunda bu liste kullanılır;
   bağlıyken kadro `kadro()` çağrısından gelir.                            */
export const KASA = [
  "Arda Eren Dil", "Ayşe Yılmaz", "Berkant Polat", "Betül Erdoğan", "Burcu Özmen",
  "Dilara Sarı", "Eda Serbes", "Efe Aldemir", "Efe Karavul", "Elif Aksu",
  "Elif Paşaoğlu", "Elif Şahingöz", "Ertuğrul Çiftçi", "Esma Uygun", "Kaan Mutlu",
  "Merve Akçaşarı Tulunay", "Mısra Ezik", "Muhammed Yakupcan Tali",
  "Saliha Ebrar Ergüven", "Sibel Tunç", "Utku Ali Aktaş",
];

export const slug = (s) =>
  s.toLocaleLowerCase("tr").replace(/ğ/g, "g").replace(/ü/g, "u").replace(/ş/g, "s")
   .replace(/ı/g, "i").replace(/ö/g, "o").replace(/ç/g, "c")
   .replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

export const VARSAYILAN_KADRO = KASA.map((ad) => ({ id: slug(ad), ad, rol: "calisan" }));

/* export'lardaki gerçek başlangıç/bitiş saatleri */
export const SAATLER = [
  "07:00","08:00","08:30","09:00","09:30","10:00","10:30","11:00","12:00",
  "13:00","14:00","15:00","16:00","17:00","18:00","18:30","19:00","20:00",
  "21:00","21:30",
];

/* Ağustos export'larındaki kasa vardiyalarından çıkan kalıplar — çalışan
   saat kısıtı yazarken neye göre yazdığını bilsin diye referans.          */
export const KALIPLAR = [
  { grup: "Açılış",  ornek: "07:00–16:00 · 08:00–17:00 · 09:00–18:00", saat: "7–8s" },
  { grup: "Ara",     ornek: "11:00–18:00 · 11:00–19:00 · 12:00–18:00", saat: "5–7s" },
  { grup: "Kapanış", ornek: "16:00–21:30 · 15:00–21:30 · 14:00–21:30", saat: "4,5–6,5s" },
  { grup: "Uzun",    ornek: "12:00–21:30 · 11:00–21:30 · 10:30–21:30", saat: "7,5–9s" },
];

export const TALEP_TIPLERI = [
  { id: "izin",    label: "Tüm gün izin",    kod: "İZİN", katı: true },
  { id: "ders",    label: "Ders var",        kod: "DERS", katı: true },
  { id: "saat",    label: "Saat kısıtı",     kod: "SAAT", katı: true },
  { id: "acilis",  label: "Açılış isterim",  kod: "AÇ",   katı: false },
  { id: "kapanis", label: "Kapanış isterim", kod: "KAP",  katı: false },
];
export const TIP = Object.fromEntries(TALEP_TIPLERI.map((t) => [t.id, t]));
export const tipBilgi = (id) =>
  TIP[id] || { id, label: id || "—", kod: "?", katı: false };

export const MUSAITLIK = [
  { id: "tam",   label: "Tüm gün" },
  { id: "sonra", label: "…'den sonra" },
  { id: "once",  label: "…'e kadar" },
  { id: "yok",   label: "Müsait değil" },
];

export const AYLAR = ["Ocak","Şubat","Mart","Nisan","Mayıs","Haziran","Temmuz",
                      "Ağustos","Eylül","Ekim","Kasım","Aralık"];
export const GUNLER = ["Paz","Pzt","Sal","Çar","Per","Cum","Cmt"];
export const HAFTA = [1, 2, 3, 4, 5, 6, 0]; // Pzt → Paz

export const IZIN_KOTA = 4;               // kişi başı aylık izin hakkı
export const MAX_DOSYA = 4 * 1024 * 1024; // seçilebilecek ham dosya (küçültülür)
