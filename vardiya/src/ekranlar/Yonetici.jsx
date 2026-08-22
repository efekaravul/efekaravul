import React, { useMemo, useState } from "react";
import { C, SERIF, label, num, meta } from "../tokens.js";
import { GUNLER, HAFTA, IZIN_KOTA, KALIPLAR, tipBilgi } from "../data/sabitler.js";
import { iso } from "../lib/tarih.js";
import { gunDurumu, gunKapali, musaitlik, talepOzet } from "../lib/kurallar.js";
import { Sayac, Sekmeler, Rozet, Dugme, ProgramGoruntule, dokun } from "../parcalar/ortak.jsx";

export default function Yonetici({ token, days, paket, kararVer, sefKoduDegistir }) {
  const [sekme, setSekme] = useState("talepler");

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

  const gunSet = useMemo(() => new Set(days.map(iso)), [days]);

  const sayilar = useMemo(() => {
    let gonderen = 0, izin = 0, kotaAsan = 0;
    for (const p of kadro) {
      const k = kayitlar[p.id];
      if (k.gonderim) gonderen += 1;
      const kisiIzin = Object.entries(k.veri.gunler || {})
        .filter(([g, v]) => v.tip === "izin" && gunSet.has(g)).length;
      izin += kisiIzin;
      if (kisiIzin > IZIN_KOTA) kotaAsan += 1;
    }
    return { gonderen, izin, kotaAsan };
  }, [kadro, kayitlar, gunSet]);

  return (
    <div>
      <div className="flex" style={{ gap: 24, padding: "18px 20px",
        borderBottom: `1px solid ${C.rule}` }}>
        <Sayac deger={`${sayilar.gonderen}/${kadro.length}`} etiket="Gönderen" />
        <Sayac deger={sayilar.izin} etiket="İzin talebi" />
        <Sayac deger={sayilar.kotaAsan} etiket="Kota aşan" uyar={sayilar.kotaAsan > 0} />
      </div>

      <Sekmeler aktif={sekme} setAktif={setSekme} liste={[
        { id: "talepler", t: "Talepler" },
        { id: "kimler", t: "Kim gönderdi" },
        { id: "matris", t: "Ay matrisi" },
        { id: "hafta", t: "Müsaitlik" },
        { id: "kalip", t: "Kalıplar" },
        { id: "ayar", t: "Ayarlar" },
      ]} />

      {sekme === "talepler" && (
        <Talepler token={token} days={days} kadro={kadro} kayitlar={kayitlar}
                  gunSet={gunSet} kararVer={kararVer} />
      )}
      {sekme === "kimler" && <Kimler kadro={kadro} kayitlar={kayitlar} gunSet={gunSet} />}
      {sekme === "matris" && <Matris days={days} kadro={kadro} kayitlar={kayitlar} />}
      {sekme === "hafta" && <HaftaIzgara kadro={kadro} kayitlar={kayitlar} />}
      {sekme === "kalip" && <Kaliplar />}
      {sekme === "ayar" && <Ayarlar sefKoduDegistir={sefKoduDegistir} />}
    </div>
  );
}

/* ------------------------------- talepler --------------------------------- */
function Talepler({ token, kadro, kayitlar, gunSet, kararVer }) {
  const [kararlar, setKararlar] = useState({});

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
        const izinSayisi = Object.entries(t.kayit.veri.gunler || {})
          .filter(([g, v]) => v.tip === "izin" && gunSet.has(g)).length;
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
                  {!t.kayit.gonderim && (
                    <span style={{ ...label, marginLeft: 8 }}>taslak</span>
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

/* ------------------------------ kim gönderdi ------------------------------ */
function Kimler({ kadro, kayitlar, gunSet }) {
  const satirlar = kadro.map((p) => {
    const k = kayitlar[p.id];
    const gunler = Object.entries(k.veri.gunler || {}).filter(([g]) => gunSet.has(g));
    return {
      ...p,
      gonderim: k.gonderim,
      talep: gunler.length,
      izin: gunler.filter(([, v]) => v.tip === "izin").length,
      hafta: Object.values(k.veri.hafta || {}).filter((v) => v.mod && v.mod !== "tam").length,
      program: !!k.program,
    };
  });
  const bekleyen = satirlar.filter((s) => !s.gonderim);

  return (
    <div style={{ marginTop: 12 }}>
      {bekleyen.length > 0 && (
        <p style={{ ...label, padding: "0 20px 12px", lineHeight: 1.8, color: C.alarm }}>
          {bekleyen.length} kişi henüz göndermedi
        </p>
      )}
      <ul className="liste">
        {[...satirlar].sort((a, b) => (a.gonderim ? 1 : 0) - (b.gonderim ? 1 : 0) ||
                                      a.ad.localeCompare(b.ad, "tr")).map((s) => (
          <li key={s.id} className="flex ac" style={{ gap: 12, padding: "12px 20px",
            borderTop: `1px solid ${C.rule}` }}>
            <div className="f1">
              <div style={{ fontSize: 15, color: s.gonderim ? C.ink : C.muted }}>{s.ad}</div>
              <div style={{ ...meta, marginTop: 4 }}>
                {s.gonderim
                  ? `${new Date(s.gonderim).toLocaleDateString("tr-TR")} · ${s.talep} gün talebi`
                  : s.talep || s.hafta ? `taslak · ${s.talep} gün talebi` : "hiç girmedi"}
                {s.izin ? ` · ${s.izin} izin` : ""}
                {s.hafta ? ` · ${s.hafta} haftalık kısıt` : ""}
                {s.program ? " · ders programı var" : ""}
              </div>
            </div>
            <Rozet kod={s.gonderim ? "GELDİ" : "BEKLİYOR"} dolu={!!s.gonderim}
                   renk={s.gonderim ? C.ok : C.alarm} />
          </li>
        ))}
      </ul>
    </div>
  );
}

/* ------------------------------- ay matrisi ------------------------------- */
function Matris({ days, kadro, kayitlar }) {
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
        Kırmızı çubuk · o gün çalışamayan kişi sayısı
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
                    const hal = musaitlik(durum);
                    const metin = durum.talep ? tipBilgi(durum.talep.tip).kod
                                : hal === "kapalı" ? "DERS"
                                : hal === "kısıtlı" ? "~" : "";
                    return (
                      <td key={gunKey}
                        title={durum.talep
                          ? `${tipBilgi(durum.talep.tip).label}${durum.talep.neden ? " — " + durum.talep.neden : ""}`
                          : hal === "kapalı" ? "Haftalık: müsait değil" : ""}
                        style={{ textAlign: "center", fontSize: 8.5, padding: "6px 1px",
                          borderRight: `1px solid ${C.rule}`, borderBottom: `1px solid ${C.rule}`,
                          background: hal === "kapalı" ? C.ink
                                    : hal === "acik" ? C.paper : C.wash,
                          color: hal === "kapalı" ? C.paper : C.ink }}>
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
        Siyah · çalışamaz &nbsp;·&nbsp; gri · saat kısıtı veya tercih
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

/* -------------------------------- kalıplar -------------------------------- */
function Kaliplar() {
  return (
    <div style={{ padding: "24px 20px 0" }}>
      <p style={{ fontSize: 15, color: C.muted, lineHeight: 1.6 }}>
        Ağustos export'larındaki kasa vardiyalarından çıkarılan kalıplar.
        Talepler bunlara göre değerlendirilir.
      </p>
      <ul className="liste" style={{ marginTop: 18 }}>
        {KALIPLAR.map((k) => (
          <li key={k.grup} style={{ borderTop: `1px solid ${C.rule}`, padding: "14px 0" }}>
            <div className="flex ab" style={{ gap: 10 }}>
              <span style={{ fontFamily: SERIF, fontSize: 18 }}>{k.grup}</span>
              <span style={label}>{k.saat}</span>
            </div>
            <p style={{ ...num, fontSize: 13, color: C.muted, marginTop: 6 }}>{k.ornek}</p>
          </li>
        ))}
      </ul>
      <div style={{ borderTop: `1px solid ${C.ink}`, padding: "18px 0 8px" }}>
        <div style={label}>Mola kuralı</div>
        <p style={{ fontSize: 14, lineHeight: 1.7, marginTop: 8 }}>
          Ödenen saat = mağazada geçen süre − mola. 5,5 saate kadar 30 dk veya 1 saat
          tek mola; 9 saati aşan planlarda iki mola veriliyor.
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
