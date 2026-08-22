/* Sunucu ayarları .env dosyasından gelir (bkz. .env.ornek).
   Anahtar tanımlı değilse uygulama "demo" modunda, yalnızca o telefonun
   hafızasında çalışır — kurulumu bitirmeden de açılıp denenebilsin diye. */
const env = import.meta.env || {};

export const SUNUCU = {
  url: (env.VITE_SUPABASE_URL || "").replace(/\/+$/, ""),
  anahtar: env.VITE_SUPABASE_ANON_KEY || "",
};

export const CANLI = Boolean(SUNUCU.url && SUNUCU.anahtar);
export const MAGAZA_ADI = env.VITE_MAGAZA || "3425 IST-Nişantaşı · Kasa";
