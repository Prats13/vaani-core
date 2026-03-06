# VAANI — The Farmer Buddy: Complete Codebase Context

> **Purpose of this file:** This is a comprehensive context document for AI assistants working on this codebase. It covers architecture, code structure, business logic, algorithms, data models, API contracts, and implementation details across ALL branches.

---

## 1. PROJECT IDENTITY

- **Name:** VAANI (Voice-based Agricultural Advisory for Natural Interaction)
- **What it does:** Voice-first AI agricultural advisory system for rural Indian farmers
- **Target users:** 146M Indian farming households, primarily Hindi-speaking, many on feature phones
- **Context:** Built for AWS AI for Bharat Hackathon
- **Repo:** `/Users/prajwalnayak/code/project/Vaani---The-Farmer-Buddy`

### Core Value Proposition
Farmers call a phone number (or use WhatsApp) → speak in Hindi/Hinglish → get spoken advice on irrigation, fertilizers, crop selection, government schemes → advice is backed by real-time weather, soil, and market data + deterministic agricultural rules + Claude AI reasoning.

---

## 2. THREE-PILLAR ARCHITECTURE

```
PILLAR 1: COMMUNICATION LAYER (main branch — sip/)
├── Phone IVR via LiveKit SIP + Exotel PSTN (feature phones)
├── WhatsApp Voice Notes + Interactive Buttons (smartphones)
├── SMS fallback notifications
└── Sarvam AI for STT (Saaras) and TTS (Bulbul)

PILLAR 2: CORE DECISION ENGINE (6 layers, partially built)
├── Layer 1: Intent Classification (NOT BUILT)
├── Layer 2: Context Manager / Slot Filling (NOT BUILT)
├── Layer 3: Data Integration (BUILT — data-service branch)
├── Layer 4: Deterministic Rules (NOT BUILT)
├── Layer 5: AI Reasoning via Claude/Bedrock (NOT BUILT)
└── Layer 6: Guardrails & Safety Filters (NOT BUILT)

PILLAR 3: ENGAGEMENT & RETENTION (NOT BUILT)
├── Daily notifications (price alerts, weather, seasonal tips)
├── WhatsApp CTA buttons
└── Proactive outreach calls
```

---

## 3. GIT BRANCHES & WHAT THEY CONTAIN

### Branch: `main`
**Contains:** SIP/telephony infrastructure + all design documentation

```
Root files:
├── README.md              — Project overview, architecture, roadmap (367 lines)
├── design.md              — System design, 6-layer engine, workflows (498 lines)
├── requirements.md        — Functional/non-functional requirements (331 lines)
├── .gitignore             — Standard Python/IDE/env ignores

assets/
├── design.md              — Copy of root design.md
├── requirements.md        — Copy of root requirements.md
├── entities.md            — Complete 31-entity data model (736 lines) *** CRITICAL FILE ***
├── VAANI Schema.erd       — ER diagram (DataGrip format)
├── VAANI_ER_Diagram.drawio — ER diagram (Draw.io format)
├── VAANI_Solution_Document.docx — Full solution document

sip/                       — LiveKit SIP telephony integration
├── sip_config.py          — All SIP env vars (LiveKit, Exotel, trunks, rooms)
├── trunks/
│   ├── inbound/create_inbound_trunk.py   — Receives farmer calls
│   └── outbound/create_outbound_trunk.py — Makes calls to farmers
├── participants/
│   ├── create_sip_participant.py         — Core SIP participant logic
│   ├── test_outbound_call.py             — Test script
│   ├── test_outbound_participant_human.json
│   └── test_outbound_participant_aip_to_line.json
└── dispatch_rules/
    └── create_sip_dispatch_rule.py       — Routes inbound → AI agent room
```

### Branch: `data-service` (THE MOST COMPLETE BACKEND)
**Contains:** Full FastAPI microservice with Weather + Crop + Mandi modules

```
Data-service/
├── app/
│   ├── main.py                    — FastAPI app, router mounting, health check
│   ├── core/
│   │   ├── config.py              — Pydantic Settings (DB, Redis, API URLs, TTLs)
│   │   ├── db.py                  — SQLAlchemy engine, session factory, Base
│   │   └── cache_service.py       — Redis get/set/TTL operations
│   │
│   ├── weather/                   — WEATHER INTELLIGENCE MODULE
│   │   ├── models.py              — 4 tables: pincode_location, weather_daily, weather_hourly, weather_coverage
│   │   ├── routers.py             — GET /v1/weather/{pincode}, GET /v2/weather/{pincode}
│   │   ├── services/
│   │   │   ├── weather_service.py           — V1 orchestration: resolve pincode → fetch forecast → detect heavy rain → upsert DB → cache
│   │   │   ├── weather_features_service.py  — V2: calls V1 then compute_features() for farming intelligence
│   │   │   └── geocode_service.py           — Pincode → lat/lon via Zippopotam API, cached in PostgreSQL
│   │   ├── clients/
│   │   │   └── openmeteo_client.py          — Async HTTPX calls to Open-Meteo (daily + hourly)
│   │   └── utils/
│   │       ├── features_utils.py            — Advisory flags, sowing/land-prep recommendations (240+ lines)
│   │       ├── rainfall_utils.py            — Heavy rain detection algorithm
│   │       └── time_utils.py                — UTC ↔ Asia/Kolkata conversions
│   │
│   ├── crop/                      — CROP INTELLIGENCE MODULE
│   │   ├── models.py              — 5 tables: states, crops, crop_calendar_windows, crop_varieties, variety_states
│   │   ├── routers.py             — 15 endpoints (Tiers 1-5)
│   │   ├── services/
│   │   │   ├── crop_catalog_service.py      — Tier 1-3: catalog, discovery, lifecycle
│   │   │   ├── crop_intelligence_service.py — Tier 4: weather-integrated suitability scoring
│   │   │   └── crop_query_service.py        — DB queries with filters
│   │   └── utils/
│   │       ├── crop_payload_utils.py        — Response formatting, grouping
│   │       ├── crop_time_utils.py           — Season/month calculations
│   │       └── state_normalization.py       — "UP" → "Uttar Pradesh" mapping
│   │
│   ├── mandi/                     — MANDI PRICE MODULE
│   │   ├── models.py              — 2 tables: api_raw_snapshots, mandi_prices
│   │   ├── routers.py             — GET /v1/mandi/raw, GET /v2/mandi/insights
│   │   ├── services/
│   │   │   └── mandi_service.py             — Price fetching, insights computation
│   │   ├── clients/
│   │   │   └── data_gov_client.py           — Data.gov.in Agmarknet API (10 retries, exponential backoff)
│   │   └── repositories/
│   │       └── mandi_repo.py                — DB upserts, queries
│   │
│   └── search/                    — GLOBAL SEARCH MODULE
│       ├── routers.py             — GET /v1/search
│       └── services/
│           └── search_service.py            — Unified search across crops + varieties
│
├── scripts/
│   ├── create_crop_schema.sql     — SQL schema initialization
│   └── load_crops.py              — Seed script: crops, varieties, calendars (251 lines)
├── docker-compose.yml             — PostgreSQL 15 + Redis 7
├── requirements.txt               — 9 Python packages
└── Readme.md                      — Full API docs, setup guide, Postman collection reference
```

### Branch: `weather-service` (PREDECESSOR — weather only)
**Contains:** Standalone weather microservice (subset of data-service)

```
Weather-service/
├── app/
│   ├── main.py            — FastAPI with /health, /v1/weather/{pincode}, /v2/weather/{pincode}
│   ├── config.py          — Settings (DB: "weather" database, not "VAANI")
│   ├── db.py              — SQLAlchemy setup
│   ├── models.py          — Same 4 weather tables as data-service
│   ├── services/
│   │   ├── openmeteo_client.py
│   │   ├── geocode_service.py
│   │   ├── cache_service.py
│   │   ├── weather_service.py
│   │   └── weather_features_service.py
│   └── utils/
│       ├── time_utils.py
│       ├── rainfall_utils.py
│       └── features_utils.py
├── docker-compose.yml     — PostgreSQL 15 + Redis 7
├── requirements.txt       — Same 9 packages
└── Readme.md
```

**Key difference from data-service:** DB name is `weather` (not `VAANI`), no crop/mandi modules, flat file structure (no `core/` separation). This was the prototype that evolved into data-service.

---

## 4. DATABASE SCHEMAS & MODELS

### 4.1 Weather Schema (data-service: `weather` schema)

**pincode_location** — Geocoded Indian pincodes
| Column | Type | Notes |
|--------|------|-------|
| pincode | String PK | e.g., "560001" |
| lat, lon | Float | From Zippopotam API |
| state, district | String | |
| timezone | String | Default "Asia/Kolkata" |
| source | String | "zippopotam" or "manual" |

**weather_daily** — Daily forecasts from Open-Meteo
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | Auto-increment |
| pincode | FK → pincode_location | |
| provider | String | "open_meteo" |
| date_local | Date | IST date |
| temperature_max/min | Float | Celsius |
| precipitation_sum | Float | mm |
| rain_sum, showers_sum | Float | mm |
| precip_probability_max | Float | 0-100% |
| wind_max, gust_max | Float | km/h |
| is_heavy_rain | Boolean | Computed flag |
| Unique | (pincode, provider, date_local) | |

**weather_hourly** — Hourly data (ONLY for heavy rain days — optimization)
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| pincode | FK → pincode_location | |
| ts_utc | DateTime | UTC timestamp |
| temperature_c, precip_mm | Float | |
| rh_pct, wind_kmh | Float | |
| Unique | (pincode, provider, ts_utc) | |
| Index | (pincode, ts_utc) | Fast lookups |

**weather_coverage** — Tracks data freshness per pincode
| Column | Type | Notes |
|--------|------|-------|
| pincode + provider | Composite PK | |
| min_ts_utc, max_ts_utc | DateTime | Data window |
| last_refresh_at | DateTime | When last fetched |

### 4.2 Crop Schema (data-service: `crop` schema)

**states** — 36 Indian states/UTs with aliases
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| name | String Unique | Full name |
| aliases | JSON | e.g., ["UP", "U.P."] |

**crops** — Master crop catalog
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| name | String Unique | e.g., "Rice", "Wheat" |
| type | String | "Cereal", "Pulse", etc. |
| base_season | String | "Kharif", "Rabi", "Zaid" |
| water_needs, soil_preference | String | |
| growing_period_days | Integer | |

**crop_calendar_windows** — When to sow/grow/harvest by region
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| crop_id | FK → crops | |
| region, season | String | |
| sow_start/end | Integer | Month number (1-12) |
| growth_start/end | Integer | Month number |
| harvest_start/end | Integer | Month number |

**crop_varieties** — Specific varieties with traits
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| crop_id | FK → crops | |
| name | String | e.g., "Basmati 1121" |
| type | String | "Hybrid", "HYV", "Traditional" |
| yield_min/max_q_per_ha | Float | Quintals per hectare |
| duration_days | Integer | |
| seed_rate_kg_per_ha | Float | |
| disease_resistance | String | |
| year | Integer | Release year |

**variety_states** — Many-to-many: varieties ↔ states
| Column | Type | Notes |
|--------|------|-------|
| variety_id | FK → crop_varieties | |
| state_id | FK → states | |

### 4.3 Mandi Schema (data-service)

**api_raw_snapshots** — Raw API responses for debugging
**mandi_prices** — Normalized market price data (commodity, market, district, state, min/max/modal price, arrival date)

### 4.4 Full Entity Model (31 entities — from assets/entities.md)

**17 Primary Entities:** Farmer, Crop, CropVariety, State, Location (pincode), AgroClimaticZone, Mandi, GovernmentScheme, Fertilizer, WeatherDaily, WeatherHourly, SoilData, DisasterAlert, PestAlert, ConversationSession, ConversationTurn, FarmerFeedback

**14 Derived Entities:** FarmerCrop, FarmerSchemeEligibility, FarmerNotifPreference, VarietyState, CropGrowthStage, CropCalendarWindow, CropAdvisoryRule, MandiPrice, MarketTrend, MarketPriceAlert, Notification, WeatherCoverage, QueryContext, QueryResult

---

## 5. API ENDPOINTS — COMPLETE REFERENCE

### 5.1 System
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | DB + Redis connectivity check |

### 5.2 Weather (data-service)
| Method | Path | Params | Description |
|--------|------|--------|-------------|
| GET | `/v1/weather/{pincode}` | days_past=7, days_future=16, force_refresh=false | Raw daily forecast + heavy rain hourly data |
| GET | `/v2/weather/{pincode}` | days_past=7, days_future=16, include_hourly=false, force_refresh=false | Farming intelligence: advisory flags, sowing/land-prep recommendations |

### 5.3 Crop Intelligence (data-service)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/v1/crops` | All crops (paginated, searchable) |
| GET | `/v1/states` | States with aliases |
| GET | `/v1/crops/state/{state}` | Crops suitable for a state |
| GET | `/v1/crops/season/{season}` | Crops by season (Kharif/Rabi/Zaid) |
| GET | `/v1/crops/month/{month}` | Crops by sowing month |
| GET | `/v1/varieties/top` | Top varieties overall |
| GET | `/v1/varieties/resistant` | Disease-resistant varieties |
| GET | `/v1/varieties/{crop_name}` | All varieties for a specific crop |
| GET | `/v1/crop/{crop_name}/calendar` | Sowing/growth/harvest windows |
| GET | `/v1/crop/{crop_name}/stage` | Current growth stage |
| GET | `/v2/crop/suitability/{pincode}` | Weather-integrated crop recommendations with scoring |
| GET | `/v2/crop/risk/{pincode}` | Weather risks for specific crop at location |
| GET | `/v2/crop/sowing-window/{pincode}` | Ideal sowing windows based on weather |
| GET | `/v1/crops/compare` | Multi-crop comparison |
| GET | `/v1/crops/{crop_name}/types` | Variety type statistics |

### 5.4 Mandi Prices (data-service)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/v1/mandi/raw` | Raw price data from Data.gov.in |
| GET | `/v2/mandi/insights` | Aggregated insights: min/max/avg, volatility, trends, market ranking |

### 5.5 Search (data-service)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/v1/search` | Unified search across crops + varieties |

---

## 6. CORE ALGORITHMS & BUSINESS LOGIC

### 6.1 Heavy Rain Detection
```python
def is_heavy_rain_day(day):
    precip = day.get("precipitation_sum", 0) or 0
    prob = day.get("precipitation_probability_max", 0) or 0
    rain = day.get("rain_sum", 0) or 0
    return (precip >= 50) or (precip >= 30 and prob >= 70) or (rain >= 30)
```

### 6.2 Advisory Flags (V2 Weather)
```python
dry_spell         = past_7d_total_rain < 5mm
irrigation_needed = dry_spell AND next_7d_total_rain < 5mm
storm_risk        = heavy_rain_days_exist OR any_precip_probability >= 80%
heat_stress       = count(days where temp_max >= 35°C) > 0
high_wind_risk    = count(days where wind >= 20 km/h) > 0 OR peak_gust >= 35 km/h
```

### 6.3 Sowing/Land-Prep Recommendations
```python
# Land Preparation
if storm_risk:        status = "WAIT"
elif irrigation_needed: status = "OK_WITH_IRRIGATION"
else:                  status = "OK"

# Sowing
if storm_risk:        status = "WAIT"
elif dry_spell and no_rain_forecast: status = "SOW_WITH_IRRIGATION"
else:                  status = "SOW"

# Recommended Window: finds first 3-day stretch without heavy rain
```

### 6.4 Crop Suitability Scoring
```python
score = 5  # base score if sowing window is currently open
score -= 3  # if heavy rain risk at location
score -= 2  # if heat stress at location
score -= 2  # if crop is out of season
# Recommended if score >= 3
```

### 6.5 State Normalization
Maps abbreviations/aliases to canonical state names:
- "UP" / "U.P." → "Uttar Pradesh"
- "MP" → "Madhya Pradesh"
- "AP" → "Andhra Pradesh"
- First checks database aliases, then falls back to static map

### 6.6 Mandi Insights Computation
- Aggregations: min/max/avg/median modal prices across time window
- Volatility: standard deviation of prices
- Grouping: by market, district, or commodity
- Market ranking: best/worst markets by price
- Refresh trigger: fetches from Data.gov.in if local data > 2 days stale

### 6.7 Weather Data Flow (V1)
```
Request for pincode
  → Check Redis cache (30-min TTL)
  → Cache miss? Resolve pincode to lat/lon (Zippopotam → PostgreSQL)
  → Check weather_coverage: stale if last_refresh > 3 hours
  → Stale? Fetch daily forecast from Open-Meteo (7 past + 16 future days)
  → Scan daily data for heavy rain days
  → Heavy rain found? Fetch hourly data (only for those days — optimization)
  → Upsert all data into PostgreSQL
  → Update weather_coverage
  → Build response JSON
  → Cache in Redis
  → Return
```

### 6.8 Decision Engine Flow (designed, not yet coded)
```
Farmer Voice → STT (Sarvam Saaras)
  → Intent Classification (domain + intent + entities)
  → Slot Filling (one question at a time until all slots filled)
  → Data Integration (weather + soil + market from data-service)
  → Deterministic Rules (IF soil_moisture > 60% AND rain_prob > 60% THEN DO_NOT_IRRIGATE)
  → Claude AI Reasoning (generate explanation in Hindi)
  → Guardrails (no yield guarantees, no exact dosages, advisory tone)
  → TTS (Sarvam Bulbul)
  → Voice Response to Farmer
```

---

## 7. EXTERNAL API INTEGRATIONS

| API | URL | Auth | Used For | Cache TTL |
|-----|-----|------|----------|-----------|
| Open-Meteo | `https://api.open-meteo.com/v1/forecast` | None (free) | Weather forecasts (daily + hourly) | 30 min Redis + 3hr DB refresh |
| Zippopotam | `http://api.zippopotam.us/in/{pincode}` | None (free) | Pincode → lat/lon geocoding | Permanent in PostgreSQL |
| Data.gov.in (Agmarknet) | `https://api.data.gov.in/resource/35985678-...` | API Key | Mandi commodity prices | 3-6 hours |
| SoilGrids | (planned) | None | Soil texture, pH, NPK | (not implemented) |
| IMD/NDMA | (planned) | (TBD) | Disaster/extreme weather alerts | (not implemented) |

---

## 8. TECH STACK & DEPENDENCIES

### Runtime & Framework
- Python 3.9+ (3.11+ recommended)
- FastAPI 0.110.0 + Uvicorn 0.28.0

### Database & Cache
- PostgreSQL 15 (database: `VAANI`, schemas: `weather`, `crop`)
- Redis 7 (caching layer)
- SQLAlchemy 2.0.28 (ORM)
- psycopg2-binary 2.9.9 (PostgreSQL driver)

### HTTP & Config
- HTTPX 0.27.0 (async HTTP client for external APIs)
- Pydantic 2.6.4 + pydantic-settings 2.2.1
- python-dotenv 1.0.1

### Voice & Telephony (main branch)
- LiveKit Python SDK (SIP/telephony management)
- Exotel (PSTN provider for Indian phone numbers)
- Sarvam AI — Saaras 2.5 (STT), Bulbul (TTS)
- google-protobuf (Duration objects for SIP config)

### AI/LLM (planned)
- Claude API via AWS Bedrock (reasoning engine)
- OpenAI GPT-4o Mini (tested in demo payloads as fallback)

### Infrastructure
- Docker Compose (PostgreSQL + Redis containers)
- AWS ECS Fargate (planned production deployment)
- AWS S3, CloudWatch, ElastiCache (planned)

---

## 9. CONFIGURATION & ENVIRONMENT VARIABLES

### Data-service Config (`app/core/config.py`)
```
DATABASE_URL          = postgresql://maheshdasika:pass@localhost:5432/VAANI
REDIS_URL             = redis://localhost:6379
OPEN_METEO_BASE       = https://api.open-meteo.com/v1/forecast
PINCODE_API_BASE      = http://api.zippopotam.us/in
FORECAST_REFRESH_TTL_HOURS = 3
CACHE_TTL_SECONDS     = 1800        # 30 min (weather Redis)
CROP_CACHE_TTL_LONG   = 604800      # 7 days (states)
CROP_CACHE_TTL_MEDIUM = 86400       # 24 hours (crops)
CROP_CACHE_TTL_SHORT  = 43200       # 12 hours (varieties)
DATA_GOV_API_KEY      = <api_key>
MANDI_CACHE_TTL_V1    = 10800       # 3 hours
MANDI_CACHE_TTL_V2    = 21600       # 6 hours
```

### SIP Config (main branch — `sip/sip_config.py`)
```
LIVEKIT_SIP_ENDPOINT
OUTBOUND_TRUNK_ID / NAME / ADDRESS / NUMBERS / AUTH
EXOTEL_SIP_DOMAIN     = account_sid.pstn.exotel.com
INBOUND_TRUNK_NAME / ALLOWED_NUMBERS / ALLOWED_ADDRESSES
INBOUND_ROOM_EMPTY_TIMEOUT    = 300s
INBOUND_ROOM_DEPARTURE_TIMEOUT = 20s
INBOUND_ROOM_MAX_PARTICIPANTS  = 5
DISPATCH_RULE_NAME    = freo-inbound-dispatch
```

---

## 10. SIP/TELEPHONY DETAILS (main branch)

### Inbound Call Flow
```
Farmer dials Exotel number
  → Exotel routes to LiveKit SIP endpoint
  → Inbound trunk validates (allowed numbers/addresses)
  → Dispatch rule creates room: "inbound-{random}"
  → Room attributes: call_direction=inbound, call_type=pstn, call_provider=exotel
  → AI agent (inbound_freo_ai_agent) joins the room
  → Krisp noise cancellation enabled
```

### Outbound Call Flow
```
System triggers outbound call
  → create_outbound_sip_participant(phone_number, ...)
  → Converts "+91" prefix to "0" for Exotel compatibility
  → Creates SIP participant with custom headers (Exotel domain)
  → Settings: krisp_enabled=True, wait_until_answered=False
  → Returns SIPParticipantResult(participant_id, identity, room_name)
```

### Key SIP Implementation Details
- `create_sip_participant()` in `sip/participants/create_sip_participant.py`
- Handles Exotel-specific SIP header formatting
- Phone number normalization: "+91XXXXXXXXXX" → "0XXXXXXXXXX"
- Uses `SIPHeaderOptions.SIP_ALL_HEADERS` to capture all headers for audit
- `SIPParticipantResult` dataclass: participant_id, participant_identity, room_name

---

## 11. CACHING STRATEGY

### Multi-Level Cache Architecture
```
Request → Redis (milliseconds)
  └─ miss → PostgreSQL (tens of ms)
       └─ stale → External API (seconds)
            └─ response → upsert PostgreSQL → set Redis → return
```

### TTL Strategy by Data Type
| Data | Redis TTL | DB Refresh | Rationale |
|------|-----------|------------|-----------|
| Weather forecast | 30 min | 3 hours | Forecasts update frequently |
| States | 7 days | — | Static reference data |
| Crops catalog | 24 hours | — | Rarely changes |
| Varieties | 12 hours | — | Seasonal relevance |
| Weather-dependent crop intel | 3 hours | — | Tied to weather freshness |
| Mandi raw prices | 3 hours | 2 days | Markets update daily |
| Mandi insights | 6 hours | — | Aggregated, less volatile |

---

## 12. DOCKER COMPOSE SETUP

### Data-service (`Data-service/docker-compose.yml`)
```yaml
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: maheshdasika
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: VAANI
    ports: ["5432:5432"]
    volumes: [postgres_data:/var/lib/postgresql/data]

  redis:
    image: redis:7
    ports: ["6379:6379"]
    volumes: [redis_data:/data]
```

### Weather-service (`Weather-service/docker-compose.yml`)
Same but with `POSTGRES_DB: weather` instead of `VAANI`.

---

## 13. RESPONSIBLE AI GUARDRAILS

### Hard Rules (MUST enforce)
- **No yield guarantees** — never promise specific harvest amounts
- **No exact chemical dosages** — suggest fertilizer types, not "use X kg/acre"
- **No medical advice** — no guidance on pesticide health effects
- **No political content** — stay agricultural
- **Advisory tone always** — "Main suggest karunga..." not "Aap yeh karo"
- **Confidence scores** — every recommendation carries a confidence level
- **Disclaimers** — for uncertain situations
- **Fallback to human experts** — when AI confidence < threshold

### Response Structure (every recommendation)
1. Direct Answer (yes/no or specific action)
2. Key Reasoning (2-3 supporting reasons with data)
3. Risk Factors (optional caveats)
4. Next Steps (follow-up or monitoring suggestion)

---

## 14. WHAT'S BUILT vs. WHAT'S NOT

### BUILT
- [x] SIP telephony infrastructure (LiveKit + Exotel) — `main`
- [x] Weather intelligence service (Open-Meteo, heavy rain detection, advisory flags) — `data-service`
- [x] Crop intelligence service (catalog, varieties, suitability scoring) — `data-service`
- [x] Mandi price service (Data.gov.in, insights, market ranking) — `data-service`
- [x] Global search across crops/varieties — `data-service`
- [x] Redis caching layer — `data-service`
- [x] PostgreSQL schemas & models — `data-service`
- [x] Docker Compose for local dev — `data-service`
- [x] Comprehensive design documentation — `main`
- [x] 31-entity data model design — `main/assets/entities.md`
- [x] Crop data loading script — `data-service/scripts/load_crops.py`

### NOT BUILT
- [ ] FastAPI main application (the orchestrator that ties everything together)
- [ ] Intent classification engine (NLP layer)
- [ ] Context manager / conversational slot filling
- [ ] Deterministic rule engine (irrigation rules, fertilizer rules)
- [ ] Claude/Bedrock LLM integration for reasoning
- [ ] Guardrail enforcement layer
- [ ] Farmer profile management (Farmer entity CRUD)
- [ ] WhatsApp Business API integration
- [ ] SMS integration
- [ ] Notification system (proactive alerts)
- [ ] SoilGrids API integration
- [ ] Disaster/pest alert system
- [ ] Authentication & authorization
- [ ] Admin dashboard
- [ ] CI/CD pipeline
- [ ] Unit/integration tests
- [ ] Monitoring & observability (CloudWatch, OpenTelemetry)
- [ ] Production deployment config (ECS Fargate, terraform/CDK)

---

## 15. MVP SCOPE & SUCCESS METRICS

### MVP Scope
- **Crops:** 5 (Rice, Wheat, Tomato, Onion, Cotton)
- **States:** 2-3 (likely Karnataka, UP, Maharashtra)
- **Language:** Hindi/Hinglish
- **Use Cases:** Irrigation decision, fertilizer guidance, crop selection, scheme awareness
- **Channels:** Phone IVR (primary), WhatsApp (secondary)

### Performance Targets
| Metric | Target |
|--------|--------|
| End-to-end voice latency | < 15 seconds |
| STT processing | < 2 seconds |
| Decision generation | < 3 seconds |
| Concurrent users (MVP) | 1,000 |
| Daily queries | 100,000+ |
| STT accuracy (Hindi) | > 90% |
| Advisory accuracy | > 85% vs extension officer |

---

## 16. KEY DESIGN DECISIONS & RATIONALE

1. **Deterministic rules BEFORE LLM** — Prevents hallucinations on physical/agricultural decisions. Rules are auditable. LLM only generates explanations.

2. **One question at a time (slot filling)** — Rural farmers aren't used to forms. Natural conversation flow. Minimize cognitive load.

3. **Hourly data only for heavy rain days** — Performance optimization. Daily data is always fetched; hourly is expensive and only needed when heavy rain is detected.

4. **Redis-first, PostgreSQL-second** — Sub-millisecond cache hits for frequently queried pincodes. PostgreSQL as persistent fallback and coverage tracking.

5. **Exotel for PSTN** — Covers rural India where internet is unreliable. Feature phone support via IVR.

6. **Sarvam AI for STT/TTS** — Purpose-built for Indian languages. Better Hindi accuracy than generic models.

7. **Microservice separation** — Weather/Crop/Mandi as independent data service. SIP as separate communication service. Decision engine as orchestrator. Each scales independently.

8. **Phone number normalization** — "+91" → "0" for Exotel compatibility. Indian telecom-specific requirement.

---

## 17. COMMON PATTERNS IN THE CODEBASE

### Service Pattern
```python
# Every service follows: check cache → check DB freshness → fetch external → upsert → cache → return
async def get_data(db, identifier, force_refresh=False):
    cache_key = generate_key(identifier)
    if not force_refresh:
        cached = await get_cached(cache_key)
        if cached: return cached
    # ... fetch, process, store ...
    await set_cached(cache_key, result, ttl)
    return result
```

### Router Pattern
```python
@router.get("/v1/resource/{id}")
async def get_resource(id: str, db: Session = Depends(get_db)):
    result = await service_function(db, id)
    return result
```

### Config Pattern
```python
class Settings(BaseSettings):
    SETTING_NAME: type = default_value
    model_config = SettingsConfigDict(env_file=".env")
settings = Settings()
```

---

## 18. SETUP & RUNNING INSTRUCTIONS

### Data-service (recommended for development)
```bash
cd Data-service
docker-compose up -d                    # Start PostgreSQL + Redis
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python scripts/load_crops.py            # Seed crop data
uvicorn app.main:app --reload --port 8081
```

### Weather-service (standalone)
```bash
cd Weather-service
docker-compose up -d
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

### SIP Setup (main branch)
```bash
# Requires .env with all LiveKit/Exotel credentials
python sip/trunks/inbound/create_inbound_trunk.py
python sip/trunks/outbound/create_outbound_trunk.py
python sip/dispatch_rules/create_sip_dispatch_rule.py
python sip/participants/test_outbound_call.py  # Test
```
