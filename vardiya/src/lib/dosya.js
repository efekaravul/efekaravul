/* Ders programı yüklemesi: telefondan çekilen 4–5 MB'lık fotoğrafı
   sunucuya göndermeden önce tarayıcıda küçültür.                         */
const EN_BUYUK_KENAR = 1400;
const KALITE = 0.75;

export const dataUrlOku = (dosya) =>
  new Promise((coz, red) => {
    const r = new FileReader();
    r.onload = () => coz(r.result);
    r.onerror = () => red(new Error("Dosya okunamadı."));
    r.readAsDataURL(dosya);
  });

export async function hazirla(dosya) {
  const pdf = dosya.type === "application/pdf" ||
              dosya.name.toLowerCase().endsWith(".pdf");
  if (pdf) {
    const icerik = await dataUrlOku(dosya);
    if (icerik.length > 2100000) throw new Error("PDF çok büyük. Ekran görüntüsü olarak yükle.");
    return { ad: dosya.name, tur: "application/pdf", boyut: dosya.size, icerik };
  }

  const ham = await dataUrlOku(dosya);
  const gorsel = await new Promise((coz, red) => {
    const g = new Image();
    g.onload = () => coz(g);
    g.onerror = () => red(new Error("Görsel açılamadı."));
    g.src = ham;
  });

  const olcek = Math.min(1, EN_BUYUK_KENAR / Math.max(gorsel.width, gorsel.height));
  const tuval = document.createElement("canvas");
  tuval.width = Math.round(gorsel.width * olcek);
  tuval.height = Math.round(gorsel.height * olcek);
  const ctx = tuval.getContext("2d");
  ctx.fillStyle = "#FFFFFF";
  ctx.fillRect(0, 0, tuval.width, tuval.height);
  ctx.drawImage(gorsel, 0, 0, tuval.width, tuval.height);
  const icerik = tuval.toDataURL("image/jpeg", KALITE);

  return {
    ad: dosya.name.replace(/\.[^.]+$/, "") + ".jpg",
    tur: "image/jpeg",
    boyut: Math.round((icerik.length * 3) / 4),
    icerik,
  };
}

export function dataUrlBlobUrl(dataUrl) {
  const [meta, b64] = dataUrl.split(",");
  const mime = (meta.match(/:(.*?);/) || [])[1] || "application/octet-stream";
  const bin = atob(b64);
  const arr = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
  return URL.createObjectURL(new Blob([arr], { type: mime }));
}
