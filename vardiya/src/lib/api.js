/* =========================== sunucu veri katmanı ===========================
   Supabase'in REST/RPC uçlarını doğrudan fetch ile çağırır; ek paket yok.
   Tablolar RLS ile kapalı olduğundan anon anahtarı yalnızca db/01_sema.sql
   içindeki fonksiyonları çalıştırabilir.                                  */
import { SUNUCU, CANLI } from "../config.js";
import { yerelApi } from "./yerel.js";

const MESAJ = {
  "oturum-gecersiz": "Oturumun düştü, tekrar giriş yap.",
  "kod-hatali": "Kod hatalı. Tekrar dene.",
  "kisi-yok": "Kişi bulunamadı.",
  "yetki-yok": "Bu ekran için yönetici girişi gerekiyor.",
  "dosya-buyuk": "Dosya çok büyük.",
  "kod-bicimi": "Kod 4–8 rakam olmalı.",
  "yonetici-yok": "Kadroda yönetici tanımlı değil.",
};

async function rpc(fn, govde = {}) {
  let cevap;
  try {
    cevap = await fetch(`${SUNUCU.url}/rest/v1/rpc/${fn}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        apikey: SUNUCU.anahtar,
        Authorization: `Bearer ${SUNUCU.anahtar}`,
      },
      body: JSON.stringify(govde),
    });
  } catch {
    throw new Error("Bağlantı yok. İnterneti kontrol et.");
  }
  const metin = await cevap.text();
  const veri = metin ? JSON.parse(metin) : null;
  if (!cevap.ok) {
    const isaret = (veri && (veri.message || veri.hint)) || "";
    const bilinen = Object.keys(MESAJ).find((k) => isaret.includes(k));
    const hata = new Error(bilinen ? MESAJ[bilinen] : isaret || "Sunucu hatası.");
    hata.kod = bilinen || null;
    throw hata;
  }
  return veri;
}

export const sunucuApi = {
  canli: true,
  kadro: () => rpc("kadro"),
  giris: (id) => rpc("giris", { p_id: id }),
  sefGiris: (kod) => rpc("sef_giris", { p_kod: kod }),
  cikis: (token) => rpc("cikis", { p_token: token }),
  kendiAyim: (token, ay) => rpc("kendi_ayim", { p_token: token, p_ay: ay }),
  talepKaydet: (token, ay, veri, gonder) =>
    rpc("talep_kaydet", { p_token: token, p_ay: ay, p_veri: veri, p_gonder: !!gonder }),
  programYukle: (token, d) =>
    rpc("program_yukle", {
      p_token: token, p_ad: d.ad, p_tur: d.tur || "",
      p_boyut: d.boyut || 0, p_icerik: d.icerik,
    }),
  programSil: (token) => rpc("program_sil", { p_token: token }),
  programAc: (token, personelId) =>
    rpc("program_ac", { p_token: token, p_personel: personelId || null }),
  sefAyi: (token, ay) => rpc("sef_ayi", { p_token: token, p_ay: ay }),
  kararVer: (token, personelId, gun, durum, not) =>
    rpc("karar_ver", {
      p_token: token, p_personel: personelId, p_gun: gun,
      p_durum: durum, p_not: not || "",
    }),
  planKaydet: (token, atamalar) =>
    rpc("plan_kaydet", { p_token: token, p_atamalar: atamalar }),
  planYayinla: (token, ay, yayinda) =>
    rpc("plan_yayinla", { p_token: token, p_ay: ay, p_yayinda: !!yayinda }),
  sefKoduDegistir: (token, yeni) =>
    rpc("sef_kodu_degistir", { p_token: token, p_yeni: yeni }),
};

export const api = CANLI ? sunucuApi : yerelApi;
export const DEMO = !CANLI;

/* Oturum telefonda saklanır ki uygulama her açılışta isim sormasın. */
const OTURUM_KEY = "vardiya-oturum";
export const oturumOku = () => {
  try { return JSON.parse(localStorage.getItem(OTURUM_KEY)); } catch { return null; }
};
export const oturumYaz = (o) => {
  try {
    if (o) localStorage.setItem(OTURUM_KEY, JSON.stringify(o));
    else localStorage.removeItem(OTURUM_KEY);
  } catch { /* özel sekme */ }
};
