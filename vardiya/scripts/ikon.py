"""Ana ekran ikonlarını üretir: siyah zemin, beyaz 'V'.
   Çalıştır:  python3 scripts/ikon.py"""
from PIL import Image, ImageDraw

SIYAH, BEYAZ = (10, 10, 10), (255, 255, 255)

def v_ciz(boyut, dolgu=0.62):
    g = Image.new("RGB", (boyut, boyut), SIYAH)
    d = ImageDraw.Draw(g)
    o = boyut / 2
    y = boyut * dolgu          # harfin yüksekliği
    x = y * 0.78               # genişliği
    kalinlik = y * 0.22
    ust, alt = o - y / 2, o + y / 2
    sol, sag = o - x / 2, o + x / 2
    d.polygon([(sol, ust), (sol + kalinlik, ust), (o, alt - kalinlik * 0.55),
               (sag - kalinlik, ust), (sag, ust), (o + kalinlik * 0.30, alt),
               (o - kalinlik * 0.30, alt)], fill=BEYAZ)
    return g

for ad, boyut, dolgu in [
    ("public/ikon-192.png", 192, 0.62),
    ("public/ikon-512.png", 512, 0.62),
    ("public/ikon-maskable-512.png", 512, 0.44),   # maskeleme için dar tut
    ("public/apple-touch-icon.png", 180, 0.62),
]:
    v_ciz_ = v_ciz(boyut * 4, dolgu).resize((boyut, boyut), Image.LANCZOS)
    v_ciz_.save(ad)
    print(ad)
