/* ====================== mağaza sabitleri ve iş kuralları ==================== */
/* 3425 IST-Nişantaşı · kasa kadrosu (20.08.2026 export'u).
   Sunucuya bağlanılamadığında ve demo modunda bu liste kullanılır;
   bağlıyken kadro `kadro()` çağrısından gelir.                              */
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

export const MAGAZA = { acilis: "07:00", kapanis: "21:30" };

/* Ağustos export'larındaki kasa vardiyalarından çıkarılan kalıplar. */
export const VARDIYALAR = [
  { id: "A1", grup: "Açılış",  bas: "07:00", bit: "16:00" },
  { id: "A2", grup: "Açılış",  bas: "08:00", bit: "17:00" },
  { id: "A3", grup: "Açılış",  bas: "09:00", bit: "18:00" },
  { id: "O1", grup: "Ara",     bas: "11:00", bit: "18:00" },
  { id: "O2", grup: "Ara",     bas: "11:00", bit: "19:00" },
  { id: "O3", grup: "Ara",     bas: "12:00", bit: "18:00" },
  { id: "K1", grup: "Kapanış", bas: "14:00", bit: "21:30" },
  { id: "K2", grup: "Kapanış", bas: "15:00", bit: "21:30" },
  { id: "K3", grup: "Kapanış", bas: "16:00", bit: "21:30" },
  { id: "U1", grup: "Uzun",    bas: "10:30", bit: "21:30" },
  { id: "U2", grup: "Uzun",    bas: "11:00", bit: "21:30" },
  { id: "U3", grup: "Uzun",    bas: "12:00", bit: "21:30" },
];
export const VARDIYA = Object.fromEntries(VARDIYALAR.map((v) => [v.id, v]));
export const GRUPLAR = ["Açılış", "Ara", "Kapanış", "Uzun"];

export const TALEP_TIPLERI = [
  { id: "izin",    label: "Tüm gün izin",  kod: "İZİN", katı: true },
  { id: "ders",    label: "Ders var",      kod: "DERS", katı: true },
  { id: "saat",    label: "Saat kısıtı",   kod: "SAAT", katı: true },
  { id: "acilis",  label: "Açılış isterim", kod: "AÇ",  katı: false },
  { id: "kapanis", label: "Kapanış isterim", kod: "KAP", katı: false },
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

/* ------------------------------- kurallar --------------------------------- */
export const IZIN_KOTA = 4;          // kişi başı aylık izin hakkı
export const ACILIS_MIN = 2;         // sabah kasayı açacak en az kişi
export const KAPANIS_MIN = 5;        // kapanışa kalacak en az kişi
export const GUNLUK_MIN = 8;         // gün içi toplam kasa personeli
export const HAFTALIK_MAX_SAAT = 45; // haftalık ödenen saat tavanı
export const ARDISIK_MAX_GUN = 6;    // üst üste en fazla çalışılan gün
export const MAX_DOSYA = 4 * 1024 * 1024; // seçilebilecek ham dosya (küçültülür)
