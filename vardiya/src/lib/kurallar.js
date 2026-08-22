/* ============================== iş kuralları ===============================
   Ekranlardan bağımsız, saf fonksiyonlar. Testleri kurallar.test.js içinde.
   ------------------------------------------------------------------------- */
import {
  VARDIYA, VARDIYALAR, ACILIS_MIN, KAPANIS_MIN, GUNLUK_MIN,
  HAFTALIK_MAX_SAAT, ARDISIK_MAX_GUN, tipBilgi,
} from "../data/sabitler.js";
import { dk, iso, tarihten, haftaKey } from "./tarih.js";

/* --------------------------------- mola ----------------------------------
   Ödenen saat = mağazada geçen süre − mola. 5,5 saate kadar 30 dk,
   9 saate kadar 1 saat tek mola; 9 saati aşan planlarda iki mola.        */
export function molaDk(brut) {
  if (brut <= 330) return 30;
  if (brut <= 540) return 60;
  return 90;
}

export function vardiyaSure(vardiyaId) {
  const v = VARDIYA[vardiyaId];
  if (!v) return { brut: 0, mola: 0, odenen: 0 };
  const brut = dk(v.bit) - dk(v.bas);
  const mola = molaDk(brut);
  return { brut, mola, odenen: brut - mola };
}

export const acilisMi = (vardiyaId) => {
  const v = VARDIYA[vardiyaId];
  return !!v && dk(v.bas) <= dk("08:00");
};
export const kapanisMi = (vardiyaId) => {
  const v = VARDIYA[vardiyaId];
  return !!v && dk(v.bit) >= dk("21:00");
};

/* ------------------------- kişinin o gündeki durumu ----------------------- */
export function gunDurumu(kayit, gunKey) {
  const veri = (kayit && kayit.veri) || {};
  const wd = tarihten(gunKey).getDay();
  const hafta = (veri.hafta && (veri.hafta[wd] ?? veri.hafta[String(wd)])) || {};
  return {
    talep: (veri.gunler && veri.gunler[gunKey]) || null,
    hafta,
    karar: (kayit && kayit.kararlar && kayit.kararlar[gunKey]) || null,
  };
}

/** Bir vardiyanın kişinin taleplerine göre çakışmaları.
 *  seviye: "katı" → yazılmamalı, "yumuşak" → yazılabilir ama tercihe ters. */
export function cakismalar(durum, vardiyaId) {
  const v = VARDIYA[vardiyaId];
  if (!v) return [];
  const { talep, hafta, karar } = durum;
  const out = [];
  const kati = (metin) => out.push({ seviye: "katı", metin });
  const yumusak = (metin) => out.push({ seviye: "yumuşak", metin });

  if (talep) {
    if (talep.tip === "izin") {
      if (karar && karar.durum === "ret") yumusak("izin talebi reddedildi");
      else kati("tüm gün izin talebi");
    }
    if (talep.tip === "ders") kati("ders var");
    if (talep.tip === "saat") {
      if (talep.enErken && dk(talep.enErken) > dk(v.bas))
        kati(`en erken ${talep.enErken} başlayabilir`);
      if (talep.enGec && dk(talep.enGec) < dk(v.bit))
        kati(`en geç ${talep.enGec} çıkabilir`);
    }
    if (talep.tip === "acilis" && v.grup !== "Açılış") yumusak("açılış istemişti");
    if (talep.tip === "kapanis" && v.grup !== "Kapanış" && v.grup !== "Uzun")
      yumusak("kapanış istemişti");
  }

  if (hafta.mod === "yok") kati("haftalık müsaitlik: kapalı");
  if (hafta.mod === "sonra" && hafta.saat && dk(hafta.saat) > dk(v.bas))
    kati(`haftalık: ${hafta.saat} sonrası`);
  if (hafta.mod === "once" && hafta.saat && dk(hafta.saat) < dk(v.bit))
    kati(`haftalık: ${hafta.saat} öncesi`);

  return out;
}

export const katiCakisma = (durum, vardiyaId) =>
  cakismalar(durum, vardiyaId).some((c) => c.seviye === "katı");

/** Kişi o gün hiçbir vardiyaya yazılamıyorsa true (izin/ders/kapalı gün). */
export const gunKapali = (durum) =>
  VARDIYALAR.every((v) => katiCakisma(durum, v.id));

/* ------------------------------- kapsama ---------------------------------- */
export function gunKapsama(plan, gunKey) {
  let kisi = 0, acilis = 0, kapanis = 0, odenen = 0;
  for (const [anahtar, vid] of Object.entries(plan)) {
    if (!vid || anahtar.split("|")[0] !== gunKey) continue;
    kisi += 1;
    if (acilisMi(vid)) acilis += 1;
    if (kapanisMi(vid)) kapanis += 1;
    odenen += vardiyaSure(vid).odenen;
  }
  return {
    kisi, acilis, kapanis, odenen,
    eksikAcilis: Math.max(0, ACILIS_MIN - acilis),
    eksikKapanis: Math.max(0, KAPANIS_MIN - kapanis),
    eksikKisi: Math.max(0, GUNLUK_MIN - kisi),
    get sorunlu() {
      return this.eksikAcilis + this.eksikKapanis + this.eksikKisi > 0;
    },
  };
}

/** Bir kişinin ay boyunca toplamı: gün sayısı, ödenen dakika, hafta dağılımı. */
export function kisiToplam(plan, personelId, days) {
  const haftalar = {};
  let gun = 0, odenen = 0, ardisik = 0, enUzunArdisik = 0;
  for (const d of days) {
    const vid = plan[`${iso(d)}|${personelId}`];
    if (vid) {
      const s = vardiyaSure(vid).odenen;
      gun += 1; odenen += s; ardisik += 1;
      enUzunArdisik = Math.max(enUzunArdisik, ardisik);
      const hk = haftaKey(d);
      haftalar[hk] = (haftalar[hk] || 0) + s;
    } else ardisik = 0;
  }
  return { gun, odenen, haftalar, enUzunArdisik };
}

/** Plandaki tüm ihlaller — şefin "kontrol" listesi. */
export function planUyarilari(days, kadro, kayitlar, plan) {
  const out = [];
  for (const d of days) {
    const gunKey = iso(d);
    const k = gunKapsama(plan, gunKey);
    if (k.eksikKapanis) out.push({ gunKey, seviye: "katı", metin: `${k.eksikKapanis} kişi eksik kapanış` });
    if (k.eksikAcilis) out.push({ gunKey, seviye: "katı", metin: `${k.eksikAcilis} kişi eksik açılış` });
    if (k.eksikKisi) out.push({ gunKey, seviye: "yumuşak", metin: `gün içi ${k.eksikKisi} kişi eksik` });
    for (const p of kadro) {
      const vid = plan[`${gunKey}|${p.id}`];
      if (!vid) continue;
      for (const c of cakismalar(gunDurumu(kayitlar[p.id], gunKey), vid)) {
        out.push({ gunKey, seviye: c.seviye, kisi: p.ad, metin: `${p.ad}: ${c.metin}` });
      }
    }
  }
  for (const p of kadro) {
    const t = kisiToplam(plan, p.id, days);
    for (const [hk, m] of Object.entries(t.haftalar)) {
      if (m > HAFTALIK_MAX_SAAT * 60)
        out.push({ seviye: "katı", kisi: p.ad, metin: `${p.ad}: ${hk} haftasında ${Math.round(m / 60)} saat` });
    }
    if (t.enUzunArdisik > ARDISIK_MAX_GUN)
      out.push({ seviye: "katı", kisi: p.ad, metin: `${p.ad}: ${t.enUzunArdisik} gün üst üste` });
  }
  return out;
}

/* ---------------------------- otomatik doldurma ---------------------------
   Elle yazılmış vardiyalara dokunmaz; yalnızca boş kalan yerleri, en az
   saat alan kişiden başlayarak ve talepleri gözeterek doldurur.           */
export function otomatikDoldur({ days, kadro, kayitlar, plan }) {
  const yeni = { ...plan };
  const toplam = Object.fromEntries(
    kadro.map((p) => [p.id, kisiToplam(yeni, p.id, days).odenen])
  );

  const ardisikSayisi = (pid, d) => {
    let n = 0;
    for (let i = 1; i <= ARDISIK_MAX_GUN + 1; i++) {
      const onceki = new Date(d.getFullYear(), d.getMonth(), d.getDate() - i);
      if (yeni[`${iso(onceki)}|${pid}`]) n += 1; else break;
    }
    return n;
  };

  const haftaYuku = (pid, d) => {
    const hk = haftaKey(d);
    return days.reduce((acc, g) => {
      if (haftaKey(g) !== hk) return acc;
      const vid = yeni[`${iso(g)}|${pid}`];
      return acc + (vid ? vardiyaSure(vid).odenen : 0);
    }, 0);
  };

  for (const d of days) {
    const gunKey = iso(d);
    const yazili = new Set(
      kadro.filter((p) => yeni[`${gunKey}|${p.id}`]).map((p) => p.id)
    );

    const ihtiyac = [];
    const k = gunKapsama(yeni, gunKey);
    for (let i = 0; i < k.eksikKapanis; i++) ihtiyac.push("Kapanış");
    for (let i = 0; i < k.eksikAcilis; i++) ihtiyac.push("Açılış");
    const kalan = GUNLUK_MIN - k.kisi - ihtiyac.length;
    for (let i = 0; i < kalan; i++) ihtiyac.push("Ara");

    for (const grup of ihtiyac) {
      let enIyi = null;
      for (const p of kadro) {
        if (yazili.has(p.id)) continue;
        const durum = gunDurumu(kayitlar[p.id], gunKey);
        const secenek = VARDIYALAR.filter(
          (v) => v.grup === grup && !katiCakisma(durum, v.id)
        );
        if (!secenek.length) continue;
        if (ardisikSayisi(p.id, d) >= ARDISIK_MAX_GUN) continue;

        const v = secenek.reduce((a, b) =>
          cakismalar(durum, a.id).length <= cakismalar(durum, b.id).length ? a : b
        );
        if (haftaYuku(p.id, d) + vardiyaSure(v.id).odenen > HAFTALIK_MAX_SAAT * 60) continue;

        const yumusak = cakismalar(durum, v.id).length;
        const tercihli =
          durum.talep &&
          ((durum.talep.tip === "acilis" && grup === "Açılış") ||
           (durum.talep.tip === "kapanis" && (grup === "Kapanış" || grup === "Uzun")));
        const puan = toplam[p.id] + yumusak * 120 - (tercihli ? 240 : 0);
        if (!enIyi || puan < enIyi.puan) enIyi = { pid: p.id, vid: v.id, puan };
      }
      if (!enIyi) continue;
      yeni[`${gunKey}|${enIyi.pid}`] = enIyi.vid;
      yazili.add(enIyi.pid);
      toplam[enIyi.pid] += vardiyaSure(enIyi.vid).odenen;
    }
  }
  return yeni;
}

/* -------------------------- çalışan formu kontrolü ------------------------ */
export function formDurumu(veri) {
  const gunler = (veri && veri.gunler) || {};
  const hafta = (veri && veri.hafta) || {};
  const eksikler = [];

  const izin = Object.values(gunler).filter((v) => v.tip === "izin").length;
  const ders = Object.values(gunler).filter((v) => v.tip === "ders").length;
  const haftaKisit = Object.values(hafta).filter((v) => v.mod && v.mod !== "tam").length;

  const nedenEksik = Object.entries(gunler).filter(([gunKey, v]) => {
    const wd = tarihten(gunKey).getDay();
    return v.tip === "izin" && (wd === 0 || wd === 6) && !(v.neden || "").trim();
  });
  const saatEksik = Object.values(gunler).some(
    (v) => v.tip === "saat" && !v.enErken && !v.enGec
  );
  const saatTers = Object.values(gunler).some(
    (v) => v.tip === "saat" && v.enErken && v.enGec && dk(v.enErken) >= dk(v.enGec)
  );

  if (nedenEksik.length) eksikler.push(`Hafta sonu izinlerine neden yazmalısın (${nedenEksik.length} gün).`);
  if (saatEksik) eksikler.push("Saat kısıtı seçtiğin günlerde en az bir saat gir.");
  if (saatTers) eksikler.push("Bir günde en erken başlangıç, en geç çıkıştan sonra olamaz.");

  return {
    izin, ders, haftaKisit, eksikler,
    dolu: Object.keys(gunler).length + haftaKisit > 0,
    gecerli: eksikler.length === 0,
  };
}

export const talepOzet = (talep) => {
  if (!talep) return "";
  const t = tipBilgi(talep.tip);
  if (talep.tip !== "saat") return t.label;
  const p = [];
  if (talep.enErken) p.push(`${talep.enErken} sonrası`);
  if (talep.enGec) p.push(`${talep.enGec} öncesi`);
  return p.join(" · ") || t.label;
};
