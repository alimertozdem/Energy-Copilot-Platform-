# Paste this into a NEW conversation to start

Copy everything between the lines below into a brand-new chat.

---

Ben Mert. Berlin'de 1KOMMA5°'de **Internship Product Management — Energy Products & Tariffs** pozisyonu için görüşmeye gireceğim. Rol: dinamik elektrik tarifi ürünleri, Direktvermarktung gibi regülasyon kaynaklı ürün lansmanları, Alman Marktkommunikation süreçlerini iyileştirme, KPI takibi. İlan "Google Sheets a must, SQL or Python a plus" diyor.

Bu şirkette bir veri/tarif analisti + ürün yöneticisinin yaptığı işi **uçtan uca kendim yapmak** istiyorum. Amaç görüşmede kendime güvenmek.

## Kurallar — bunlara harfiyen uy

1. **Her satır kodu BEN yazacağım.** Bana hazır dosya, hazır script, hazır sorgu VERME. Ne yazacağımı söyle, ben yazayım, sonra çıktıyı sana göstereyim.
2. **Tek adım.** Bir mesajda tek bir iş ver. Ben yapıp çıktıyı yazana kadar sonraki adıma geçme.
3. **Uzun doküman üretme.** Okumaktan yoruldum. Her adımda 2-3 cümle "neden bunu yapıyoruz" yeter.
4. **Gerçek konsollarda çalışayım.** SQL'i DuckDB'nin kendi CLI'ında (`duckdb.exe`) yazacağım, Python'u kendi yazdığım `.py` dosyalarında.
5. **Bir şeyi neden öyle yaptığımızı söyle**, özellikle enerji sektörüne özgü olan kısımları (yaz saati, kW/kWh, MaLo-ID, denge grubu, spot fiyat yapısı).
6. Hata yaptığımda düzeltmeyi bana yaptır, sen düzeltme.

## Sıra — bu sırayla ilerleyelim

**Faz 1 — SQL (en uzun kısım).** Sıfırdan medallion pipeline yazacağım:
- bronze: kirli CSV'leri olduğu gibi yükle
- silver: 12 veri hatasını tek tek düzelt (her düzeltmeyi ayrı adımda yazacağım)
- gold: iş tabloları — müşteri kârlılığı, tedarikçi-değişim hunisi, DSO karnesi, veri kalitesi
- sonra 10 gerçek ürün sorusunu SQL ile cevaplayacağım

**Faz 2 — Python.** Tarif backtest'i sıfırdan yazacağım: sabit tarife vs dinamik tarife vs dinamik+batarya, gerçek fiziksel kısıtlarla.

**Faz 3 — Google Sheets.** Birim ekonomi modelini hücre hücre kuracağım, sonra veri işleme alıştırmaları (QUERY, pivot, XLOOKUP, ARRAYFORMULA, koşullu biçimlendirme).

## Ortam — hazır

- Windows, VS Code, terminal PowerShell 5.x (**`&&` çalışmıyor**, komutları satır başına bir ver)
- Python 3.14.4 kurulu; `pip` PATH'te yok → `python -m pip` kullanıyorum
- Kurulu paketler: duckdb, pandas, numpy, matplotlib, openpyxl
- DuckDB CLI kurulu (`duckdb.exe`)
- Çalışma klasörüm: `C:\Energy Management App\Energy-copilot-platform\docs\job-1komma5\sql-lab`
  - `data\` → 4 kirli CSV hazır (bunları ben üretmedim, ham malzeme)
  - `queries\` → SQL dosyalarımı buraya yazacağım
  - `python\` → Python dosyalarımı buraya yazacağım
  - `output\` → çıktılar

`data\` içindeki 4 dosya:
- `raw_day_ahead_prices.csv` — 2025 Alman gün-öncesi fiyatları, 15 dakikalık (35.100 satır)
- `raw_meter_readings.csv` — 30 müşterinin çeyrek saatlik sayaç okumaları, Şubat–Nisan 2025 (257.061 satır)
- `raw_customers.csv` — müşteri ana verisi, MaLo-ID'li (28 satır)
- `raw_mako_events.csv` — tedarikçi değişim süreci olayları (151 satır)

Veri **kasten kirli**. İçinde şu 12 gerçek sektör hatası var: kopya satırlar, eksik aralıklar, NULL değerler, Alman ondalık virgülü, karışık tarih formatları, yaz saati (30.03.2025'te 92 çeyrek saat var), kW yerine kWh raporlayan 3 müşteri, negatif tüketim (PV ihracı sızmış), Excel'in kırptığı MaLo-ID baştaki sıfırı, tutarsız şehir adları, ana veride olmayan 2 MaLo, ve hiç onaylanmamış/faturalanmamış geçişler.

`..\practice-project\` klasöründe bitmiş bir referans çözüm var. **Oraya bakmayacağım** ve sen de bana oradan kod kopyalamayacaksın — ancak ben açıkça istersem karşılaştırma için kullanırız.

Faz 1'in ilk adımıyla başla: DuckDB CLI'ı açıp veritabanını oluşturmak. Tek adım ver, bekle.

---
