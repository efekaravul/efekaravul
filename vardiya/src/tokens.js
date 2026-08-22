/* Görsel dil: gazete dizgisi — siyah/beyaz, ince çizgi, tek vurgu rengi. */
export const C = {
  ink: "#0A0A0A",
  paper: "#FFFFFF",
  rule: "#E6E4E1",
  wash: "#F5F4F2",
  muted: "#8A8783",
  alarm: "#C8102E",
  ok: "#1F6F43",
};

export const SERIF = "'Times New Roman', Times, Georgia, serif";
export const SANS =
  "-apple-system, BlinkMacSystemFont, 'Helvetica Neue', Helvetica, Arial, sans-serif";

export const label = {
  fontFamily: SANS,
  fontSize: 10,
  letterSpacing: "0.18em",
  textTransform: "uppercase",
  color: C.muted,
};

export const num = { fontFamily: SANS, fontVariantNumeric: "tabular-nums" };

/* Satır altı bilgi: küçük, sessiz, ama BÜYÜK HARFE çevrilmez. */
export const meta = { fontFamily: SANS, fontSize: 11.5, color: C.muted };
