# Day 17 — Yeni Konuşma Başlangıç Promptu

**Yeni konuşma açtığında BU METNİ kopyala-yapıştır:**

---

Selam, EnergyLens platformu — Day 17'ye başlıyoruz.

Önce memory'yi oku — özellikle bunları:
- spaces/.../memory/MEMORY.md (tam liste)
- day_16_completion.md (DÜN tamamlandı, /copilot canlı, ~3900 satır 22 dosya)
- day_15_completion.md (/portfolio canlı, 3 paralel Fabric veri yolu)
- application_pivot_2026_05_29.md (DÜN: Microsoft Startups submit edilemedi, EXIST/Avrupa programlarına pivot)
- frontend_architecture.md (V1 mimari kararları, 70 Day toplam plan)
- founder_profile.md
- feedback_language.md (Web App UI tamamen İngilizce)
- feedback_pbi_embed.md
- feedback_fabric_notebooks.md

ÖNEMLİ DURUM ÖZETİ (2026-05-29 sonu):

**Day 16 tamamlandı (önceki gün):**
- /copilot canlı: LLMProvider + 6 tool + SSE + chat UI + Mock provider
- Anthropic credit=0, Mock devrede. Credit gelince LLM_PROVIDER=anthropic flip
- Day 16 V1.5 backlog mevcut: title auto-generate, markdown rendering, building context selector, conversation rename, schema doğrulama
- 3 paralel Fabric veri yolu canlı (DirectLake embed + SQL Analytics Endpoint + LLM tool use)

**Pivot kararı (dün, 2026-05-29):**
- Microsoft Startups 2026 yeni yapısı sadece $1K otomatik + $5K verification → Tier 2 manual app kalkmış
- Mert "prior Azure customer" → $1K otomatik bile gelmedi
- Pivot: EXIST Gründerstipendium (€65K paket, %60-75 kabul) + Avrupa programları + BSBI pilot
- Strateji: ÖNCE V1 production-ready bitir (Day 17-70 ~6 hafta), SONRA EXIST submit (Ağustos hedef)
- Detay: docs/startups-application/ klasöründe EXIST_BASVURU_PLANI.md + AVRUPA_FONLAMA_ASAMALI_PLAN.md + BSBI_PILOT_MAILS.md

**Paralel iş (Mert tarafı):**
- Hocaya (Dr. Kaddour Chelabi) mentor mail gönderdi (veya gönderecek)
- BSBI Transfer Office discover mail gönderdi (veya gönderecek)
- Bu süreçler 1-4 hafta sürer, V1 web app polish ile paralel ilerleyecek

KARARLAR (memory'de detay):
- UI dili İngilizce
- Türkçe konuş
- DOSYA DEĞİŞİKLİĞİ ONAY OLMADAN YAPMA
- Plan + onay + parça parça pattern
- BMAD methodology

İLK İŞ — Day 17 ne olacak karar:
1. Memory'yi oku (yukarıdaki referansları)
2. Day 17 için 5 aday değerlendir:
   - A) `/actions` sayfası — Page 5 recommendation tracking. Backend `update_action_status` tool zaten var (Day 16'da), front-end eksik
   - B) `/onboarding` wizard — yeni müşteri akışı, building inventory
   - C) Page 8 IoT dashboard polish — capacity sonrası bug fix (sensor uptime renk hatası vs)
   - D) Copilot V1.5 — markdown rendering, title auto-generate, building context selector
   - E) `/demo` public sayfa — kayıtsız erişim, 6 sample bina, marketing değeri
3. Bana sun — hangisi önce mantıklı, neden, kaç parça olur
4. Onay alınca parça parça uygula

HEDEF: Day 17 sonu V1.5 production-ready'ye 1 adım daha. Toplam 54 Day kaldı (16/70). Hız ortalaması 1.3 Day/gün, devamla ~6 hafta'da V1 production.

---

**Not — Yukarıdaki promptu kopyala, yeni konuşmada başla. Mevcut konuşmada Day 17 başlatma, çünkü konuşma uzadı, context kayar.**
