import React, { useEffect, useMemo, useRef, useState } from "react";
import { C, label, num } from "../tokens.js";
import {
  TALEP_TIPLERI, MUSAITLIK, SAATLER, GUNLER, HAFTA, IZIN_KOTA, MAX_DOSYA, tipBilgi,
} from "../data/sabitler.js";
import { iso, haftaSonu } from "../lib/tarih.js";
import { formDurumu } from "../lib/kurallar.js";
import { hazirla } from "../lib/dosya.js";
import {
  Sayac, Sekmeler, Rozet, Uyari, Dugme, SaatSecici, ProgramGoruntule, dokun,
} from "../parcalar/ortak.jsx";

const bosVeri = () => ({ gunler: {}, hafta: {} });

export default function Calisan({
  token, ay, days, paket, kaydet, programYukle, programSil,
}) {
  const [sekme, setSekme] = useState("gunler");
  const [acik, setAcik] = useState(null);
  const [veri, setVeri] = useState(() => (paket.talep && paket.talep.veri) || bosVeri());
  const [gonderim, setGonderim] = useState((paket.talep && paket.talep.gonderim) || null);
  const [durum, setDurum] = useState("");
  const [yuklemeHata, setYuklemeHata] = useState("");
  const ilk = useRef(true);

  /* Ay veya kişi değişince formu sunucudan gelenle tazele */
  useEffect(() => {
    setVeri((paket.talep && paket.talep.veri) || bosVeri());
    setGonderim((paket.talep && paket.talep.gonderim) || null);
    ilk.current = true;
  }, [paket.talep, ay]);

  /* Telefonda "kaydet" düğmesi aramasın diye yazdıkça sessizce kaydeder */
  useEffect(() => {
    if (ilk.current) { ilk.current = false; return; }
    const z = setTimeout(async () => {
      setDurum("kaydediliyor");
      try { await kaydet(veri, false); setGonderim(null); setDurum("kaydedildi"); }
      catch (e) { setDurum(e.message || "kaydedilemedi"); }
    }, 700);
    return () => clearTimeout(z);
  }, [veri]);

  const kontrol = useMemo(() => formDurumu(veri), [veri]);
  const programEksik = (kontrol.ders > 0 || kontrol.haftaKisit > 0) && !paket.program;
  const hazir = kontrol.dolu && kontrol.gecerli && !programEksik;

  const setGun = (gunKey, yama) =>
    setVeri((v) => {
      const g = { ...v.gunler };
      if (yama === null) delete g[gunKey];
      else g[gunKey] = { ...(g[gunKey] || { neden: "" }), ...yama };
      return { ...v, gunler: g };
    });

  const setHafta = (wd, yama) =>
    setVeri((v) => ({ ...v, hafta: { ...v.hafta, [wd]: { ...(v.hafta[wd] || {}), ...yama } } }));

  const dosyaSec = async (e) => {
    const f = e.target.files && e.target.files[0];
    e.target.value = "";
    if (!f) return;
    if (f.size > MAX_DOSYA) {
      setYuklemeHata(`Dosya çok büyük (${Math.round(f.size / 1024 / 1024)} MB).`);
      return;
    }
    setYuklemeHata("Yükleniyor…");
    try {
      await programYukle(await hazirla(f));
      setYuklemeHata("");
    } catch (err) {
      setYuklemeHata(err.message || "Yükleme başarısız. Tekrar dene.");
    }
  };

  const gonder = async () => {
    setDurum("gönderiliyor");
    try {
      const c = await kaydet(veri, true);
      setGonderim((c && c.gonderim) || Date.now());
      setDurum("gönderildi");
    } catch (e) { setDurum(e.message || "gönderilemedi"); }
  };

  return (
    <div>
      <div className="flex" style={{ gap: 26, padding: "18px 20px",
        borderBottom: `1px solid ${C.rule}` }}>
        <Sayac deger={`${kontrol.izin}/${IZIN_KOTA}`} etiket="İzin" uyar={kontrol.izin > IZIN_KOTA} />
        <Sayac deger={Object.keys(veri.gunler).length} etiket="Gün talebi" />
        <Sayac deger={paket.program ? "Var" : "Yok"} etiket="Ders programı" uyar={programEksik} />
      </div>

      <Sekmeler aktif={sekme} setAktif={setSekme} liste={[
        { id: "gunler", t: "Günler" },
        { id: "hafta", t: "Haftalık müsaitlik" },
        { id: "program", t: "Ders programı" },
      ]} />

      {sekme === "gunler" && (
        <ul className="liste" style={{ marginTop: 16 }}>
          {days.map((d) => {
            const gunKey = iso(d);
            const v = veri.gunler[gunKey];
            const karar = paket.kararlar && paket.kararlar[gunKey];
            const acikMi = acik === gunKey;
            const hs = haftaSonu(d);
            const t = v ? tipBilgi(v.tip) : null;
            return (
              <li key={gunKey} style={{ borderTop: `1px solid ${C.rule}` }}>
                <button onClick={() => setAcik(acikMi ? null : gunKey)}
                  className="flex ac w100 anim" style={{ ...dokun, gap: 12, textAlign: "left",
                    background: acikMi ? C.wash : C.paper, border: "none", cursor: "pointer",
                    padding: "10px 20px" }}>
                  <span style={{ ...num, fontSize: 17, width: 26, color: hs ? C.alarm : C.ink }}>
                    {String(d.getDate()).padStart(2, "0")}
                  </span>
                  <span style={{ ...label, width: 32 }}>{GUNLER[d.getDay()]}</span>
                  <span className="f1" />
                  {karar && (
                    <Rozet kod={karar.durum === "onay" ? "ONAY" : "RET"} dolu
                           renk={karar.durum === "onay" ? C.ok : C.alarm} />
                  )}
                  {t ? <Rozet kod={t.kod} dolu={t.katı} />
                     : <span style={{ ...label, color: "#C9C6C2" }}>Boş</span>}
                  <span style={{ color: C.muted, fontSize: 16, width: 12 }}>{acikMi ? "−" : "+"}</span>
                </button>

                {acikMi && (
                  <div style={{ background: C.wash, padding: "0 20px 20px" }}>
                    <div className="flex wrap" style={{ gap: 8 }}>
                      {TALEP_TIPLERI.map((tp) => {
                        const s = v && v.tip === tp.id;
                        return (
                          <button key={tp.id} onClick={() => setGun(gunKey, { tip: tp.id })}
                            style={{ ...dokun, padding: "10px 13px", border: `1px solid ${C.ink}`,
                              borderRadius: 0, background: s ? C.ink : "transparent",
                              color: s ? C.paper : C.ink, cursor: "pointer", fontSize: 14 }}>
                            {tp.label}
                          </button>
                        );
                      })}
                      {v && (
                        <button onClick={() => setGun(gunKey, null)}
                          style={{ ...dokun, padding: "10px 13px", border: `1px solid ${C.rule}`,
                            background: "transparent", color: C.muted, cursor: "pointer", fontSize: 14 }}>
                          Kaldır
                        </button>
                      )}
                    </div>

                    {v && v.tip === "saat" && (
                      <div className="flex" style={{ gap: 10, marginTop: 16 }}>
                        <SaatSecici etiket="En erken başlarım" deger={v.enErken || ""}
                          secenekler={SAATLER} onChange={(x) => setGun(gunKey, { enErken: x })} />
                        <SaatSecici etiket="En geç çıkarım" deger={v.enGec || ""}
                          secenekler={SAATLER} onChange={(x) => setGun(gunKey, { enGec: x })} />
                      </div>
                    )}

                    {v && (
                      <div style={{ marginTop: 16 }}>
                        <div style={label}>
                          Neden {hs && v.tip === "izin" ? "(zorunlu)" : "(opsiyonel)"}
                        </div>
                        <textarea rows={2} value={v.neden || ""}
                          onChange={(e) => setGun(gunKey, { neden: e.target.value })}
                          placeholder="Sadece şefin ve müdürler görür"
                          style={{ width: "100%", marginTop: 8, padding: 12, borderRadius: 0,
                            border: `1px solid ${hs && v.tip === "izin" && !(v.neden || "").trim()
                              ? C.alarm : C.ink}`, background: C.paper, color: C.ink,
                            fontSize: 16, resize: "vertical" }} />
                      </div>
                    )}

                    {karar && (
                      <p style={{ fontSize: 13, marginTop: 14, lineHeight: 1.6,
                                  color: karar.durum === "onay" ? C.ok : C.alarm }}>
                        Şef {karar.durum === "onay" ? "onayladı" : "reddetti"}
                        {karar.not ? ` — ${karar.not}` : ""}
                      </p>
                    )}
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}

      {sekme === "hafta" && (
        <div style={{ padding: "20px 20px 0" }}>
          <p style={{ fontSize: 15, color: C.muted, lineHeight: 1.6 }}>
            Ders programına göre her gün hangi saatlerde çalışabileceğini işaretle.
            Şef ayın tamamını buna bakarak yazar, her ay tekrar girmene gerek kalmaz.
          </p>
          <ul className="liste" style={{ marginTop: 16 }}>
            {HAFTA.map((wd) => {
              const h = veri.hafta[wd] || {};
              return (
                <li key={wd} style={{ borderTop: `1px solid ${C.rule}`, padding: "14px 0" }}>
                  <div className="flex ac" style={{ gap: 12 }}>
                    <span style={{ ...label, width: 38, color: C.ink }}>{GUNLER[wd]}</span>
                    <div className="flex wrap f1" style={{ gap: 6 }}>
                      {MUSAITLIK.map((m) => {
                        const s = (h.mod || "tam") === m.id;
                        return (
                          <button key={m.id} onClick={() => setHafta(wd, { mod: m.id })}
                            style={{ ...dokun, padding: "8px 11px",
                              border: `1px solid ${s ? C.ink : C.rule}`,
                              background: s ? C.ink : "transparent", color: s ? C.paper : C.muted,
                              cursor: "pointer", fontSize: 13 }}>
                            {m.label}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                  {(h.mod === "sonra" || h.mod === "once") && (
                    <div style={{ marginTop: 12, paddingLeft: 50 }}>
                      <SaatSecici secenekler={SAATLER} deger={h.saat || ""}
                        etiket={h.mod === "sonra" ? "Şu saatten sonra" : "Şu saate kadar"}
                        onChange={(x) => setHafta(wd, { saat: x })} />
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        </div>
      )}

      {sekme === "program" && (
        <div style={{ padding: "20px 20px 0" }}>
          <p style={{ fontSize: 15, color: C.muted, lineHeight: 1.6 }}>
            Ders programının fotoğrafı veya PDF'i. Fotoğrafı çekip yükleyebilirsin,
            telefonda küçültülüp gönderilir. Dosyayı yalnızca kasa şefi ve müdürler açabilir.
          </p>
          {paket.program ? (
            <div style={{ marginTop: 16 }}>
              <div className="flex ac" style={{ border: `1px solid ${C.ink}`, padding: 12, gap: 12 }}>
                <div className="flex ac jc" style={{ width: 44, height: 44, background: C.wash, ...label }}>
                  {(paket.program.ad || "").toLowerCase().endsWith(".pdf") ? "PDF" : "IMG"}
                </div>
                <div className="f1">
                  <div style={{ fontSize: 14, overflow: "hidden", textOverflow: "ellipsis",
                                whiteSpace: "nowrap" }}>{paket.program.ad}</div>
                  <div style={{ ...label, marginTop: 3 }}>
                    {Math.round((paket.program.boyut || 0) / 1024)} KB · yüklendi
                  </div>
                </div>
                <button onClick={programSil} style={{ ...label, ...dokun, background: "none",
                  border: "none", cursor: "pointer", color: C.alarm }}>Sil</button>
              </div>
              <ProgramGoruntule token={token} personelId={null} program={paket.program} />
            </div>
          ) : (
            <label className="flex ac jc" style={{ marginTop: 16, cursor: "pointer", ...label,
              border: `1px dashed ${programEksik ? C.alarm : C.ink}`, padding: "28px 12px",
              color: programEksik ? C.alarm : C.ink }}>
              Fotoğraf çek veya dosya seç
              <input type="file" accept="image/*,application/pdf" onChange={dosyaSec}
                     style={{ display: "none" }} />
            </label>
          )}
          {yuklemeHata && <p style={{ fontSize: 13, color: C.alarm, marginTop: 12 }}>{yuklemeHata}</p>}
        </div>
      )}

      <div style={{ padding: "24px 20px calc(28px + env(safe-area-inset-bottom))" }}>
          {kontrol.eksikler.map((m) => <Uyari key={m}>{m}</Uyari>)}
          {programEksik && <Uyari>Ders / saat kısıtı işaretledin, ders programını yükle.</Uyari>}
          {kontrol.izin > IZIN_KOTA && (
            <Uyari>Aylık izin hakkın {IZIN_KOTA} gün. Fazlası için şefinle konuş.</Uyari>
          )}
          <Dugme birincil sonuc={!!gonderim} disabled={!hazir} onClick={gonder}
                 style={{ marginTop: 16 }}>
            {gonderim ? "Gönderildi" : "Şefe gönder"}
          </Dugme>
          <p style={{ ...label, textAlign: "center", marginTop: 12 }}>
            {gonderim
              ? `${new Date(gonderim).toLocaleDateString("tr-TR")} tarihinde iletildi`
              : durum === "kaydediliyor" ? "Kaydediliyor…"
              : durum === "kaydedildi" ? "Taslak kaydedildi"
              : durum || "Değişiklikler otomatik kaydedilir"}
          </p>
      </div>
    </div>
  );
}

