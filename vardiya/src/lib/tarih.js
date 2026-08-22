/* ============================ tarih yardımcıları =========================== */
export const iso = (d) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;

export const ayKey = (y, m) => `${y}-${String(m + 1).padStart(2, "0")}`;

export const ayGunleri = (y, m) =>
  Array.from({ length: new Date(y, m + 1, 0).getDate() }, (_, i) => new Date(y, m, i + 1));

export const tarihten = (gunKey) => new Date(`${gunKey}T00:00:00`);

/** "14:30" → 870 */
export const dk = (s) => {
  if (!s) return null;
  const [h, m] = String(s).split(":");
  return Number(h) * 60 + Number(m || 0);
};

/** 870 → "14:30" */
export const saat = (m) =>
  `${String(Math.floor(m / 60)).padStart(2, "0")}:${String(m % 60).padStart(2, "0")}`;

/** 510 → "8,5s" — Türkçe ondalık ayracı, sıfır kuyruğu yok */
export const sure = (m) => {
  if (!m) return "0s";
  const s = m / 60;
  return `${(Math.round(s * 10) / 10).toString().replace(".", ",")}s`;
};

/** ISO hafta anahtarı: "2026-W36" */
export const haftaKey = (d) => {
  const t = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
  t.setUTCDate(t.getUTCDate() + 4 - (t.getUTCDay() || 7));
  const yilBasi = new Date(Date.UTC(t.getUTCFullYear(), 0, 1));
  const no = Math.ceil(((t - yilBasi) / 86400000 + 1) / 7);
  return `${t.getUTCFullYear()}-W${String(no).padStart(2, "0")}`;
};

export const haftaSonu = (d) => d.getDay() === 0 || d.getDay() === 6;
