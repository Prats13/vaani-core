# Vaani Data Service

Weather, Crop Intelligence, and Mandi Price backend for **Vaani - The Farmer Buddy**.

Fetches, caches, and serves localized agricultural data based on Indian pincodes — weather forecasts, crop catalogs with variety-level detail, sowing/harvest calendars, weather-integrated crop suitability scoring, and real-time mandi prices from Data.gov.in.

---

## Architecture

```
Client Request (Pincode / State / Crop)
   |
   +---> FastAPI
           |
           +---> 1. Redis Cache (hit? return)
           |
           +---> 2. PostgreSQL (pincode_location, weather, crop, mandi tables)
           |
           +---> 3. External APIs (Open-Meteo, Zippopotam, Data.gov.in)
           |
           +---> 4. Intelligence Processing (suitability scoring, risk, insights)
           |
           +---> 5. Upsert DB + Cache Result --> Return JSON
```

---

## Tech Stack

- **Framework**: FastAPI + Uvicorn
- **Database**: PostgreSQL 15 (DB: `VAANI`, schemas: `weather`, `crop`)
- **Cache**: Redis 7
- **ORM**: SQLAlchemy 2.x
- **HTTP Client**: HTTPX (async)
- **External APIs**: Open-Meteo (weather), Zippopotam (geocoding), Data.gov.in Agmarknet (mandi prices)

---

## Project Structure

```
Data-service/
├── app/
│   ├── main.py                          # FastAPI app, router mounting, health check
│   ├── core/
│   │   ├── config.py                    # Pydantic Settings (DB, Redis, API URLs, TTLs)
│   │   ├── db.py                        # SQLAlchemy engine, session factory
│   │   └── cache_service.py             # Redis get/set/TTL operations
│   │
│   ├── weather/
│   │   ├── models.py                    # pincode_location, weather_daily, weather_hourly, weather_coverage
│   │   ├── routers.py                   # /v1/weather, /v2/weather
│   │   ├── services/
│   │   │   ├── weather_service.py       # V1: fetch forecast, detect heavy rain, upsert DB
│   │   │   ├── weather_features_service.py  # V2: farming advisory flags
│   │   │   └── geocode_service.py       # Pincode -> lat/lon via Zippopotam
│   │   ├── clients/
│   │   │   └── openmeteo_client.py      # Async Open-Meteo API calls
│   │   └── utils/
│   │       ├── features_utils.py        # Advisory flag computation
│   │       └── rainfall_utils.py        # Heavy rain detection algorithm
│   │
│   ├── crop/
│   │   ├── models.py                    # states, crops, crop_calendar_windows, crop_varieties, variety_states
│   │   ├── routers.py                   # 15 endpoints (Tiers 1-5)
│   │   ├── services/
│   │   │   ├── crop_catalog_service.py  # Tier 1-3: catalog, discovery, lifecycle
│   │   │   ├── crop_intelligence_service.py  # Tier 4: weather-integrated suitability
│   │   │   └── crop_query_service.py    # DB queries with filters
│   │   └── utils/
│   │       ├── crop_payload_utils.py    # Response formatting, grouping
│   │       ├── crop_time_utils.py       # Season/month calculations
│   │       ├── state_normalization.py   # "UP" -> "Uttar Pradesh" mapping
│   │       └── time_utils.py            # UTC <-> IST conversions
│   │
│   ├── mandi/
│   │   ├── models.py                    # mandi_prices, api_raw_snapshots
│   │   ├── routers.py                   # /v1/mandi/raw, /v2/mandi/insights
│   │   ├── services/
│   │   │   └── mandi_service.py         # Price fetch, insights computation
│   │   ├── clients/
│   │   │   └── data_gov_client.py       # Data.gov.in Agmarknet API (10 retries)
│   │   └── repositories/
│   │       └── mandi_repo.py            # DB upserts and queries
│   │
│   └── search/
│       ├── routers.py                   # /v1/search
│       └── services/
│           └── search_service.py        # Unified search across crops + varieties
│
├── data/
│   └── merged_crop_calendar_and_varieties.json  # Seed data (35 crops, 109 varieties)
├── scripts/
│   ├── create_crop_schema.sql           # SQL schema + state seed data
│   └── load_crops.py                    # Seed script for crops, varieties, calendars
├── docker-compose.yml                   # PostgreSQL 15 + Redis 7
└── requirements.txt
```

---

## Setup

```bash
cd Data-service

# 1. Start PostgreSQL + Redis
docker-compose up -d

# 2. Python environment
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 3. Initialize crop schema and seed data
psql -U postgres -d VAANI -f scripts/create_crop_schema.sql
python scripts/load_crops.py

# 4. Run
uvicorn app.main:app --reload --port 8081
```

---

## API Endpoints

### System
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | DB + Redis connectivity check |

### Weather
| Method | Path | Params | Description |
|--------|------|--------|-------------|
| GET | `/v1/weather/{pincode}` | `days_past`, `days_future`, `force_refresh` | Daily forecast + heavy rain hourly data |
| GET | `/v2/weather/{pincode}` | `days_past`, `days_future`, `include_hourly`, `force_refresh` | Farming advisory flags, sowing/land-prep recommendations |

### Crop Intelligence
| Method | Path | Description |
|--------|------|-------------|
| GET | `/v1/crops` | All crops (paginated, searchable) |
| GET | `/v1/states` | States with aliases |
| GET | `/v1/crops/state/{state}` | Crops grown in a state |
| GET | `/v1/crops/season/{season}` | Crops by season (Kharif/Rabi/Zaid) |
| GET | `/v1/crops/month/{month}` | Crops by sowing month |
| GET | `/v1/varieties/top` | Top varieties by yield for a state |
| GET | `/v1/varieties/resistant` | Disease-resistant variety search |
| GET | `/v1/varieties/{crop_name}` | All varieties for a crop |
| GET | `/v1/crop/{crop_name}/calendar` | Sowing/growth/harvest calendar windows |
| GET | `/v1/crop/{crop_name}/stage` | Current growth stage by month |
| GET | `/v2/crop/suitability/{pincode}` | Weather-integrated crop recommendations with scoring |
| GET | `/v2/crop/risk/{pincode}` | Weather risks for a specific crop at location |
| GET | `/v2/crop/sowing-window/{pincode}` | Optimal sowing windows based on forecast |
| GET | `/v1/crops/compare` | Multi-crop comparison |
| GET | `/v1/crops/{crop_name}/types` | Variety type statistics |

### Mandi Prices
| Method | Path | Description |
|--------|------|-------------|
| GET | `/v1/mandi/raw` | Raw price data from Data.gov.in Agmarknet |
| GET | `/v2/mandi/insights` | Aggregated insights: trends, volatility, market rankings |

### Search
| Method | Path | Description |
|--------|------|-------------|
| GET | `/v1/search` | Unified search across crops + varieties |

---

## Database Schemas

### `crop` schema (5 tables)
- **states** — 36 Indian states/UTs with aliases
- **crops** — Master crop catalog (35 crops, with local_names, crop_type, season, msp_eligible)
- **crop_varieties** — Variety-level data (109 varieties with yield, seed rate, resistance, growth duration)
- **crop_calendar_windows** — Regional sowing/growth/harvest months (22 calendar entries)
- **variety_states** — Many-to-many: which varieties grow in which states

### `weather` schema (4 tables)
- **pincode_location** — Geocoded pincodes (lat/lon from Zippopotam, cached permanently)
- **weather_daily** — Daily forecasts from Open-Meteo (temp, rain, wind, heavy rain flag)
- **weather_hourly** — Hourly data fetched only for heavy rain days (optimization)
- **weather_coverage** — Data freshness tracking per pincode/provider

### Mandi tables (in `crop` schema)
- **mandi_prices** — Normalized market prices (state, district, market, commodity, min/max/modal price)
- **api_raw_snapshots** — Raw Data.gov.in responses for debugging

---

## Caching Strategy

| Data | Redis TTL | DB Refresh | Rationale |
|------|-----------|------------|-----------|
| Weather forecast | 30 min | 3 hours | Forecasts update frequently |
| States | 7 days | -- | Static reference data |
| Crop catalog | 24 hours | -- | Rarely changes |
| Varieties | 12 hours | -- | Seasonal relevance |
| Crop intelligence (weather-dependent) | 3 hours | -- | Tied to weather freshness |
| Mandi raw prices | 3 hours | 2 days stale threshold | Markets update daily |
| Mandi insights | 6 hours | -- | Aggregated, less volatile |

---

## Seed Data

The crop database is populated from `data/merged_crop_calendar_and_varieties.json`:
- **35 crops** — Rice, Wheat, Bajra, Brinjal, Tomato, Onion, Cotton, etc.
- **109 varieties** — With yield ranges, seed rates, resistance lines, sowing time tags
- **22 calendar entries** — Regional sowing/growth/harvest month windows
- **36 states** — Pre-seeded with aliases (UP, MP, AP, etc.)
