import React, { useMemo, useState } from "react";
import { C, SERIF, label, num } from "../tokens.js";
import { MAGAZA_ADI } from "../config.js";
import { dokun } from "../parcalar/ortak.jsx";

export default function Giris({ kadro, girisYap, sefGirisi, demo }) {
  const [mod, setMod] = useState("calisan");
  const [ara, setAra] = useState("");
  const [kod, setKod] = useState("");
  const [hata, setHata] = useState("");
  const [bekliyor, setBekliyor] = useState(false);

  const liste = useMemo(() => {
    const q = ara.trim().toLocaleLowerCase("tr");
    const c = kadro.filter((p) => p.rol !== "yonetici");
    return q ? c.filter((p) => p.ad.toLocaleLowerCase("tr").includes(q)) : c;
  }, [kadro, ara]);

  const sar = async (islem) => {
    setBekliyor(true); setHata("");
    try { await islem(); }
    catch (e) { setHata(e.message || "Bir şeyler ters gitti."); }
    finally { setBekliyor(false); }
  };

  return (
    <div style={{ background: C.ink, minHeight: "100vh", color: C.paper,
                  paddingTop: "env(safe-area-inset-top)" }}>
      <div className="dar" style={{ padding: "56px 20px 40px" }}>
        <h1 style={{ fontFamily: SERIF, fontWeight: 700, fontSize: 44, lineHeight: 0.9,
                     letterSpacing: "-0.045em", margin: 0 }}>VARDİYA</h1>
        <p style={{ ...label, color: "rgba(255,255,255,0.55)", marginTop: 12 }}>{MAGAZA_ADI}</p>

        <div className="flex" style={{ marginTop: 36, border: "1px solid rgba(255,255,255,0.25)" }}>
          {[{ id: "calisan", t: "Çalışan" }, { id: "yonetici", t: "Yönetici" }].map((r) => {
            const a = mod === r.id;
            return (
              <button key={r.id} onClick={() => { setMod(r.id); setHata(""); }}
                className="f1" style={{ ...label, ...dokun, color: a ? C.ink : "rgba(255,255,255,0.7)",
                  background: a ? C.paper : "transparent", border: "none", cursor: "pointer" }}>
                {r.t}
              </button>
            );
          })}
        </div>

        {mod === "calisan" ? (
          <div style={{ marginTop: 28 }}>
            <p style={{ ...label, color: "rgba(255,255,255,0.55)" }}>İsmini seç</p>
            <input value={ara} onChange={(e) => setAra(e.target.value)}
              placeholder="İsim ara" autoComplete="off"
              style={{ width: "100%", marginTop: 12, padding: "13px 12px", borderRadius: 0,
                border: "1px solid rgba(255,255,255,0.35)", background: "transparent",
                color: C.paper, fontSize: 16 }} />
            <ul className="liste" style={{ marginTop: 6 }}>
              {liste.map((p) => (
                <li key={p.id} style={{ borderTop: "1px solid rgba(255,255,255,0.15)" }}>
                  <button disabled={bekliyor} onClick={() => sar(() => girisYap(p.id))}
                    className="w100 flex ac jb" style={{ ...dokun, background: "none", border: "none",
                      color: C.paper, cursor: "pointer", fontSize: 17, textAlign: "left",
                      padding: "12px 0", opacity: bekliyor ? 0.5 : 1 }}>
                    {p.ad}<span style={{ color: "rgba(255,255,255,0.4)" }}>›</span>
                  </button>
                </li>
              ))}
              {liste.length === 0 && (
                <li style={{ ...label, color: "rgba(255,255,255,0.4)", paddingTop: 18 }}>
                  Bu isimde kimse yok
                </li>
              )}
            </ul>
          </div>
        ) : (
          <div style={{ marginTop: 28 }}>
            <p style={{ ...label, color: "rgba(255,255,255,0.55)" }}>Yönetici kodu</p>
            <input value={kod} onChange={(e) => { setKod(e.target.value); setHata(""); }}
              type="password" inputMode="numeric" placeholder="••••"
              onKeyDown={(e) => e.key === "Enter" && sar(() => sefGirisi(kod))}
              style={{ width: "100%", marginTop: 12, padding: "14px 12px", borderRadius: 0,
                border: "1px solid rgba(255,255,255,0.4)", background: "transparent",
                color: C.paper, fontSize: 22, letterSpacing: "0.4em", ...num }} />
            <button disabled={bekliyor} onClick={() => sar(() => sefGirisi(kod))}
              className="w100" style={{ ...label, ...dokun, letterSpacing: "0.2em", border: "none",
                background: C.paper, color: C.ink, cursor: "pointer", marginTop: 16, padding: 14 }}>
              {bekliyor ? "Kontrol ediliyor…" : "Giriş yap"}
            </button>
            <p style={{ ...label, color: "rgba(255,255,255,0.35)", marginTop: 16, lineHeight: 1.8 }}>
              İzin nedenleri ve ders programları yalnızca bu girişte görünür
            </p>
          </div>
        )}

        {hata && <p style={{ color: "#FF8B8B", fontSize: 14, marginTop: 16 }}>{hata}</p>}

        {demo && (
          <p style={{ ...label, color: "rgba(255,255,255,0.35)", marginTop: 28, lineHeight: 1.9 }}>
            Demo modu · veriler yalnızca bu telefonda tutuluyor.<br />
            Ortak sunucu için .env dosyasındaki anahtarları doldur.
          </p>
        )}
      </div>
    </div>
  );
}
