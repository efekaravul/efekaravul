-- =====================================================================
--  Kadro tohumu · 3425 IST-Nişantaşı · Kasa (20.08.2026 export'u)
--  01_sema.sql'den SONRA çalıştır. Tekrar çalıştırmak güvenlidir.
--  Şef kodu burada 3425 olarak kurulur; ilk girişten sonra uygulamadan
--  (Yönetici → Ayarlar) değiştir.
-- =====================================================================

insert into personel (id, ad, rol) values
  ('arda-eren-dil', 'Arda Eren Dil', 'calisan'),
  ('ayse-yilmaz', 'Ayşe Yılmaz', 'calisan'),
  ('berkant-polat', 'Berkant Polat', 'calisan'),
  ('betul-erdogan', 'Betül Erdoğan', 'calisan'),
  ('burcu-ozmen', 'Burcu Özmen', 'calisan'),
  ('dilara-sari', 'Dilara Sarı', 'calisan'),
  ('eda-serbes', 'Eda Serbes', 'calisan'),
  ('efe-aldemir', 'Efe Aldemir', 'calisan'),
  ('efe-karavul', 'Efe Karavul', 'calisan'),
  ('elif-aksu', 'Elif Aksu', 'calisan'),
  ('elif-pasaoglu', 'Elif Paşaoğlu', 'calisan'),
  ('elif-sahingoz', 'Elif Şahingöz', 'calisan'),
  ('ertugrul-ciftci', 'Ertuğrul Çiftçi', 'calisan'),
  ('esma-uygun', 'Esma Uygun', 'calisan'),
  ('kaan-mutlu', 'Kaan Mutlu', 'calisan'),
  ('merve-akcasari-tulunay', 'Merve Akçaşarı Tulunay', 'calisan'),
  ('misra-ezik', 'Mısra Ezik', 'calisan'),
  ('muhammed-yakupcan-tali', 'Muhammed Yakupcan Tali', 'calisan'),
  ('saliha-ebrar-erguven', 'Saliha Ebrar Ergüven', 'calisan'),
  ('sibel-tunc', 'Sibel Tunç', 'calisan'),
  ('utku-ali-aktas', 'Utku Ali Aktaş', 'calisan'),
  ('kasa-sefi', 'Kasa Şefi', 'yonetici')
on conflict (id) do update set ad = excluded.ad, rol = excluded.rol, aktif = true;

insert into ayar (anahtar, deger) values ('sef_kodu', crypt('3425', gen_salt('bf')))
on conflict (anahtar) do nothing;

-- Kadrodan biri işten ayrılırsa satırı silme, pasife al:
--   update personel set aktif = false where id = 'ornek-isim';
