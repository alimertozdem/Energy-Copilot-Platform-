# Row Level Security (RLS) Tanımı
## Energy Copilot Platform

---

## Genel Mantık

Her müşteri sadece kendi binalarını görür. Hangi kullanıcının hangi binaları görebileceği
`customer_building_map` tablosundan yönetilir. Bu tablo Lakehouse'a eklenirse
her bina eklendiğinde/çıkarıldığında sadece bu tabloyu güncellemek yeterlidir.

---

## Adım 1 — customer_building_map Tablosu

Lakehouse'ta `silver_customer_building_map` adında bir Delta tablo oluştur.
Yeni bir CSV'den yükleyebilirsin (Files/sample-data/ klasörüne at, reference loader çalıştır).

### Tablo şeması:
| Kolon | Tip | Örnek |
|-------|-----|-------|
| user_email | Text (PK bileşen) | kunde@firma.de |
| building_id | Text (PK bileşen) | BLD_001 |
| customer_name | Text | Müller GmbH |
| access_level | Text | read_only / admin |

### Örnek veri (CSV):
```
user_email,building_id,customer_name,access_level
manager@muellerGmbH.de,BLD_001,Müller GmbH,admin
manager@muellerGmbH.de,BLD_002,Müller GmbH,admin
viewer@muellerGmbH.de,BLD_001,Müller GmbH,read_only
admin@energycopilot.com,BLD_001,Internal,admin
admin@energycopilot.com,BLD_002,Internal,admin
admin@energycopilot.com,BLD_003,Internal,admin
```

Bu tabloyu semantic model'e de ekle (silver_building_master gibi — ama sadece RLS için kullanılır, raporlarda görünmez).

---

## Adım 2 — RLS Rolleri Tanımla

Fabric semantic model editöründe: **Manage roles** → **Create role**

### Rol 1: `Customer`
Bu rol müşterilere verilir. Sadece kendi binalarını görürler.

**Filter table:** `silver_building_master`
**DAX Filter:**
```dax
[building_id] IN
    CALCULATETABLE(
        VALUES(silver_customer_building_map[building_id]),
        silver_customer_building_map[user_email] = USERPRINCIPALNAME()
    )
```

> `USERPRINCIPALNAME()` → Power BI'a login olan kullanıcının e-posta adresi.
> Filtre otomatik tüm fact tablolara yayılır çünkü hepsi silver_building_master'a bağlı.

### Rol 2: `InternalAdmin`
Şirket içi kullanıcılar — tüm binaları görür, filtre yok.

**Filter table:** `silver_building_master`
**DAX Filter:**
```dax
TRUE()
```

> TRUE() = filtre yok, her şeyi görür.

---

## Adım 3 — Rolleri Test Et

Model editöründe **View as role** → `Customer` seç → test kullanıcısı olarak bir e-posta gir.
Sadece o kullanıcının mapping tablosundaki binalar görünmeli.

---

## Adım 4 — Rolleri Fabric'te Atamalar

Semantic model publish edildikten sonra Fabric'te:
1. Semantic model'e sağ tıkla → **Security**
2. `Customer` rolüne müşteri kullanıcılarını veya gruplarını ekle
3. `InternalAdmin` rolüne şirket içi ekibi ekle

> **Önemli:** Rolleri atamadan önce kullanıcıların Fabric workspace'e "Viewer" olarak eklenmesi gerekir.

---

## Notlar

- RLS semantic model katmanında çalışır — Delta Lake'i etkilemez.
- Bir kullanıcı birden fazla role atanabilir (en geniş izin geçerli olur).
- `admin@energycopilot.com` gibi internal hesaplar mapping tablosuna ALL binalarla eklenebilir.
- Yeni bina eklendiğinde: sadece `silver_customer_building_map`'e yeni satır ekle → pipeline çalıştır → otomatik görünür.
