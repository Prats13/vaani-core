# VAANI — The Farmer Buddy

> **Voice-first AI agricultural advisory system for rural Indian farmers**
> Built for the **AWS AI for Bharat Hackathon**

---

## What is VAANI?

VAANI answers the one question every rural farmer asks every day:

> **"Mujhe ab kya karna chahiye?"** *(What should I do now?)*

India's 146 million farming households have access to weather data, mandi prices, and government scheme portals — but the data is fragmented, technical, and inaccessible to farmers with low digital literacy. VAANI bridges this gap by converting that fragmented public data into simple, explainable, voice-delivered decisions in the farmer's own language.

**VAANI is not a data dashboard. It is a digital farmer buddy.**

---

## The Problem

| Challenge | Impact |
|---|---|
| Fragmented weather + mandi + soil data | Farmers make decisions blind |
| Low digital literacy | Apps and portals go unused |
| Language barriers | Hindi/regional languages not supported by most tools |
| No decision support — only raw data | Farmers get numbers, not answers |
| Limited government scheme awareness | Eligible farmers miss out on benefits |

---

## How It Works

A farmer sends a voice note on WhatsApp in Hindi or their local language. VAANI responds with a spoken advisory in under 15 seconds.

```
Farmer Voice Query (WhatsApp / Phone IVR)
         ↓
   Speech-to-Text  (Sarvam AI — saaras model)
         ↓
   Intent Classification  → domain + intent + entity extraction
         ↓
   Context Gathering  → one clarifying question at a time
         ↓
   Data Fetch  → Weather (IMD) + Soil (SoilGrids) + Market (eNAM)
         ↓
   Deterministic Rules  → threshold logic BEFORE the LLM
         ↓
   AI Reasoning  → Claude API synthesises context into advice
         ↓
   Guardrails  → no yield guarantees, no exact dosage, always advisory
         ↓
   Text-to-Speech  (Sarvam AI — bulbul model)
         ↓
Farmer receives voice response (WhatsApp / Phone)
```

### Example — Irrigation Decision

```
Farmer:   "Kya main aaj tamatar ko paani doon?"

VAANI:    "Main suggest karunga ki aaj paani na den. Do karan hain:
           1. Mitti mein nami kaafi hai (65%)
           2. Kal se barish aane ki sambhavna hai (70%)

           Agar 2 din baad barish nahi hui, to check kar sakte hain."
```

---

## Three Pillars

### Pillar 1 — Communication
| Channel | Use Case |
|---|---|
| WhatsApp Voice Notes | Primary interaction channel |
| WhatsApp Interactive Buttons | Quick access to mandi prices, weather, crop advice, schemes |
| Phone IVR | Feature phone users without WhatsApp |
| SMS | Notification fallback |

### Pillar 2 — Core Decision Engine (6 Layers)
| Layer | Function |
|---|---|
| Intent Classification | Identifies domain (farming / market / scheme) and extracts entities |
| Context Manager | Fills missing information one question at a time |
| Data Integration | Fetches weather, soil, and market data from public APIs |
| Deterministic Logic | Applies threshold-based rules **before** LLM — prevents hallucinations |
| AI Reasoning | Claude API generates explainable, conversational recommendations |
| Guardrails | Safety filters — no guaranteed yields, no exact dosage, always advisory |

### Pillar 3 — Engagement & Retention
- Daily personalised alerts: price movements, rain warnings, seasonal reminders
- Motivation and best practice messages
- WhatsApp CTA buttons for one-tap access

---

## Coverage

| Dimension | MVP Scope |
|---|---|
| States | Karnataka, Andhra Pradesh, Telangana, West Bengal |
| Crops | Paddy, Maize, Groundnut, Cotton, Potato, Ragi + Wheat, Tomato, Sugarcane |
| Languages | Hindi (demo), Kannada, Telugu, Bengali |
| Advisory types | Irrigation, Fertilizer guidance, Crop selection, Government schemes, Pest alerts, Disaster alerts |

---

## Data Sources

| Source | Data | Entity |
|---|---|---|
| IMD / Open-Meteo | Daily + hourly weather, soil moisture, rain forecast | `weather_daily`, `weather_hourly` |
| SoilGrids | Soil type, pH, NPK levels, water holding capacity | `SoilData` |
| eNAM / State Mandi Boards | Daily crop prices, trade volumes, price trends | `MandiPrice`, `MarketTrend` |
| NDMA / IMD | Disaster and extreme weather alerts | `DisasterAlert` |
| ICAR / State Agri Depts | Pest and disease advisories | `PestAlert` |
| Government portals | Central and state agricultural schemes | `GovernmentScheme` |

---

## Technology Stack

| Layer | Technology |
|---|---|
| Runtime | Python 3.11+ / FastAPI |
| Voice (STT) | Sarvam AI — `saaras` model |
| Voice (TTS) | Sarvam AI — `bulbul` model |
| LLM / Reasoning | Claude API (Anthropic) via AWS Bedrock |
| Real-time audio | LiveKit Python SDK |
| WhatsApp | Gupshup / WhatsApp Business API |
| Database | PostgreSQL (AWS RDS) |
| Cache | Redis (AWS ElastiCache) |
| Storage | AWS S3 (voice files, knowledge base JSONs) |
| Task queue | Celery + Redis |
| Hosting | AWS ECS Fargate |
| Monitoring | AWS CloudWatch + OpenTelemetry |

---

## Data Model

VAANI has **31 entities** split into two categories:

### Primary Entities (17)
> Things that exist in the real world. VAANI observes or records them.

| Group | Entities |
|---|---|
| People | `Farmer` |
| Geography | `Location (pincode_location)`, `State`, `AgroClimaticZone` |
| Markets | `Mandi` |
| Agricultural reference | `Crop`, `CropVariety`, `Fertilizer` |
| Government | `GovernmentScheme` |
| Live data signals | `WeatherDaily`, `WeatherHourly`, `SoilData` |
| External alerts | `DisasterAlert`, `PestAlert` |
| Farmer interactions | `ConversationSession`, `ConversationTurn`, `FarmerFeedback` |

### Derived Entities (14)
> Things VAANI creates, computes, or infers by processing primary entities.

| Group | Entities |
|---|---|
| Farmer context | `FarmerCrop`, `FarmerSchemeEligibility`, `FarmerNotifPreference` |
| Crop knowledge | `CropGrowthStage`, `CropCalendarWindow`, `CropAdvisoryRule`, `VarietyState` |
| Market intelligence | `MandiPrice`, `MarketTrend`, `MarketPriceAlert` |
| AI pipeline | `QueryContext`, `QueryResult` |
| System | `Notification`, `WeatherCoverage` |

> Full entity definitions with attributes: [`assets/entities.md`](assets/entities.md)
> ER diagram: [`assets/VAANI_ER_Diagram.drawio`](assets/VAANI_ER_Diagram.drawio)

---

## Database Schema Layout

The database follows a schema-per-domain organisation (PostgreSQL):

```
weather.*       → pincode_location, weather_daily, weather_hourly, weather_coverage
crop.*          → crops, crop_varieties, variety_states, crop_calendar_windows, states
farmer.*        → farmers, farmer_crops, farmer_scheme_eligibility, farmer_notif_preferences
market.*        → mandis, mandi_prices, market_trends, market_price_alerts
advisory.*      → crop_advisory_rules, query_contexts, query_results
conversation.*  → conversation_sessions, conversation_turns
engagement.*    → notifications, farmer_feedback
alerts.*        → pest_alerts, disaster_alerts
```

> Note: `weather.*` schema is sourced from colleague's tried-and-tested API integration.

---

## Project Structure

```
VAANI---The-Farmer-Buddy/
│
├── assets/
│   ├── design.md                  # System design document (3 pillars, 6 layers)
│   ├── requirements.md            # Functional and non-functional requirements
│   ├── VAANI_Solution_Document.docx  # Full solution document (AWS hackathon)
│   ├── entities.md                # All 31 entities with attributes + classification
│   ├── VAANI_ER_Diagram.drawio    # ER diagram (open in draw.io / VS Code extension)
│   └── VAANI Schema.erd           # Colleague's tested DB schema (DataGrip)
│
├── data_models/                   # JSON schemas for static knowledge base entities
│   ├── farmer.json
│   ├── crop.json
│   ├── climate.json
│   ├── soil.json
│   ├── irrigation.json
│   ├── fertilizers.json
│   ├── farmer-market.json
│   └── weather.json
│
├── sip/                           # SIP/telephony configuration (LiveKit)
│   ├── trunks/
│   └── dispatch_rules/
│
├── main.py                        # Application entrypoint
└── requirements.txt               # Python dependencies
```

---

## Performance Targets

| Metric | Target |
|---|---|
| End-to-end latency | < 15 seconds (voice in → voice out) |
| STT accuracy | > 90% for supported languages |
| Advisory accuracy | > 85% (vs agri extension officer benchmark) |
| Farmer satisfaction | > 4.2 / 5 |
| Concurrent users (MVP) | 1,000 |

---

## Responsible AI Commitments

VAANI is built with the following hard guardrails:

- **No guaranteed yield claims** — every recommendation is advisory
- **No exact chemical dosages** — general guidance only, refer to a kisan mitra
- **No medical advice** — out of scope
- **No political content** — neutral and government-scheme aware only
- **Always explainable** — every recommendation includes 2–3 clear reasons
- **Uncertainty acknowledged** — confidence scores surfaced, fallback to human expert when low

---

## Roadmap

| Phase | Features |
|---|---|
| MVP (Hackathon) | Irrigation, fertilizer, crop selection, scheme awareness — Hindi, 4 states |
| Phase 2 | Crop disease detection via image, IoT sensor integration, 8 states, 8 languages |
| Phase 3 | Financial advisory (crop insurance, MSP vs market), community knowledge sharing, all-India |

---

## Hackathon Context

**Event:** AWS AI for Bharat Hackathon
**Track:** Agriculture / Rural AI
**Stack requirement:** AWS services (Bedrock, RDS, S3, ECS, ElastiCache, SQS, CloudWatch)