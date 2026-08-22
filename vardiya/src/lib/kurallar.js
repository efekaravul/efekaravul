/* ============================== form kuralları =============================
   Ekranlardan bağımsız, saf fonksiyonlar. Testleri kurallar.test.js içinde.
   Burada vardiya yazma mantığı yoktur; yalnızca talebin geçerli olup
   olmadığı ve şefin gördüğü özet vardır.                                  */
import { tipBilgi } from "../data/sabitler.js";
import { dk, tarihten } from "./tarih.js";

/* ------------------------ kişinin o gündeki durumu ------------------------ */
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

/** O gün için müsaitlik: "kapalı" (hiç çalışamaz), "kısıtlı" (saat sınırı
 *  var), "tercih" (çalışır ama bir isteği var) veya "acik". */
export function musaitlik(durum) {
  const { talep, hafta, karar } = durum;
  const izinGecerli = talep && talep.tip === "izin" && !(karar && karar.durum === "ret");
  if (izinGecerli || (talep && talep.tip === "ders") || hafta.mod === "yok") return "kapalı";
  if ((talep && talep.tip === "saat") || hafta.mod === "sonra" || hafta.mod === "once")
    return "kısıtlı";
  if (talep) return "tercih";
  return "acik";
}

export const gunKapali = (durum) => musaitlik(durum) === "kapalı";

/** Şefin listede gördüğü tek satırlık özet. */
export const talepOzet = (talep) => {
  if (!talep) return "";
  const t = tipBilgi(talep.tip);
  if (talep.tip !== "saat") return t.label;
  const p = [];
  if (talep.enErken) p.push(`${talep.enErken} sonrası`);
  if (talep.enGec) p.push(`${talep.enGec} öncesi`);
  return p.join(" · ") || t.label;
};

/* --------------------------- çalışan formu kontrolü ----------------------- */
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
