import React, { useCallback, useEffect, useMemo, useState } from "react";
import { C, label } from "./tokens.js";
import { MAGAZA_ADI } from "./config.js";
import { VARSAYILAN_KADRO } from "./data/sabitler.js";
import { api, DEMO, oturumOku, oturumYaz } from "./lib/api.js";
import { ayGunleri, ayKey } from "./lib/tarih.js";
import { Baslik, AyBar, Yukleniyor, HataKutusu, EkleIpucu } from "./parcalar/ortak.jsx";
import Giris from "./ekranlar/Giris.jsx";
import Calisan from "./ekranlar/Calisan.jsx";
import Yonetici from "./ekranlar/Yonetici.jsx";

export default function App() {
  const bugun = new Date();
  /* Talepler bir sonraki ay için toplanır; şef geriye de gidebilir. */
  const [ay, setAy] = useState(() => {
    const d = new Date(bugun.getFullYear(), bugun.getMonth() + 1, 1);
    return { y: d.getFullYear(), m: d.getMonth() };
  });
  const days = useMemo(() => ayGunleri(ay.y, ay.m), [ay]);
  const anahtar = ayKey(ay.y, ay.m);

  const [oturum, setOturum] = useState(() => oturumOku());
  const [kadro, setKadro] = useState(VARSAYILAN_KADRO);
  const [paket, setPaket] = useState(null);
  const [hata, setHata] = useState("");
  const [yukleniyor, setYukleniyor] = useState(false);

  useEffect(() => {
    let iptal = false;
    api.kadro()
      .then((k) => { if (!iptal && Array.isArray(k) && k.length) setKadro(k); })
      .catch(() => { /* sunucuya ulaşılamazsa yerleşik kadro kalır */ });
    return () => { iptal = true; };
  }, []);

  const yukle = useCallback(async () => {
    if (!oturum) return;
    setYukleniyor(true); setHata("");
    try {
      const d = oturum.rol === "yonetici"
        ? await api.sefAyi(oturum.token, anahtar)
        : await api.kendiAyim(oturum.token, anahtar);
      setPaket(d);
    } catch (e) {
      if (e.kod === "oturum-gecersiz") { oturumYaz(null); setOturum(null); }
      else setHata(e.message || "Veriler alınamadı.");
    } finally { setYukleniyor(false); }
  }, [oturum, anahtar]);

  useEffect(() => { setPaket(null); yukle(); }, [yukle]);

  const girisTamam = (o) => { oturumYaz(o); setOturum(o); };
  const cikis = async () => {
    try { await api.cikis(oturum.token); } catch { /* yine de çık */ }
    oturumYaz(null); setOturum(null); setPaket(null);
  };

  if (!oturum) {
    return (
      <Giris kadro={kadro} demo={DEMO}
        girisYap={async (id) => girisTamam(await api.giris(id))}
        sefGirisi={async (kod) => girisTamam(await api.sefGiris(kod))} />
    );
  }

  const govde = () => {
    if (hata) return <HataKutusu hata={hata} tekrar={yukle} />;
    if (!paket || yukleniyor) return <Yukleniyor />;
    if (oturum.rol === "yonetici") {
      return (
        <Yonetici token={oturum.token} days={days} paket={paket}
          kararVer={(pid, gun, durum, not) => api.kararVer(oturum.token, pid, gun, durum, not)}
          sefKoduDegistir={(yeni) => api.sefKoduDegistir(oturum.token, yeni)} />
      );
    }
    return (
      <Calisan token={oturum.token} ay={anahtar} days={days} paket={paket}
        kaydet={(veri, gonder) => api.talepKaydet(oturum.token, anahtar, veri, gonder)}
        programYukle={async (d) => { await api.programYukle(oturum.token, d); await yukle(); }}
        programSil={async () => { await api.programSil(oturum.token); await yukle(); }} />
    );
  };

  return (
    <div style={{ background: C.paper, color: C.ink, minHeight: "100vh" }}>
      <Baslik ad={oturum.ad} alt={oturum.rol === "yonetici" ? "yönetici" : null} cikis={cikis} />
      <EkleIpucu />
      <div className="orta">
        <AyBar ay={ay} setAy={setAy} />
        {govde()}
      </div>
      <footer style={{ borderTop: `1px solid ${C.rule}`, marginTop: 40,
        padding: "24px 20px calc(32px + env(safe-area-inset-bottom))" }}>
        <p style={{ ...label, lineHeight: 1.9 }}>
          {MAGAZA_ADI}{DEMO ? " · demo modu" : ""}<br />
          İzin nedenleri ve ders programları yalnızca yönetici girişinde görünür
        </p>
      </footer>
    </div>
  );
}
