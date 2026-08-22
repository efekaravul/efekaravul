"""Mola odasına asılacak QR afişi üretir.

    pip install segno
    python3 scripts/qr.py https://efekaravul.github.io/ > vardiya-afis.svg

Telefonun kamerasıyla okutan herkes uygulamayı açar; oradan
"Ana Ekrana Ekle" ile ikon olarak kalır.
"""
import sys

try:
    import segno
except ImportError:
    sys.exit("Önce: pip install segno")

if len(sys.argv) < 2:
    sys.exit("Kullanım: python3 scripts/qr.py <uygulama-adresi>")

adres = sys.argv[1]
qr = segno.make(adres, error="h")
kod = qr.svg_inline(scale=10, dark="#0A0A0A", border=2)

print(f'''<svg xmlns="http://www.w3.org/2000/svg" width="595" height="842" viewBox="0 0 595 842">
  <rect width="595" height="842" fill="#FFFFFF"/>
  <text x="48" y="96" font-family="Times New Roman, serif" font-size="54" font-weight="700"
        letter-spacing="-2" fill="#0A0A0A">VARDİYA</text>
  <text x="48" y="126" font-family="Helvetica, Arial, sans-serif" font-size="12"
        letter-spacing="2.4" fill="#8A8783">3425 IST-NİŞANTAŞI · KASA</text>
  <line x1="48" y1="150" x2="547" y2="150" stroke="#E6E4E1"/>
  <g transform="translate(148, 200)">{kod}</g>
  <text x="48" y="640" font-family="Helvetica, Arial, sans-serif" font-size="18" fill="#0A0A0A">
    1 · Kamerayı QR'a tut, çıkan linke dokun.
  </text>
  <text x="48" y="676" font-family="Helvetica, Arial, sans-serif" font-size="18" fill="#0A0A0A">
    2 · Listeden ismini seç.
  </text>
  <text x="48" y="712" font-family="Helvetica, Arial, sans-serif" font-size="18" fill="#0A0A0A">
    3 · Paylaş ⬆ → "Ana Ekrana Ekle" de; ikon olarak kalsın.
  </text>
  <line x1="48" y1="754" x2="547" y2="754" stroke="#E6E4E1"/>
  <text x="48" y="784" font-family="Helvetica, Arial, sans-serif" font-size="12"
        letter-spacing="2" fill="#8A8783">İZİN NEDENLERİNİ YALNIZCA ŞEF GÖRÜR</text>
  <text x="48" y="806" font-family="Helvetica, Arial, sans-serif" font-size="11"
        fill="#8A8783">{adres}</text>
</svg>''')
