import test from "node:test";
import assert from "node:assert/strict";
import { gunDurumu, musaitlik, gunKapali, talepOzet, formDurumu } from "./kurallar.js";

const kayit = (veri, kararlar = {}) => ({ veri, kararlar });

test("izin ve ders günü kapalı sayılır", () => {
  const g = "2026-09-05";
  const izinli = kayit({ gunler: { [g]: { tip: "izin", neden: "düğün" } }, hafta: {} });
  const dersli = kayit({ gunler: { [g]: { tip: "ders" } }, hafta: {} });
  assert.ok(gunKapali(gunDurumu(izinli, g)));
  assert.ok(gunKapali(gunDurumu(dersli, g)));
});

test("reddedilen izin günü tekrar açılır", () => {
  const g = "2026-09-05";
  const k = kayit(
    { gunler: { [g]: { tip: "izin", neden: "düğün" } }, hafta: {} },
    { [g]: { durum: "ret", not: "kadro yetmiyor" } }
  );
  assert.ok(!gunKapali(gunDurumu(k, g)));
});

test("saat kısıtı ve haftalık sınır 'kısıtlı' verir", () => {
  const g = "2026-09-07";                       // Pazartesi
  const saatli = kayit({ gunler: { [g]: { tip: "saat", enErken: "14:00" } }, hafta: {} });
  const haftalik = kayit({ gunler: {}, hafta: { 1: { mod: "once", saat: "18:00" } } });
  assert.equal(musaitlik(gunDurumu(saatli, g)), "kısıtlı");
  assert.equal(musaitlik(gunDurumu(haftalik, g)), "kısıtlı");
});

test("haftalık 'müsait değil' gün talebi olmadan da kapatır", () => {
  const g = "2026-09-07";
  const k = kayit({ gunler: {}, hafta: { 1: { mod: "yok" } } });
  assert.ok(gunKapali(gunDurumu(k, g)));
});

test("açılış/kapanış isteği günü kapatmaz, tercih olarak durur", () => {
  const g = "2026-09-08";
  const k = kayit({ gunler: { [g]: { tip: "kapanis" } }, hafta: {} });
  assert.equal(musaitlik(gunDurumu(k, g)), "tercih");
});

test("talep yoksa gün açık", () => {
  assert.equal(musaitlik(gunDurumu(kayit({ gunler: {}, hafta: {} }), "2026-09-09")), "acik");
});

test("özet metni saat kısıtını okunur yazar", () => {
  assert.equal(talepOzet({ tip: "saat", enErken: "14:00", enGec: "19:00" }),
               "14:00 sonrası · 19:00 öncesi");
  assert.equal(talepOzet({ tip: "izin" }), "Tüm gün izin");
  assert.equal(talepOzet(null), "");
});

test("form kontrolü hafta sonu izninde neden, saat kısıtında saat ister", () => {
  assert.ok(!formDurumu({ gunler: {}, hafta: {} }).dolu);

  const cumartesiNedensiz = formDurumu({
    gunler: { "2026-09-05": { tip: "izin", neden: "" } }, hafta: {},
  });
  assert.ok(!cumartesiNedensiz.gecerli);

  const duzgun = formDurumu({
    gunler: { "2026-09-05": { tip: "izin", neden: "Kardeşimin düğünü" } }, hafta: {},
  });
  assert.ok(duzgun.gecerli && duzgun.dolu && duzgun.izin === 1);

  const saatsiz = formDurumu({ gunler: { "2026-09-07": { tip: "saat" } }, hafta: {} });
  assert.ok(!saatsiz.gecerli);

  const tersSaat = formDurumu({
    gunler: { "2026-09-07": { tip: "saat", enErken: "18:00", enGec: "14:00" } }, hafta: {},
  });
  assert.ok(!tersSaat.gecerli);
});

test("haftalık kısıt tek başına formu dolu sayar", () => {
  const k = formDurumu({ gunler: {}, hafta: { 3: { mod: "yok" } } });
  assert.ok(k.dolu && k.gecerli && k.haftaKisit === 1);
});
