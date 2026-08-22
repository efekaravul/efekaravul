-- =====================================================================
--  VARDİYA · 3425 IST-Nişantaşı · Kasa
--  Supabase SQL Editor'e bu dosyayı olduğu gibi yapıştırıp çalıştır.
--  Tabloların tamamı RLS ile kapalıdır; istemci yalnızca aşağıdaki
--  SECURITY DEFINER fonksiyonlarını çağırabilir ve her çağrı bir
--  oturum token'ı ister. Yani anon anahtarı ele geçse bile kimsenin
--  izin nedeni veya ders programı okunamaz.
-- =====================================================================

create extension if not exists pgcrypto;

-- ------------------------------- tablolar ----------------------------
create table if not exists personel (
  id          text primary key,
  ad          text not null,
  rol         text not null default 'calisan' check (rol in ('calisan','yonetici')),
  aktif       boolean not null default true,
  olusma      timestamptz not null default now()
);

-- Mağaza geneli ayarlar; şu an yalnızca şef kodunun bcrypt özeti.
create table if not exists ayar (
  anahtar text primary key,
  deger   text not null
);

create table if not exists oturum (
  token        uuid primary key default gen_random_uuid(),
  personel_id  text not null references personel(id) on delete cascade,
  olusma       timestamptz not null default now(),
  son_kullanma timestamptz not null default now() + interval '60 days'
);
create index if not exists oturum_personel_ix on oturum(personel_id);

-- Bir çalışanın bir aya ait tüm talebi tek satırda:
--   veri = { "gunler": { "2026-09-05": {...} }, "hafta": { "1": {...} } }
create table if not exists talep (
  personel_id text not null references personel(id) on delete cascade,
  ay          text not null,                    -- 'YYYY-MM'
  veri        jsonb not null default '{}'::jsonb,
  gonderim    timestamptz,
  guncelleme  timestamptz not null default now(),
  primary key (personel_id, ay)
);

-- Şefin gün bazlı kararı (izin onayı / reddi)
create table if not exists karar (
  personel_id text not null references personel(id) on delete cascade,
  gun         date not null,
  durum       text not null check (durum in ('onay','ret')),
  not_metni   text not null default '',
  veren       text references personel(id),
  tarih       timestamptz not null default now(),
  primary key (personel_id, gun)
);

-- Ders programı: küçültülmüş görsel/PDF, base64 olarak
create table if not exists program (
  personel_id text primary key references personel(id) on delete cascade,
  ad          text not null,
  tur         text not null default '',
  boyut       integer not null default 0,
  icerik      text not null,
  tarih       timestamptz not null default now()
);

-- Şefin yazdığı vardiya planı
create table if not exists plan (
  gun         date not null,
  personel_id text not null references personel(id) on delete cascade,
  vardiya     text not null,                    -- VARDIYALAR[].id
  primary key (gun, personel_id)
);

create table if not exists plan_yayin (
  ay     text primary key,
  tarih  timestamptz not null default now(),
  veren  text references personel(id)
);

alter table personel   enable row level security;
alter table ayar       enable row level security;
alter table oturum     enable row level security;
alter table talep      enable row level security;
alter table karar      enable row level security;
alter table program    enable row level security;
alter table plan       enable row level security;
alter table plan_yayin enable row level security;
-- Politika tanımlanmadı: doğrudan tablo erişimi herkese kapalı.

-- ------------------------------ yardımcılar --------------------------
create or replace function _oturum(p_token text)
returns personel language plpgsql security definer set search_path = public as $$
declare k personel;
begin
  select p.* into k
    from oturum o join personel p on p.id = o.personel_id
   where o.token = p_token::uuid and o.son_kullanma > now() and p.aktif;
  if not found then
    raise exception 'oturum-gecersiz' using errcode = '28000';
  end if;
  return k;
end $$;

create or replace function _sef(p_token text)
returns personel language plpgsql security definer set search_path = public as $$
declare k personel;
begin
  k := _oturum(p_token);
  if k.rol <> 'yonetici' then
    raise exception 'yetki-yok' using errcode = '42501';
  end if;
  return k;
end $$;

-- -------------------------------- giriş ------------------------------
-- Çalışan girişi kişisel şifre istemez: listeden ismine dokunur.
-- Dönen token yalnızca o kişinin kendi verisini açar.
create or replace function giris(p_id text)
returns jsonb language plpgsql security definer set search_path = public as $$
declare k personel; t uuid;
begin
  select * into k from personel where id = p_id and aktif and rol = 'calisan';
  if not found then
    raise exception 'kisi-yok' using errcode = '28000';
  end if;
  delete from oturum where son_kullanma < now();
  insert into oturum(personel_id) values (k.id) returning token into t;
  return jsonb_build_object('token', t, 'id', k.id, 'ad', k.ad, 'rol', k.rol);
end $$;

-- Şef/müdür girişi tek bir mağaza kodu ister (izin nedenleri ve ders
-- programları yalnızca bu girişte görünür).
create or replace function sef_giris(p_kod text)
returns jsonb language plpgsql security definer set search_path = public as $$
declare k personel; h text; t uuid;
begin
  select deger into h from ayar where anahtar = 'sef_kodu';
  if h is null or h <> crypt(p_kod, h) then
    raise exception 'kod-hatali' using errcode = '28P01';
  end if;
  select * into k from personel where rol = 'yonetici' and aktif limit 1;
  if not found then
    raise exception 'yonetici-yok' using errcode = '28000';
  end if;
  delete from oturum where son_kullanma < now();
  insert into oturum(personel_id) values (k.id) returning token into t;
  return jsonb_build_object('token', t, 'id', k.id, 'ad', k.ad, 'rol', k.rol);
end $$;

create or replace function cikis(p_token text)
returns void language sql security definer set search_path = public as $$
  delete from oturum where token = p_token::uuid;
$$;

create or replace function sef_kodu_degistir(p_token text, p_yeni text)
returns void language plpgsql security definer set search_path = public as $$
begin
  perform _sef(p_token);
  if p_yeni !~ '^[0-9]{4,8}$' then
    raise exception 'kod-bicimi' using errcode = '22023';
  end if;
  insert into ayar(anahtar, deger) values ('sef_kodu', crypt(p_yeni, gen_salt('bf')))
  on conflict (anahtar) do update set deger = excluded.deger;
end $$;

-- --------------------------- çalışan tarafı --------------------------
create or replace function kadro()
returns jsonb language sql security definer set search_path = public stable as $$
  select coalesce(jsonb_agg(jsonb_build_object('id', id, 'ad', ad, 'rol', rol)
                            order by ad), '[]'::jsonb)
    from personel where aktif;
$$;

create or replace function kendi_ayim(p_token text, p_ay text)
returns jsonb language plpgsql security definer set search_path = public as $$
declare k personel; sonuc jsonb;
begin
  k := _oturum(p_token);
  select jsonb_build_object(
    'kisi',    jsonb_build_object('id', k.id, 'ad', k.ad, 'rol', k.rol),
    'talep',   coalesce((select jsonb_build_object('veri', t.veri, 'gonderim', t.gonderim)
                           from talep t where t.personel_id = k.id and t.ay = p_ay), 'null'::jsonb),
    'program', coalesce((select jsonb_build_object('ad', g.ad, 'tur', g.tur,
                                                   'boyut', g.boyut, 'tarih', g.tarih)
                           from program g where g.personel_id = k.id), 'null'::jsonb),
    'kararlar',coalesce((select jsonb_object_agg(x.gun::text,
                                 jsonb_build_object('durum', x.durum, 'not', x.not_metni))
                           from karar x where x.personel_id = k.id
                            and to_char(x.gun,'YYYY-MM') = p_ay), '{}'::jsonb),
    'plan',    case when exists (select 1 from plan_yayin y where y.ay = p_ay)
                    then coalesce((select jsonb_object_agg(pl.gun::text, pl.vardiya)
                                     from plan pl where pl.personel_id = k.id
                                      and to_char(pl.gun,'YYYY-MM') = p_ay), '{}'::jsonb)
                    else 'null'::jsonb end
  ) into sonuc;
  return sonuc;
end $$;

create or replace function talep_kaydet(p_token text, p_ay text, p_veri jsonb, p_gonder boolean)
returns jsonb language plpgsql security definer set search_path = public as $$
declare k personel; g timestamptz;
begin
  k := _oturum(p_token);
  g := case when p_gonder then now() else null end;
  insert into talep(personel_id, ay, veri, gonderim, guncelleme)
       values (k.id, p_ay, p_veri, g, now())
  on conflict (personel_id, ay) do update
    set veri = excluded.veri, gonderim = excluded.gonderim, guncelleme = now();
  return jsonb_build_object('gonderim', g);
end $$;

create or replace function program_yukle(p_token text, p_ad text, p_tur text,
                                         p_boyut integer, p_icerik text)
returns void language plpgsql security definer set search_path = public as $$
declare k personel;
begin
  k := _oturum(p_token);
  if length(p_icerik) > 2200000 then
    raise exception 'dosya-buyuk' using errcode = '22001';
  end if;
  insert into program(personel_id, ad, tur, boyut, icerik, tarih)
       values (k.id, p_ad, p_tur, p_boyut, p_icerik, now())
  on conflict (personel_id) do update
    set ad = excluded.ad, tur = excluded.tur, boyut = excluded.boyut,
        icerik = excluded.icerik, tarih = now();
end $$;

create or replace function program_sil(p_token text)
returns void language plpgsql security definer set search_path = public as $$
declare k personel;
begin
  k := _oturum(p_token);
  delete from program where personel_id = k.id;
end $$;

-- Dosyanın kendisi: sahibi ya da şef açabilir.
create or replace function program_ac(p_token text, p_personel text)
returns jsonb language plpgsql security definer set search_path = public as $$
declare k personel; hedef text;
begin
  k := _oturum(p_token);
  hedef := coalesce(p_personel, k.id);
  if hedef <> k.id and k.rol <> 'yonetici' then
    raise exception 'yetki-yok' using errcode = '42501';
  end if;
  return coalesce((select jsonb_build_object('ad', ad, 'tur', tur, 'icerik', icerik)
                     from program where personel_id = hedef), 'null'::jsonb);
end $$;

-- --------------------------- yönetici tarafı -------------------------
create or replace function sef_ayi(p_token text, p_ay text)
returns jsonb language plpgsql security definer set search_path = public as $$
declare sonuc jsonb;
begin
  perform _sef(p_token);
  select jsonb_build_object(
    'kadro', (select coalesce(jsonb_agg(jsonb_build_object('id', id, 'ad', ad, 'rol', rol)
                              order by ad), '[]'::jsonb) from personel where aktif),
    'talepler', (select coalesce(jsonb_object_agg(t.personel_id,
                          jsonb_build_object('veri', t.veri, 'gonderim', t.gonderim)), '{}'::jsonb)
                   from talep t where t.ay = p_ay),
    'programlar', (select coalesce(jsonb_object_agg(g.personel_id,
                          jsonb_build_object('ad', g.ad, 'tur', g.tur,
                                             'boyut', g.boyut, 'tarih', g.tarih)), '{}'::jsonb)
                     from program g),
    'kararlar', (select coalesce(jsonb_object_agg(x.personel_id || '|' || x.gun::text,
                          jsonb_build_object('durum', x.durum, 'not', x.not_metni)), '{}'::jsonb)
                   from karar x where to_char(x.gun,'YYYY-MM') = p_ay),
    'plan', (select coalesce(jsonb_object_agg(pl.gun::text || '|' || pl.personel_id, pl.vardiya),
                    '{}'::jsonb)
               from plan pl where to_char(pl.gun,'YYYY-MM') = p_ay),
    'yayin', coalesce((select to_jsonb(y.tarih) from plan_yayin y where y.ay = p_ay), 'null'::jsonb)
  ) into sonuc;
  return sonuc;
end $$;

create or replace function karar_ver(p_token text, p_personel text, p_gun date,
                                     p_durum text, p_not text)
returns void language plpgsql security definer set search_path = public as $$
declare k personel;
begin
  k := _sef(p_token);
  if p_durum is null then
    delete from karar where personel_id = p_personel and gun = p_gun;
  else
    insert into karar(personel_id, gun, durum, not_metni, veren, tarih)
         values (p_personel, p_gun, p_durum, coalesce(p_not,''), k.id, now())
    on conflict (personel_id, gun) do update
      set durum = excluded.durum, not_metni = excluded.not_metni,
          veren = excluded.veren, tarih = now();
  end if;
end $$;

-- p_atamalar: { "2026-09-05|efe-karavul": "K2", "2026-09-06|efe-karavul": null, ... }
create or replace function plan_kaydet(p_token text, p_atamalar jsonb)
returns void language plpgsql security definer set search_path = public as $$
declare anahtar text; deger text; g date; kim text;
begin
  perform _sef(p_token);
  for anahtar, deger in select * from jsonb_each_text(p_atamalar) loop
    g   := split_part(anahtar, '|', 1)::date;
    kim := split_part(anahtar, '|', 2);
    if deger is null or deger = '' then
      delete from plan where gun = g and personel_id = kim;
    else
      insert into plan(gun, personel_id, vardiya) values (g, kim, deger)
      on conflict (gun, personel_id) do update set vardiya = excluded.vardiya;
    end if;
  end loop;
end $$;

create or replace function plan_yayinla(p_token text, p_ay text, p_yayinda boolean)
returns void language plpgsql security definer set search_path = public as $$
declare k personel;
begin
  k := _sef(p_token);
  if p_yayinda then
    insert into plan_yayin(ay, tarih, veren) values (p_ay, now(), k.id)
    on conflict (ay) do update set tarih = now(), veren = k.id;
  else
    delete from plan_yayin where ay = p_ay;
  end if;
end $$;

-- ------------------------------- yetkiler ----------------------------
revoke all on all tables in schema public from anon, authenticated;
revoke all on all functions in schema public from anon, authenticated;

grant execute on function giris(text)                                  to anon;
grant execute on function sef_giris(text)                              to anon;
grant execute on function cikis(text)                                  to anon;
grant execute on function sef_kodu_degistir(text,text)                 to anon;
grant execute on function kadro()                                      to anon;
grant execute on function kendi_ayim(text,text)                        to anon;
grant execute on function talep_kaydet(text,text,jsonb,boolean)        to anon;
grant execute on function program_yukle(text,text,text,integer,text)   to anon;
grant execute on function program_sil(text)                            to anon;
grant execute on function program_ac(text,text)                        to anon;
grant execute on function sef_ayi(text,text)                           to anon;
grant execute on function karar_ver(text,text,date,text,text)          to anon;
grant execute on function plan_kaydet(text,jsonb)                      to anon;
grant execute on function plan_yayinla(text,text,boolean)              to anon;
