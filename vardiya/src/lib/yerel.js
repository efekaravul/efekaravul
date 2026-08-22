/* ======================= demo (tek cihaz) veri katmanı =====================
   Supabase anahtarı tanımlı değilken devreye girer. api.js ile birebir aynı
   fonksiyonları sunar; veriler yalnızca bu tarayıcıda durur.              */
import { VARSAYILAN_KADRO } from "../data/sabitler.js";
import { iso } from "./tarih.js";

const KEY = "vardiya-demo-v3";
const oku = () => {
  try { return JSON.parse(localStorage.getItem(KEY)) || tohum(); }
  catch { return tohum(); }
};
const yaz = (d) => { try { localStorage.setItem(KEY, JSON.stringify(d)); } catch { /* kota */ } };

function tohum() {
  const bugun = new Date();
  const y = bugun.getFullYear(), m = bugun.getMonth() + 1;
  const ay = `${y}-${String(m + 1).padStart(2, "0")}`;
  const g = (n) => iso(new Date(y, m, n));
  const d = {
    talepler: {
      [`dilara-sari|${ay}`]: {
        veri: {
          gunler: {
            [g(6)]: { tip: "izin", neden: "Kardeşimin düğünü" },
            [g(7)]: { tip: "izin", neden: "Kardeşimin düğünü" },
          }, hafta: {},
        }, gonderim: Date.now() - 86400000,
      },
      [`efe-karavul|${ay}`]: {
        veri: {
          gunler: {
            [g(2)]: { tip: "saat", neden: "Sabah dersim var", enErken: "14:00" },
            [g(4)]: { tip: "ders", neden: "" },
          },
          hafta: { 1: { mod: "sonra", saat: "14:00" }, 3: { mod: "yok" } },
        }, gonderim: Date.now() - 72000000,
      },
      [`kaan-mutlu|${ay}`]: {
        veri: { gunler: { [g(6)]: { tip: "kapanis", neden: "" } }, hafta: {} },
        gonderim: null,
      },
    },
    programlar: {}, icerikler: {}, kararlar: {},
  };
  yaz(d);
  return d;
}

const kim = (token) => String(token || "").replace(/^demo:/, "");
const sefMi = (token) => kim(token) === "kasa-sefi";

export const yerelApi = {
  canli: false,
  async kadro() { return VARSAYILAN_KADRO; },
  async giris(id) {
    const k = VARSAYILAN_KADRO.find((p) => p.id === id);
    if (!k) throw new Error("Kişi bulunamadı.");
    return { token: `demo:${id}`, id, ad: k.ad, rol: "calisan" };
  },
  async sefGiris(kod) {
    if (kod !== "3425") throw new Error("Kod hatalı. Tekrar dene.");
    return { token: "demo:kasa-sefi", id: "kasa-sefi", ad: "Kasa Şefi", rol: "yonetici" };
  },
  async cikis() {},
  async kendiAyim(token, ay) {
    const d = oku(), id = kim(token);
    const kisi = VARSAYILAN_KADRO.find((p) => p.id === id) || { id, ad: id };
    const kararlar = {};
    Object.entries(d.kararlar).forEach(([k, v]) => {
      const [pid, gun] = k.split("|");
      if (pid === id && gun.startsWith(ay)) kararlar[gun] = v;
    });
    return {
      kisi: { id: kisi.id, ad: kisi.ad, rol: "calisan" },
      talep: d.talepler[`${id}|${ay}`] || null,
      program: d.programlar[id] || null,
      kararlar,
    };
  },
  async talepKaydet(token, ay, veri, gonder) {
    const d = oku(), id = kim(token);
    const gonderim = gonder ? Date.now() : null;
    d.talepler[`${id}|${ay}`] = { veri, gonderim };
    yaz(d);
    return { gonderim };
  },
  async programYukle(token, dosya) {
    const d = oku(), id = kim(token);
    const { icerik, ...meta } = dosya;
    d.programlar[id] = { ...meta, tarih: Date.now() };
    d.icerikler[id] = icerik;
    yaz(d);
  },
  async programSil(token) {
    const d = oku(), id = kim(token);
    delete d.programlar[id]; delete d.icerikler[id];
    yaz(d);
  },
  async programAc(token, personelId) {
    const d = oku(), id = personelId || kim(token);
    if (!d.icerikler[id]) return null;
    return { ...d.programlar[id], icerik: d.icerikler[id] };
  },
  async sefAyi(token, ay) {
    if (!sefMi(token)) throw new Error("Yetki yok.");
    const d = oku();
    const talepler = {}, kararlar = {};
    Object.entries(d.talepler).forEach(([k, v]) => {
      const [pid, a] = k.split("|");
      if (a === ay) talepler[pid] = v;
    });
    Object.entries(d.kararlar).forEach(([k, v]) => {
      if (k.split("|")[1].startsWith(ay)) kararlar[k] = v;
    });
    return {
      kadro: VARSAYILAN_KADRO, talepler, programlar: d.programlar, kararlar,
    };
  },
  async kararVer(token, personelId, gun, durum, not) {
    const d = oku();
    if (durum === null) delete d.kararlar[`${personelId}|${gun}`];
    else d.kararlar[`${personelId}|${gun}`] = { durum, not: not || "" };
    yaz(d);
  },
  async sefKoduDegistir() {
    throw new Error("Demo modunda şef kodu değiştirilemez.");
  },
};
