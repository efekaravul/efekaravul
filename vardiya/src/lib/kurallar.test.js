import test from "node:test";
import assert from "node:assert/strict";
import {
  molaDk, vardiyaSure, cakismalar, katiCakisma, gunKapsama, kisiToplam,
  otomatikDoldur, formDurumu, gunDurumu, acilisMi, kapanisMi,
} from "./kurallar.js";
import { iso, ayGunleri, sure } from "./tarih.js";
import { VARDIYA, KAPANIS_MIN, ACILIS_MIN } from "../data/sabitler.js";

test("mola: 5,5 saate kadar 30 dk, 9 saate kadar 1 saat, üstü iki mola", () => {
  assert.equal(molaDk(330), 30);
  assert.equal(molaDk(331), 60);
  assert.equal(molaDk(540), 60);
  assert.equal(molaDk(541), 90);
});

test("kalıpların ödenen süreleri export'takiyle uyuşuyor", () => {
  assert.equal(vardiyaSure("A1").odenen, 480);   // 07:00–16:00 → 8s
  assert.equal(vardiyaSure("K3").odenen, 300);   // 16:00–21:30 → 5s
  assert.equal(vardiyaSure("U3").odenen, 480);   // 12:00–21:30 → 8s
  assert.equal(sure(vardiyaSure("O1").odenen), "6s"); // 11:00–18:00
});

test("açılış/kapanış sınıflaması", () => {
  assert.ok(acilisMi("A2") && !acilisMi("O1"));
  assert.ok(kapanisMi("K1") && kapanisMi("U1") && !kapanisMi("A3"));
});

const kayit = (veri, kararlar = {}) => ({ veri, kararlar });

test("izin talebi katı çakışma; reddedilen izin yumuşağa iner", () => {
  const g = "2026-09-05";
  const izinli = kayit({ gunler: { [g]: { tip: "izin", neden: "düğün" } }, hafta: {} });
  assert.ok(katiCakisma(gunDurumu(izinli, g), "K2"));

  const reddedilmis = kayit(izinli.veri, { [g]: { durum: "ret", not: "kadro yetmiyor" } });
  const c = cakismalar(gunDurumu(reddedilmis, g), "K2");
  assert.equal(c.length, 1);
  assert.equal(c[0].seviye, "yumuşak");
});

test("saat kısıtı yalnızca sığmayan vardiyaları eler", () => {
  const g = "2026-09-07";
  const k = kayit({ gunler: { [g]: { tip: "saat", enErken: "14:00" } }, hafta: {} });
  assert.ok(katiCakisma(gunDurumu(k, g), "A1"));   // 07:00 başlıyor
  assert.ok(!katiCakisma(gunDurumu(k, g), "K2"));  // 15:00 başlıyor
});

test("haftalık müsaitlik gün talebi olmadan da bağlar", () => {
  const g = "2026-09-07";                           // Pazartesi
  const k = kayit({ gunler: {}, hafta: { 1: { mod: "once", saat: "18:00" } } });
  assert.ok(katiCakisma(gunDurumu(k, g), "K1"));    // 21:30'da biter
  assert.ok(!katiCakisma(gunDurumu(k, g), "O3"));   // 18:00'de biter
});

test("tercihler yumuşak kalır, vardiyayı engellemez", () => {
  const g = "2026-09-08";
  const k = kayit({ gunler: { [g]: { tip: "kapanis" } }, hafta: {} });
  const c = cakismalar(gunDurumu(k, g), "A1");
  assert.equal(c.length, 1);
  assert.equal(c[0].seviye, "yumuşak");
  assert.ok(!katiCakisma(gunDurumu(k, g), "A1"));
});

test("gün kapsaması açılış/kapanış eksiğini sayar", () => {
  const g = "2026-09-10";
  const plan = { [`${g}|a`]: "A1", [`${g}|b`]: "K2", [`${g}|c`]: "K3" };
  const k = gunKapsama(plan, g);
  assert.equal(k.kisi, 3);
  assert.equal(k.acilis, 1);
  assert.equal(k.kapanis, 2);
  assert.equal(k.eksikAcilis, ACILIS_MIN - 1);
  assert.equal(k.eksikKapanis, KAPANIS_MIN - 2);
  assert.ok(k.sorunlu);
});

test("kişi toplamı ardışık gün ve ödenen saati verir", () => {
  const plan = {
    "2026-09-01|x": "A1", "2026-09-02|x": "A1", "2026-09-04|x": "K3",
  };
  const t = kisiToplam(plan, "x", ayGunleri(2026, 8));
  assert.equal(t.gun, 3);
  assert.equal(t.odenen, 480 + 480 + 300);
  assert.equal(t.enUzunArdisik, 2);
});

test("otomatik doldurma: kapanış kotasını tutturur ve izinliye vardiya yazmaz", () => {
  const days = ayGunleri(2026, 8).slice(0, 3);
  const kadro = Array.from({ length: 12 }, (_, i) => ({ id: `k${i}`, ad: `Kişi ${i}` }));
  const g0 = iso(days[0]);
  const kayitlar = {
    k0: kayit({ gunler: { [g0]: { tip: "izin", neden: "" } }, hafta: {} }),
    k1: kayit({ gunler: {}, hafta: { [days[0].getDay()]: { mod: "yok" } } }),
  };
  const plan = otomatikDoldur({ days, kadro, kayitlar, plan: {} });

  const k = gunKapsama(plan, g0);
  assert.ok(k.kapanis >= KAPANIS_MIN, `kapanış ${k.kapanis}`);
  assert.ok(k.acilis >= ACILIS_MIN, `açılış ${k.acilis}`);
  assert.equal(plan[`${g0}|k0`], undefined);
  assert.equal(plan[`${g0}|k1`], undefined);
});

test("otomatik doldurma elle yazılanı korur", () => {
  const days = ayGunleri(2026, 8).slice(0, 1);
  const kadro = Array.from({ length: 12 }, (_, i) => ({ id: `k${i}`, ad: `Kişi ${i}` }));
  const g0 = iso(days[0]);
  const plan = otomatikDoldur({
    days, kadro, kayitlar: {}, plan: { [`${g0}|k5`]: "A1" },
  });
  assert.equal(plan[`${g0}|k5`], "A1");
});

test("otomatik doldurma haftalık saat tavanını aşmaz", () => {
  const days = ayGunleri(2026, 8);
  const kadro = Array.from({ length: 14 }, (_, i) => ({ id: `k${i}`, ad: `Kişi ${i}` }));
  const plan = otomatikDoldur({ days, kadro, kayitlar: {}, plan: {} });
  for (const p of kadro) {
    const t = kisiToplam(plan, p.id, days);
    assert.ok(t.enUzunArdisik <= 6, `${p.id} ${t.enUzunArdisik} gün üst üste`);
    for (const [hk, m] of Object.entries(t.haftalar)) {
      assert.ok(m <= 45 * 60, `${p.id} ${hk} → ${m} dk`);
    }
  }
});

test("form kontrolü hafta sonu izninde neden, saat kısıtında saat ister", () => {
  const bos = formDurumu({ gunler: {}, hafta: {} });
  assert.ok(!bos.dolu);

  const hataliCumartesi = formDurumu({
    gunler: { "2026-09-05": { tip: "izin", neden: "" } }, hafta: {},
  });
  assert.ok(!hataliCumartesi.gecerli);

  const duzgun = formDurumu({
    gunler: { "2026-09-05": { tip: "izin", neden: "Kardeşimin düğünü" } }, hafta: {},
  });
  assert.ok(duzgun.gecerli && duzgun.dolu && duzgun.izin === 1);

  const tersSaat = formDurumu({
    gunler: { "2026-09-07": { tip: "saat", enErken: "18:00", enGec: "14:00" } }, hafta: {},
  });
  assert.ok(!tersSaat.gecerli);
});
