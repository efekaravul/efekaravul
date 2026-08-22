import React, { useMemo, useState } from "react";
import { C, SERIF, label, num, meta } from "../tokens.js";
import {
  VARDIYALAR, VARDIYA, GRUPLAR, GUNLER, HAFTA, IZIN_KOTA,
  ACILIS_MIN, KAPANIS_MIN, GUNLUK_MIN, tipBilgi,
} from "../data/sabitler.js";
import { iso, sure, haftaSonu } from "../lib/tarih.js";
import {
  gunDurumu, cakismalar, katiCakisma, gunKapsama, kisiToplam,
  otomatikDoldur, planUyarilari, vardiyaSure, talepOzet, gunKapali,
} from "../lib/kurallar.js";
import {
  Sayac, Sekmeler, Rozet, Uyari, Dugme, ProgramGoruntule, dokun,
} from "../parcalar/ortak.jsx";

export default function Yonetici({
  token, ay, days, paket, kararVer, planKaydet, planYayinla, sefKoduDegistir,
}) {
  const [sekme, setSekme] = useState("plan");
  const [plan, setPlan] = useState(paket.plan || {});
  const [yayin, setYayin] = useState(paket.yayin || null);
  const [isaret, setIsaret] = useState("");

  const kadro = useMemo(
    () => (paket.kadro || []).filter((p) => p.rol !== "yonetici"),
    [paket.kadro]
  );

  /* Talep + karar + program tek bir kayıt nesnesinde toplanır */
  const kayitlar = useMemo(() => {
    const out = {};
    for (const p of kadro) {
      const t = (paket.talepler || {})[p.id];
      const kararlar = {};
      Object.entries(paket.kararlar || {}).forEach(([k, v]) => {
        const [pid, gun] = k.split("|");
        if (pid === p.id) kararlar[gun] = v;
      });
      out[p.id] = {
        veri: (t && t.veri) || { gunler: {}, hafta: {} },
        gonderim: (t && t.gonderim) || null,
        program: (paket.programlar || {})[p.id] || null,
        kararlar,
      };
    }
    return out;
  }, [kadro, paket]);

  const planYaz = async (yeni, mesaj) => {
    const fark = {};
    const anahtarlar = new Set([...Object.keys(plan), ...Object.keys(yeni)]);
    for (const a of anahtarlar) if (plan[a] !== yeni[a]) fark[a] = yeni[a] || null;
    setPlan(yeni);
    if (!Object.keys(fark).length) return;
    setIsaret("kaydediliyor…");
    try { await planKaydet(fark); setIsaret(mesaj || "kaydedildi"); }
    catch (e) { setIsaret(e.message || "kaydedilemedi"); }
  };

  const gonderen = kadro.filter((p) => kayitlar[p.id].gonderim).length;
  const uyarilar = useMemo(
    () => planUyarilari(days, kadro, kayitlar, plan),
    [days, kadro, kayitlar, plan]
  );
  const katiUyari = uyarilar.filter((u) => u.seviye === "katı").length;

  return (
    <div>
      <div className="flex" style={{ gap: 22, padding: "18px 20px",
        borderBottom: `1px solid ${C.rule}` }}>
        <Sayac deger={`${gonderen}/${kadro.length}`} etiket="Gönderen" />
        <Sayac deger={katiUyari} etiket="Plan ihlali" uyar={katiUyari > 0} />
        <Sayac deger={yayin ? "Açık" : "Kapalı"} etiket="Yayın" />
      </div>

      <Sekmeler aktif={sekme} setAktif={setSekme} liste={[
        { id: "plan", t: "Plan" },
        { id: "talepler", t: "Talepler" },
        { id: "matris", t: "Ay matrisi" },
        { id: "hafta", t: "Müsaitlik" },
        { id: "kontrol", t: "Kontrol" },
        { id: "ayar", t: "Ayarlar" },
      ]} />

      {sekme === "plan" && (
        <PlanEkrani days={days} kadro={kadro} kayitlar={kayitlar} plan={plan}
          planYaz={planYaz} isaret={isaret} yayin={yayin}
          yayinla={async (a) => {
            setIsaret(a ? "yayınlanıyor…" : "yayın kapatılıyor…");
            try { await planYayinla(ay, a); setYayin(a ? Date.now() : null); setIsaret(a ? "yayınlandı" : "yayın kapalı"); }
            catch (e) { setIsaret(e.message); }
          }} />
      )}
      {sekme === "talepler" && (
        <Talepler token={token} days={days} kadro={kadro} kayitlar={kayitlar} kararVer={kararVer} />
      )}
      {sekme === "matris" && <Matris days={days} kadro={kadro} kayitlar={kayitlar} plan={plan} />}
      {sekme === "hafta" && <HaftaIzgara kadro={kadro} kayitlar={kayitlar} />}
      {sekme === "kontrol" && <Kontrol uyarilar={uyarilar} days={days} kadro={kadro} plan={plan} />}
      {sekme === "ayar" && <Ayarlar sefKoduDegistir={sefKoduDegistir} />}
    </div>
  );
}

/* --------------------------------- plan ----------------------------------- */
function PlanEkrani({ days, kadro, kayitlar, plan, planYaz, isaret, yayin, yayinla }) {
  const bugun = iso(new Date());
  const [gunKey, setGunKey] = useState(
    () => (days.some((d) => iso(d) === bugun) ? bugun : iso(days[0]))
  );
  const kapsama = gunKapsama(plan, gunKey);
  const gun = days.find((d) => iso(d) === gunKey) || days[0];

  const sirali = useMemo(() => {
    return [...kadro].sort((a, b) => {
      const av = plan[`${gunKey}|${a.id}`] ? 0 : 1;
      const bv = plan[`${gunKey}|${b.id}`] ? 0 : 1;
      if (av !== bv) return av - bv;
      return a.ad.localeCompare(b.ad, "tr");
    });
  }, [kadro, plan, gunKey]);

  const gunuDoldur = () =>
    planYaz(otomatikDoldur({ days: [gun], kadro, kayitlar, plan }), "gün dolduruldu");
  const ayiDoldur = () =>
    planYaz(otomatikDoldur({ days, kadro, kayitlar, plan }), "ay dolduruldu");
  const gunuBosalt = () => {
    const yeni = { ...plan };
    kadro.forEach((p) => delete yeni[`${gunKey}|${p.id}`]);
    planYaz(yeni, "gün boşaltıldı");
  };

  return (
    <div>
      <div className="kaydir" style={{ borderBottom: `1px solid ${C.rule}`, marginTop: 12 }}>
        <div className="flex" style={{ padding: "0 12px 10px", gap: 6 }}>
          {days.map((d) => {
            const k = iso(d);
            const s = k === gunKey;
            const kap = gunKapsama(plan, k);
            return (
              <button key={k} onClick={() => setGunKey(k)}
                style={{ ...dokun, minWidth: 46, padding: "8px 4px", cursor: "pointer",
                  border: `1px solid ${s ? C.ink : C.rule}`, background: s ? C.ink : C.paper,
                  color: s ? C.paper : haftaSonu(d) ? C.alarm : C.ink }}>
                <div style={{ ...num, fontSize: 15 }}>{String(d.getDate()).padStart(2, "0")}</div>
                <div style={{ fontSize: 9, opacity: 0.7 }}>{GUNLER[d.getDay()]}</div>
                <div style={{ height: 4, marginTop: 4,
                  background: kap.sorunlu ? C.alarm : s ? C.paper : C.ink,
                  opacity: kap.kisi ? 1 : 0.15 }} />
              </button>
            );
          })}
        </div>
      </div>

      <div className="flex" style={{ gap: 20, padding: "16px 20px" }}>
        <Sayac deger={`${kapsama.kisi}/${GUNLUK_MIN}`} etiket="Kişi" uyar={!!kapsama.eksikKisi} />
        <Sayac deger={`${kapsama.acilis}/${ACILIS_MIN}`} etiket="Açılış" uyar={!!kapsama.eksikAcilis} />
        <Sayac deger={`${kapsama.kapanis}/${KAPANIS_MIN}`} etiket="Kapanış" uyar={!!kapsama.eksikKapanis} />
        <Sayac deger={sure(kapsama.odenen)} etiket="Ödenen" />
      </div>

      <div className="flex" style={{ gap: 8, padding: "0 20px 8px" }}>
        <Dugme onClick={gunuDoldur}>Günü doldur</Dugme>
        <Dugme onClick={ayiDoldur}>Ayı doldur</Dugme>
        <Dugme onClick={gunuBosalt}>Boşalt</Dugme>
      </div>
      <p style={{ ...label, padding: "0 20px 12px" }}>{isaret || "Değişiklikler anında kaydedilir"}</p>

      <ul className="liste">
        {sirali.map((p) => {
          const vid = plan[`${gunKey}|${p.id}`] || "";
          const durum = gunDurumu(kayitlar[p.id], gunKey);
          const kapali = gunKapali(durum);
          const cak = vid ? cakismalar(durum, vid) : [];
          const t = kisiToplam(plan, p.id, days);
          const talep = durum.talep;
          return (
            <li key={p.id} style={{ borderTop: `1px solid ${C.rule}`, padding: "12px 20px",
              background: kapali && !vid ? C.wash : C.paper }}>
              <div className="flex ac" style={{ gap: 10 }}>
                <div className="f1">
                  <div style={{ fontSize: 15 }}>{p.ad}</div>
                  <div style={{ ...meta, marginTop: 4 }}>
                    {t.gun} gün · {sure(t.odenen)}
                    {talep ? ` · ${talepOzet(talep)}` : ""}
                    {durum.hafta.mod === "yok" ? " · haftalık kapalı" : ""}
                  </div>
                </div>
                <select value={vid} onChange={(e) => planYaz(
                    { ...plan, [`${gunKey}|${p.id}`]: e.target.value || undefined }, "kaydedildi")}
                  style={{ ...dokun, ...num, width: 148, padding: "8px 6px", borderRadius: 0, fontSize: 14,
                    border: `1px solid ${cak.some((c) => c.seviye === "katı") ? C.alarm : C.ink}`,
                    background: vid ? C.ink : C.paper, color: vid ? C.paper : C.ink }}>
                  <option value="">— izinli —</option>
                  {GRUPLAR.map((g) => (
                    <optgroup key={g} label={g}>
                      {VARDIYALAR.filter((v) => v.grup === g).map((v) => (
                        <option key={v.id} value={v.id}>
                          {katiCakisma(durum, v.id) ? "⚠ " : ""}{v.bas}–{v.bit}
                        </option>
                      ))}
                    </optgroup>
                  ))}
                </select>
              </div>
              {cak.length > 0 && (
                <p style={{ fontSize: 12.5, marginTop: 8, lineHeight: 1.5,
                  color: cak.some((c) => c.seviye === "katı") ? C.alarm : C.muted }}>
                  {cak.map((c) => c.metin).join(" · ")}
                </p>
              )}
            </li>
          );
        })}
      </ul>

      <div style={{ padding: "24px 20px calc(28px + env(safe-area-inset-bottom))" }}>
        <Dugme birincil sonuc={!!yayin} onClick={() => yayinla(!yayin)}>
          {yayin ? "Yayında · kapat" : "Planı yayınla"}
        </Dugme>
        <p style={{ ...label, textAlign: "center", marginTop: 12, lineHeight: 1.8 }}>
          {yayin
            ? "Herkes kendi vardiyalarını görüyor"
            : "Yayınlanana kadar planı kimse göremez"}
        </p>
      </div>
    </div>
  );
}

/* ------------------------------- talepler --------------------------------- */
function Talepler({ token, days, kadro, kayitlar, kararVer }) {
  const [kararlar, setKararlar] = useState({});
  const gunSet = useMemo(() => new Set(days.map(iso)), [days]);

  const liste = useMemo(() => {
    const out = [];
    for (const p of kadro) {
      const k = kayitlar[p.id];
      Object.entries(k.veri.gunler || {}).forEach(([gunKey, v]) => {
        if (gunSet.has(gunKey)) out.push({ ...p, gunKey, talep: v, kayit: k });
      });
    }
    return out.sort((a, b) => a.gunKey.localeCompare(b.gunKey) || a.ad.localeCompare(b.ad, "tr"));
  }, [kadro, kayitlar, gunSet]);

  const kararGoster = (pid, gunKey) =>
    kararlar[`${pid}|${gunKey}`] ?? (kayitlar[pid].kararlar[gunKey] || null);

  const ver = async (pid, gunKey, durum) => {
    const simdiki = kararGoster(pid, gunKey);
    const yeni = simdiki && simdiki.durum === durum ? null : { durum, not: "" };
    setKararlar((k) => ({ ...k, [`${pid}|${gunKey}`]: yeni }));
    try { await kararVer(pid, gunKey, yeni ? durum : null, ""); }
    catch { setKararlar((k) => ({ ...k, [`${pid}|${gunKey}`]: simdiki })); }
  };

  if (!liste.length) {
    return (
      <div className="merkez" style={{ padding: "64px 20px" }}>
        <p style={{ fontFamily: SERIF, fontSize: 20 }}>Bu ay için talep yok</p>
        <p style={{ ...label, marginTop: 8 }}>Çalışanlar girdikçe burada listelenir</p>
      </div>
    );
  }

  let son = null;
  return (
    <ul className="liste" style={{ marginTop: 12 }}>
      {liste.map((t, i) => {
        const d = new Date(`${t.gunKey}T00:00:00`);
        const yeniGun = t.gunKey !== son; son = t.gunKey;
        const tip = tipBilgi(t.talep.tip);
        const karar = kararGoster(t.id, t.gunKey);
        const izinSayisi = Object.values(t.kayit.veri.gunler || {})
          .filter((v) => v.tip === "izin").length;
        return (
          <React.Fragment key={`${t.id}-${t.gunKey}-${i}`}>
            {yeniGun && (
              <li style={{ borderTop: `1px solid ${C.rule}`, padding: "18px 20px 6px" }}>
                <span style={{ ...num, fontSize: 17 }}>{String(d.getDate()).padStart(2, "0")}</span>
                <span style={{ ...label, marginLeft: 8 }}>{GUNLER[d.getDay()]}</span>
              </li>
            )}
            <li className="flex at" style={{ gap: 12, padding: "10px 20px" }}>
              <Rozet kod={tip.kod} dolu={tip.katı} />
              <div className="f1">
                <div style={{ fontSize: 15 }}>
                  {t.ad}
                  {t.talep.tip === "izin" && izinSayisi > IZIN_KOTA && (
                    <span style={{ ...label, color: C.alarm, marginLeft: 8 }}>
                      kota aşımı ({izinSayisi})
                    </span>
                  )}
                </div>
                {t.talep.tip === "saat" && (
                  <p style={{ ...num, fontSize: 13, marginTop: 4 }}>{talepOzet(t.talep)}</p>
                )}
                {t.talep.neden ? (
                  <p style={{ fontSize: 14, color: C.muted, marginTop: 4, lineHeight: 1.5 }}>
                    {t.talep.neden}
                  </p>
                ) : null}
                {t.kayit.program && (t.talep.tip === "ders" || t.talep.tip === "saat") ? (
                  <ProgramGoruntule token={token} personelId={t.id}
                                    program={t.kayit.program} kompakt />
                ) : null}
                {t.talep.tip === "izin" && (
                  <div className="flex" style={{ gap: 8, marginTop: 10 }}>
                    {[
                      { id: "onay", t: "Onayla", renk: C.ok },
                      { id: "ret", t: "Reddet", renk: C.alarm },
                    ].map((b) => {
                      const s = karar && karar.durum === b.id;
                      return (
                        <button key={b.id} onClick={() => ver(t.id, t.gunKey, b.id)}
                          style={{ ...label, ...dokun, padding: "0 14px", cursor: "pointer",
                            border: `1px solid ${b.renk}`, background: s ? b.renk : "transparent",
                            color: s ? C.paper : b.renk }}>
                          {b.t}
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            </li>
          </React.Fragment>
        );
      })}
    </ul>
  );
}

/* ------------------------------- ay matrisi ------------------------------- */
function Matris({ days, kadro, kayitlar, plan }) {
  const W = 34, NW = 104;
  const yogunluk = useMemo(() => {
    const m = {};
    days.forEach((d) => {
      const gunKey = iso(d);
      m[gunKey] = kadro.filter((p) => gunKapali(gunDurumu(kayitlar[p.id], gunKey))).length;
    });
    return m;
  }, [days, kadro, kayitlar]);
  const enYogun = Math.max(1, ...Object.values(yogunluk));

  return (
    <div style={{ marginTop: 16 }}>
      <p style={{ ...label, padding: "0 20px 10px", lineHeight: 1.8 }}>
        Kırmızı çubuk · o gün hiç çalışamayan kişi sayısı
      </p>
      <div className="kaydir" style={{ borderTop: `1px solid ${C.rule}` }}>
        <table style={{ borderCollapse: "collapse", ...num }}>
          <thead>
            <tr>
              <th className="yapisik" style={{ width: NW, minWidth: NW, background: C.paper,
                zIndex: 2, textAlign: "left", padding: "6px 8px", ...label,
                borderRight: `1px solid ${C.ink}`, borderBottom: `1px solid ${C.ink}` }}>İsim</th>
              {days.map((d) => {
                const y = yogunluk[iso(d)];
                const yg = y >= 3;
                return (
                  <th key={iso(d)} style={{ width: W, minWidth: W, padding: "6px 2px 0",
                    verticalAlign: "bottom", borderBottom: `1px solid ${C.ink}`,
                    borderRight: `1px solid ${C.rule}` }}>
                    <div style={{ fontSize: 11, color: yg ? C.alarm : C.ink, fontWeight: yg ? 700 : 400 }}>
                      {String(d.getDate()).padStart(2, "0")}
                    </div>
                    <div style={{ fontSize: 8, color: C.muted }}>{GUNLER[d.getDay()]}</div>
                    <div className="flex jc" style={{ height: 18, alignItems: "flex-end", paddingBottom: 3 }}>
                      <div style={{ width: 12, height: Math.max(y ? 2 : 0, (y / enYogun) * 14),
                        background: yg ? C.alarm : C.ink, opacity: yg ? 1 : 0.35 }} />
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {kadro.map((p) => {
              const k = kayitlar[p.id];
              return (
                <tr key={p.id}>
                  <td className="yapisik" style={{ background: C.paper, zIndex: 2, padding: "6px 8px",
                    fontSize: 11.5, whiteSpace: "nowrap", color: k.gonderim ? C.ink : C.muted,
                    borderRight: `1px solid ${C.ink}`, borderBottom: `1px solid ${C.rule}` }}>
                    {p.ad}
                    {k.program ? <span style={{ color: C.alarm, marginLeft: 4 }}>•</span> : null}
                  </td>
                  {days.map((d) => {
                    const gunKey = iso(d);
                    const durum = gunDurumu(k, gunKey);
                    const vid = plan[`${gunKey}|${p.id}`];
                    const kati = durum.talep && tipBilgi(durum.talep.tip).katı;
                    const kapali = gunKapali(durum);
                    const metin = vid ? VARDIYA[vid].bas.slice(0, 2)
                                 : durum.talep ? tipBilgi(durum.talep.tip).kod
                                 : kapali ? "—" : "";
                    return (
                      <td key={gunKey}
                        title={durum.talep
                          ? `${tipBilgi(durum.talep.tip).label}${durum.talep.neden ? " — " + durum.talep.neden : ""}`
                          : kapali ? "Haftalık: müsait değil" : ""}
                        style={{ textAlign: "center", fontSize: 8.5, padding: "6px 1px",
                          borderRight: `1px solid ${C.rule}`, borderBottom: `1px solid ${C.rule}`,
                          background: vid ? C.ok : kati || kapali ? C.ink : durum.talep ? C.wash : C.paper,
                          color: vid || kati || kapali ? C.paper : C.ink }}>
                        {metin}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p style={{ ...label, padding: "16px 20px", lineHeight: 2 }}>
        Yeşil · yazılmış vardiyanın başlangıcı &nbsp;·&nbsp; siyah · çalışamaz
        &nbsp;·&nbsp; soluk isim · göndermedi &nbsp;·&nbsp;
        <span style={{ color: C.alarm }}>•</span> ders programı var
      </p>
    </div>
  );
}

/* ------------------------------- müsaitlik -------------------------------- */
function HaftaIzgara({ kadro, kayitlar }) {
  return (
    <div style={{ marginTop: 16 }}>
      <p style={{ ...label, padding: "0 20px 12px", lineHeight: 1.8 }}>
        Ders programından gelen sabit müsaitlik · ayın tamamı için geçerli
      </p>
      <div className="kaydir" style={{ borderTop: `1px solid ${C.rule}` }}>
        <table style={{ borderCollapse: "collapse", fontSize: 11, ...num }}>
          <thead>
            <tr>
              <th className="yapisik" style={{ background: C.paper, zIndex: 2, textAlign: "left",
                padding: "6px 8px", ...label, borderRight: `1px solid ${C.ink}`,
                borderBottom: `1px solid ${C.ink}` }}>İsim</th>
              {HAFTA.map((wd) => (
                <th key={wd} style={{ padding: "6px 8px", minWidth: 64, ...label, color: C.ink,
                  borderBottom: `1px solid ${C.ink}`, borderRight: `1px solid ${C.rule}` }}>
                  {GUNLER[wd]}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {kadro.map((p) => {
              const hafta = kayitlar[p.id].veri.hafta || {};
              const kisitli = Object.values(hafta).some((v) => v.mod && v.mod !== "tam");
              return (
                <tr key={p.id}>
                  <td className="yapisik" style={{ background: C.paper, zIndex: 2, padding: "6px 8px",
                    whiteSpace: "nowrap", color: kisitli ? C.ink : C.muted,
                    borderRight: `1px solid ${C.ink}`, borderBottom: `1px solid ${C.rule}` }}>
                    {p.ad}
                  </td>
                  {HAFTA.map((wd) => {
                    const h = hafta[wd] || hafta[String(wd)] || {};
                    let txt = "—", bg = C.paper, fg = "#C9C6C2";
                    if (h.mod === "yok") { txt = "Kapalı"; bg = C.ink; fg = C.paper; }
                    else if (h.mod === "sonra") { txt = `${h.saat || "?"}→`; bg = C.wash; fg = C.ink; }
                    else if (h.mod === "once") { txt = `→${h.saat || "?"}`; bg = C.wash; fg = C.ink; }
                    else if (h.mod === "tam") { txt = "Tam"; fg = C.ink; }
                    return (
                      <td key={wd} style={{ textAlign: "center", padding: "7px 4px",
                        background: bg, color: fg, borderRight: `1px solid ${C.rule}`,
                        borderBottom: `1px solid ${C.rule}` }}>{txt}</td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* -------------------------------- kontrol --------------------------------- */
function Kontrol({ uyarilar, days, kadro, plan }) {
  const kati = uyarilar.filter((u) => u.seviye === "katı");
  const yumusak = uyarilar.filter((u) => u.seviye !== "katı");
  const toplamlar = kadro
    .map((p) => ({ ...p, ...kisiToplam(plan, p.id, days) }))
    .sort((a, b) => b.odenen - a.odenen);

  return (
    <div style={{ padding: "20px 20px calc(28px + env(safe-area-inset-bottom))" }}>
      {kati.length === 0 && yumusak.length === 0 ? (
        <p style={{ fontFamily: SERIF, fontSize: 20 }}>Plan temiz — ihlal yok.</p>
      ) : (
        <>
          {kati.length > 0 && (
            <>
              <div style={label}>Düzeltilmeli ({kati.length})</div>
              {kati.slice(0, 40).map((u, i) => (
                <Uyari key={i}>{u.gunKey ? `${u.gunKey.slice(8)} · ` : ""}{u.metin}</Uyari>
              ))}
              {kati.length > 40 && (
                <p style={{ ...label, marginTop: 10 }}>… ve {kati.length - 40} tane daha</p>
              )}
            </>
          )}
          {yumusak.length > 0 && (
            <div style={{ marginTop: 24 }}>
              <div style={label}>Tercihe ters ({yumusak.length})</div>
              {yumusak.slice(0, 20).map((u, i) => (
                <Uyari key={i} renk={C.muted}>
                  {u.gunKey ? `${u.gunKey.slice(8)} · ` : ""}{u.metin}
                </Uyari>
              ))}
            </div>
          )}
        </>
      )}

      <div style={{ marginTop: 32, borderTop: `1px solid ${C.ink}`, paddingTop: 16 }}>
        <div style={label}>Ay toplamı · ödenen saat</div>
        <ul className="liste" style={{ marginTop: 10 }}>
          {toplamlar.map((t) => (
            <li key={t.id} className="flex ac jb"
                style={{ padding: "10px 0", borderTop: `1px solid ${C.rule}` }}>
              <span style={{ fontSize: 14 }}>{t.ad}</span>
              <span style={{ ...num, fontSize: 14 }}>
                {t.gun} gün · {sure(t.odenen)}
              </span>
            </li>
          ))}
        </ul>
      </div>

      <div style={{ marginTop: 32, borderTop: `1px solid ${C.ink}`, paddingTop: 16 }}>
        <div style={label}>Mola kuralı</div>
        <p style={{ fontSize: 14, lineHeight: 1.7, marginTop: 8 }}>
          Ödenen saat = mağazada geçen süre − mola. 5,5 saate kadar 30 dk, 9 saate kadar
          1 saat tek mola; 9 saati aşan planlarda iki mola. Tablodaki süreler bu kurala göre.
        </p>
      </div>
    </div>
  );
}

/* -------------------------------- ayarlar --------------------------------- */
function Ayarlar({ sefKoduDegistir }) {
  const [yeni, setYeni] = useState("");
  const [mesaj, setMesaj] = useState("");
  const uygula = async () => {
    try { await sefKoduDegistir(yeni); setMesaj("Kod değişti."); setYeni(""); }
    catch (e) { setMesaj(e.message || "Değiştirilemedi."); }
  };
  return (
    <div style={{ padding: "20px 20px calc(28px + env(safe-area-inset-bottom))" }}>
      <div style={label}>Yönetici kodu</div>
      <p style={{ fontSize: 14, color: C.muted, lineHeight: 1.6, marginTop: 8 }}>
        Bu kodu bilen herkes izin nedenlerini ve ders programlarını görebilir.
        Kadroda değişiklik olduğunda yenile.
      </p>
      <input value={yeni} onChange={(e) => setYeni(e.target.value)} inputMode="numeric"
        placeholder="Yeni kod (4–8 rakam)"
        style={{ width: "100%", marginTop: 12, padding: "13px 12px", borderRadius: 0,
          border: `1px solid ${C.ink}`, background: C.paper, color: C.ink, fontSize: 16, ...num }} />
      <Dugme onClick={uygula} disabled={!/^[0-9]{4,8}$/.test(yeni)} style={{ marginTop: 12 }}>
        Kodu değiştir
      </Dugme>
      {mesaj && <p style={{ fontSize: 13, marginTop: 12, color: C.muted }}>{mesaj}</p>}
    </div>
  );
}
