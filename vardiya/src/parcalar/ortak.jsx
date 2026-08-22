import React, { useEffect, useState } from "react";
import { C, SERIF, SANS, label, num } from "../tokens.js";
import { AYLAR } from "../data/sabitler.js";
import { api } from "../lib/api.js";
import { dataUrlBlobUrl } from "../lib/dosya.js";

export const dokun = { minHeight: 44 }; // telefonda güvenli dokunma alanı

export function Baslik({ ad, alt, cikis }) {
  return (
    <header style={{ background: C.ink, color: C.paper,
                     paddingTop: "env(safe-area-inset-top)" }}>
      <div className="orta flex ac jb" style={{ padding: "14px 20px" }}>
        <div>
          <div style={{ fontFamily: SERIF, fontWeight: 700, fontSize: 24,
                        lineHeight: 1, letterSpacing: "-0.04em" }}>VARDİYA</div>
          <div style={{ ...label, color: "rgba(255,255,255,0.55)", marginTop: 6 }}>
            {ad}{alt ? ` · ${alt}` : ""}
          </div>
        </div>
        <button onClick={cikis} style={{ ...label, ...dokun, color: "rgba(255,255,255,0.7)",
          background: "none", border: "1px solid rgba(255,255,255,0.3)",
          padding: "0 14px", cursor: "pointer" }}>Çıkış</button>
      </div>
    </header>
  );
}

export function AyBar({ ay, setAy }) {
  const kaydir = (y) => {
    const d = new Date(ay.y, ay.m + y, 1);
    setAy({ y: d.getFullYear(), m: d.getMonth() });
  };
  const ok = { background: "none", border: "none", cursor: "pointer",
               fontSize: 22, color: C.ink, ...dokun, minWidth: 44 };
  return (
    <div className="flex ac jb" style={{ padding: "6px 12px", borderBottom: `1px solid ${C.rule}` }}>
      <button onClick={() => kaydir(-1)} aria-label="Önceki ay" style={ok}>‹</button>
      <div style={{ fontFamily: SERIF, fontSize: 21, letterSpacing: "-0.02em" }}>
        {AYLAR[ay.m]} {ay.y}
      </div>
      <button onClick={() => kaydir(1)} aria-label="Sonraki ay" style={ok}>›</button>
    </div>
  );
}

export function Sekmeler({ aktif, setAktif, liste }) {
  return (
    <div className="flex kaydir" style={{ gap: 18, padding: "16px 20px 0" }}>
      {liste.map((s) => (
        <button key={s.id} onClick={() => setAktif(s.id)}
          style={{ ...label, background: "none", border: "none", cursor: "pointer",
            whiteSpace: "nowrap", paddingBottom: 8, color: aktif === s.id ? C.ink : C.muted,
            borderBottom: aktif === s.id ? `2px solid ${C.ink}` : "2px solid transparent" }}>
          {s.t}
        </button>
      ))}
    </div>
  );
}

export function Sayac({ deger, etiket, uyar }) {
  return (
    <div>
      <div style={{ ...num, fontSize: 22, lineHeight: 1, color: uyar ? C.alarm : C.ink }}>{deger}</div>
      <div style={{ ...label, marginTop: 6 }}>{etiket}</div>
    </div>
  );
}

export function Rozet({ kod, dolu, renk }) {
  const zemin = renk || C.ink;
  return (
    <span style={{ ...label, color: dolu ? C.paper : zemin, background: dolu ? zemin : "transparent",
      border: dolu ? "none" : `1px solid ${C.rule}`, padding: "4px 8px",
      letterSpacing: "0.12em", whiteSpace: "nowrap" }}>{kod}</span>
  );
}

export function Uyari({ children, renk = C.alarm }) {
  return (
    <p style={{ fontSize: 13, lineHeight: 1.6, color: renk, marginTop: 12,
                borderLeft: `2px solid ${renk}`, paddingLeft: 12 }}>{children}</p>
  );
}

export function Dugme({ children, birincil, sonuc, ...rest }) {
  const pasif = rest.disabled;
  return (
    <button {...rest} style={{
      ...label, ...dokun, letterSpacing: "0.2em", width: "100%", cursor: pasif ? "not-allowed" : "pointer",
      border: birincil ? "none" : `1px solid ${C.ink}`,
      background: pasif ? C.rule : birincil ? (sonuc ? C.ok : C.ink) : "transparent",
      color: pasif ? C.muted : birincil ? C.paper : C.ink,
      padding: "14px 12px", ...(rest.style || {}),
    }}>{children}</button>
  );
}

export function SaatSecici({ etiket, deger, onChange, secenekler }) {
  return (
    <div className="f1">
      <div style={label}>{etiket}</div>
      <select value={deger} onChange={(e) => onChange(e.target.value)}
        style={{ width: "100%", marginTop: 6, padding: "11px 8px", borderRadius: 0, ...dokun,
          border: `1px solid ${C.ink}`, background: C.paper, color: C.ink, fontSize: 16, ...num }}>
        <option value="">—</option>
        {secenekler.map((s) => <option key={s} value={s}>{s}</option>)}
      </select>
    </div>
  );
}

export function Yukleniyor({ metin = "Yükleniyor" }) {
  return (
    <div className="flex ac jc" style={{ minHeight: 220 }}>
      <span style={label}>{metin}…</span>
    </div>
  );
}

export function HataKutusu({ hata, tekrar }) {
  if (!hata) return null;
  return (
    <div style={{ margin: 20, border: `1px solid ${C.alarm}`, padding: 16 }}>
      <div style={{ ...label, color: C.alarm }}>Sorun</div>
      <p style={{ fontSize: 14, marginTop: 8, lineHeight: 1.6 }}>{hata}</p>
      {tekrar && (
        <button onClick={tekrar} style={{ ...label, ...dokun, marginTop: 12, background: "none",
          border: `1px solid ${C.ink}`, padding: "0 14px", cursor: "pointer", color: C.ink }}>
          Tekrar dene
        </button>
      )}
    </div>
  );
}

/* Ders programını ancak sahibi veya şef açabilir; dosya isteğe bağlı olarak
   sunucudan çekilir, önden indirilmez.                                     */
export function ProgramGoruntule({ token, personelId, program, kompakt }) {
  const [url, setUrl] = useState(null);
  const [durum, setDurum] = useState("bekliyor");
  const [tur, setTur] = useState("");

  useEffect(() => () => { if (url) URL.revokeObjectURL(url); }, [url]);

  const ac = async () => {
    setDurum("yukleniyor");
    try {
      const d = await api.programAc(token, personelId);
      if (!d || !d.icerik) { setDurum("yok"); return; }
      setTur(d.tur || "");
      setUrl(dataUrlBlobUrl(d.icerik));
      setDurum("hazir");
    } catch { setDurum("yok"); }
  };

  if (durum === "bekliyor") {
    return (
      <button onClick={ac} style={{ ...label, ...dokun, color: C.ink, background: "none",
        border: `1px solid ${C.ink}`, padding: "0 12px", cursor: "pointer",
        marginTop: kompakt ? 8 : 16 }}>Ders programını aç</button>
    );
  }
  if (durum === "yukleniyor") return <p style={{ ...label, marginTop: 12 }}>Açılıyor…</p>;
  if (durum === "yok") return <p style={{ fontSize: 13, color: C.alarm, marginTop: 12 }}>Dosya bulunamadı.</p>;

  const pdf = tur === "application/pdf" || (program?.ad || "").toLowerCase().endsWith(".pdf");
  return (
    <div style={{ marginTop: 12, border: `1px solid ${C.rule}` }}>
      {pdf
        ? <iframe src={url} title="Ders programı" style={{ width: "100%", height: 380, border: "none" }} />
        : <img src={url} alt="Ders programı" style={{ width: "100%", display: "block" }} />}
      <a href={url} target="_blank" rel="noreferrer"
         style={{ ...label, color: C.ink, display: "block", padding: 14,
                  borderTop: `1px solid ${C.rule}`, textDecoration: "none" }}>
        Yeni sekmede aç
      </a>
    </div>
  );
}

export const stilSans = SANS;

/* iPhone'da "Ana ekrana ekle" tarayıcıdan yapılır; kullanıcı bir kez
   ekleyince bu şerit bir daha çıkmaz.                                   */
export function EkleIpucu() {
  const [gizli, setGizli] = useState(() => {
    try { return localStorage.getItem("vardiya-ipucu") === "kapali"; } catch { return true; }
  });
  const [uygun, setUygun] = useState(false);

  useEffect(() => {
    const standalone =
      window.matchMedia("(display-mode: standalone)").matches ||
      window.navigator.standalone === true;
    const ios = /iphone|ipad|ipod/i.test(navigator.userAgent);
    setUygun(ios && !standalone);
  }, []);

  if (gizli || !uygun) return null;
  const kapat = () => {
    try { localStorage.setItem("vardiya-ipucu", "kapali"); } catch { /* özel sekme */ }
    setGizli(true);
  };
  return (
    <div className="flex ac" style={{ gap: 12, background: C.wash, padding: "12px 20px",
      borderBottom: `1px solid ${C.rule}` }}>
      <p className="f1" style={{ fontSize: 13, lineHeight: 1.5, margin: 0 }}>
        Paylaş ⬆︎ → <b>Ana Ekrana Ekle</b> dersen uygulama gibi açılır.
      </p>
      <button onClick={kapat} style={{ ...label, background: "none", border: "none",
        cursor: "pointer", color: C.muted, minHeight: 44 }}>Kapat</button>
    </div>
  );
}
