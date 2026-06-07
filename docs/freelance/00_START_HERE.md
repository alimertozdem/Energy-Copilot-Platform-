# START HERE — Freelance Setup Roadmap

**Date:** 2026-05-26
**Goal:** EnergyLens'ten gerçek para çıkarmak için 1 study guide + 2 referans dokümanı + 1 bot var. Bu dosya akışı söyler.

---

## Klasördeki dosyalar

| Dosya | Ne işe yarar | Ne zaman okursun |
|---|---|---|
| **00_START_HERE.md** (bu dosya) | Yol haritası | Şimdi |
| **EnergyLens_Master_Study_Guide.pdf** | **Tek merkez çalışma dokümanı** — pozisyon + proje teknik referans + CSRD/Fabric vocabulary + discovery call + Q&A + glossary. 33 sayfa İngilizce, TR ipuçları parantez içinde | Bot kurulumundan önce baştan sona oku |
| **EnergyLens_Master_Study_Guide.md** | PDF'in markdown kaynağı — sadece düzenleme istersen | Genellikle açma |
| **04_profiles.md** | Malt + Contra + freelance.de + Toptal kopyala-yapıştır profile metinleri | Profil kurarken |
| **05_automation_architecture.md** | Bot mimari kararları — referans amaçlı | Sadece merak edersen |
| `_archive_individual_docs/` | Eski 01/02/03 ayrı dosyalar — artık master guide'a entegre, sadece arşiv için | Açma |

> **Bot README:** `scripts/freelance_bot/README.md` — bot kurulum talimatı. Tamamen ayrı bir konu, profil setup'tan bağımsız.

---

## Yeni sıralama

Mert'in karar verdiği akış şu:

### 1. ÖNCE — Master Study Guide'ı tam oku (~6-8 saat, birkaç güne yayılabilir)

PDF'i aç, baştan sona git. İçinde 7 Part var:

- **Part I — Why This Niche** (pozisyon, ICP'ler, paketler, fiyatlar, kazanan proposal'ın 5 parçası)
- **Part II — Master Your Own Project** (EnergyLens'in 9 sayfası, KPI formülleri, anomaly logic, battery dispatch, simulation, data model, varsayımlar)
- **Part III — Regulatory Vocabulary** (CSRD, ESRS E1, GHG Protocol, EU Taxonomy, EPC, ISO 50001, Almanya/Türkiye regülasyonları, teknik standartlar)
- **Part IV — Microsoft Analytics Sales Vocabulary** (Fabric elevator pitch, DP-600, Direct Lake, Embedded, Copilot, Real-Time Intelligence)
- **Part V — Discovery Call Framework** (30 dakikalık call yapısı, 6 diagnostic soru, "Position-and-Propose" tekniği)
- **Part VI — 7 Common Q&A** (ezberlenecek hazır cevaplar)
- **Part VII — Glossary A-Z** (80+ terim, toplantı sırasında referans)

> En kritik bölümler ezbere düzey: Part I §2 (positioning cümlesi), Part I §5 (paketler), Part II §11 (KPI formülleri), Part III §17-19 (CSRD/ESRS/GHG), Part IV §23 (Fabric pitch), Part V §30 (6 soru).

### 2. SONRA — Bot kurulumu (~20 dk)

`scripts/freelance_bot/README.md` → Quick Start adımları:
- Gemini API key (https://aistudio.google.com/apikey)
- Telegram bot (@BotFather)
- freelance.de RSS URL

### 3. SONRA — Profilleri kur (~10 saat dağıtık)

`04_profiles.md` → Section 1 (Malt) → Section 2 (Contra) → Section 3 (freelance.de) → Section 4 (Toptal application)

### 4. PARALEL — İlk teklifler

Profillerden ilki canlı olduğu anda bot Telegram'a düşürür, sen review et + submit.

---

## Çalışma rejimi önerisi

**Hızlı varyant (acelen varsa):**
- Day 1-2: Master Study Guide Part I + II + Part III §17-19 (CSRD/ESRS/GHG) — bu yeterli sviar minimum
- Day 3: Bot kurulumu + Malt profili
- Day 4-7: Master Study Guide Part III §20-22 + Part IV (Microsoft sales lang) + Part V (call framework)
- Day 5: Diğer profilleri kur (Contra, freelance.de, Toptal)
- Day 8 itibariyle bot çalışıyor, profiller yayında, teklif göndermeye başlıyorsun

**Sağlam varyant (acelen yoksa):**
- Week 1: Master Study Guide Part I + II + III tam okuma, günde 1.5 saat
- Week 1 sonu: Bot kur, Malt profili kur
- Week 2: Master Study Guide Part IV + V + VI okuma + diğer profiller
- Week 2 sonu: Toptal başvurusu yapt + ilk teklifler başla
- Week 3+: Bot çalışıyor, sen aktifsin, gerçek müşterilerle pratik

---

## Şu an ne yap?

**PDF'i aç.** [Master Study Guide PDF](computer://C:\Energy Management App\Energy-copilot-platform\docs\freelance\EnergyLens_Master_Study_Guide.pdf)

Part I'den başla, Part II'ye geç. Bu iki Part'ı bitirince zaten projeyi avucunun içi gibi bileceksin. Sonra Part III'ten devam et.

Bir bölüm okudukça takıldığın bir terim veya formül olursa söyle, daha derinleştirelim.
