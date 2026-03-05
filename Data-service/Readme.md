# 🌤 Vaani - Weather & Crop Intelligence Service

A high-performance weather and crop intelligence backend service for "Vaani - The Farmer Buddy". It is designed to fetch, cache, and serve highly localized weather data based on Indian Pincodes, alongside comprehensive agricultural crop data, suitability analysis, and farming recommendations.

## 🎯 Objective
This service efficiently resolves Indian pincodes to geographic coordinates, fetches weather data gracefully, and correlates it with detailed crop catalogs to provide actionable intelligence. Key capabilities include:
1. **Pincode Localized Weather**: Fetches both legacy and generalized weather data.
2. **Heavy Rain Detection Algorithm**: Evaluates the daily data to find days with heavy rainfall and selectively caches computational hourly metrics.
3. **Structured Crop Catalog**: Exposes robust APIs to explore crops, varieties, calendars, and states.
4. **Weather-Integrated Crop Intelligence**: Recommends crops, identifies risk, and finds ideal sowing windows based on weather forecasts for specific pincodes.
5. **Resilient Caching**: Utilizes Redis for sub-millisecond response caching and PostgreSQL for persistent data coverage tracking.

---

## 🏗 Architecture & Request Flow

```text
Client Request (Pincode)
   │
   ├──▶ FastAPI
   │      │
   │      ├──▶ 1. Redis (Check Cached Response) ──(Hit)──▶ Return JSON
   │      │
   │      │ (Miss)
   │      ▼
   │      ├──▶ 2. Postgres (Check Local Pincode DB) ──(Miss)──▶ Zippopotam API
   │      │
   │      ├──▶ 3. Postgres (Check Weather Coverage Window & Crop Data)
   │      │
   │      ├──▶ 4. Open-Meteo DAILY/HOURLY API (Always fetched if refresh needed)
   │      │
   │      ├──▶ 5. Weather & Crop Intelligence Processing (Risk/Suitability)
   │      │
   │      ├──▶ 6. Upsert Data into PostgreSQL (VAANI Database)
   │      │
   │      └──▶ 7. Cache final JSON in Redis ──▶ Return JSON
```

---

## 🛠 Tech Stack
- **Framework**: FastAPI (Python 3.9+)
- **Database**: PostgreSQL 15 (Database: `VAANI`, Schemas: `weather`, `crop`)
- **Cache**: Redis 7
- **ORM**: SQLAlchemy
- **HTTP Client**: HTTPX (Asynchronous)
- **External APIs**: Open-Meteo (Weather), Zippopotam (Geocoding)

---

## 📁 Project Structure
```text
Weather-service/
├── app/
│   ├── main.py                     # FastAPI application & mounted routers
│   ├── core/
│   │   ├── config.py               # Pydantic Settings & Env management
│   │   ├── db.py                   # SQLAlchemy engine & session maker
│   │   └── cache_service.py        # Redis caching logic
│   ├── weather/
│   │   ├── routers.py              # Weather API endpoints
│   │   ├── models.py               # Weather DB Schemas
│   │   ├── services/               # Core orchestration logic
│   │   ├── clients/                # Open-Meteo interactions
│   │   └── utils/                  # Heavy rain detection algorithms
│   ├── crop/
│   │   ├── routers.py              # Crop Intelligence endpoints
│   │   ├── models.py               # Crop DB Schemas
│   │   ├── services/               # Crop catalog and risk evaluations
│   │   └── utils/                  # Season and time calculations
│   ├── mandi/
│   │   ├── routers.py              # Mandi Prices endpoints
│   │   ├── models.py               # Mandi DB Schemas
│   │   ├── services/               # Mandi caching and insights logic
│   │   ├── repositories/           # Mandi DB queries and upserts
│   │   └── clients/                # Data.gov.in interactions
│   └── search/
│       ├── routers.py              # Universal search endpoint
│       └── services/               # Search service logic
├── .env                            # Environment variables
├── docker-compose.yml              # Postgres & Redis containers
└── requirements.txt                # Python dependencies
```

---

## 🚀 Setup & Installation

### 1. Prerequisites
- [Docker](https://docs.docker.com/get-docker/) & Docker Compose
- Python 3.9+

### 2. Environment Variables
Ensure a `.env` file exists in the root directory:

### 3. Start Database and Cache Native Services (Docker)
This project uses Docker Compose to easily spin up a PostgreSQL 15 database and a Redis 7 instance. 

Run the following command to start the containers in the background:
```bash
docker-compose up -d
```
*Note: If you change DB credentials later, you must delete the docker volume using `docker-compose down -v` and rebuild.*

To stop the containers when you are done:
```bash
docker-compose down
```

To view the database (PostgreSQL) and Redis container logs:
```bash
docker-compose logs -f
```

### 4. Setup Python Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5. Run the Server
```bash
uvicorn app.main:app --reload --port 8081
```

---

## 📡 API Endpoints

### 🟢 System
- `GET /health` - Checks if FastAPI, Postgres, and Redis are talking to each other.

### 🌤 Weather APIs
- `GET /v1/weather/{pincode}` - Fetches weather forecast for the specified area (includes daily and conditionally fetched hourly data).
- `GET /v2/weather/{pincode}` - Fetches compact weather features (aggregates, conditions, temperature metrics).

### 🌱 Crop Intelligence APIs

**1. Basic Crop Catalog (Tier 1)**
- `GET /v1/crops` - List all crops.
- `GET /v1/states` - List states with coverage.
- `GET /v1/crops/state/{state}` - Get crops suitable for a specific state.
- `GET /v1/crops/season/{season}` - Get crops suitable for a specific season.
- `GET /v1/crops/month/{month}` - Get crops suitable to be sown in a specific month.

**2. Variety Discovery (Tier 2)**
- `GET /v1/varieties/top` - Get top varieties overall for a state.
- `GET /v1/varieties/resistant` - Search for disease-resistant varieties.
- `GET /v1/varieties/{crop_name}` - Get all varieties for a particular crop.

**3. Crop Life Cycle (Tier 3)**
- `GET /v1/crop/{crop_name}/calendar` - Get the calendar windows (sowing/harvesting) for a crop.
- `GET /v1/crop/{crop_name}/stage` - Get the current stage of a crop based on the month.

**4. Weather-Integrated Intelligence (Tier 4)**
- `GET /v2/crop/suitability/{pincode}` - Recommends suitable crops for a pincode based on current weather/month.
- `GET /v2/crop/risk/{pincode}` - Evaluates weather-based risks for a specific crop at a pincode.
- `GET /v2/crop/sowing-window/{pincode}` - Finds ideal sowing windows within the forecast timeframe.

**5. Comparative Analysis (Tier 5)**
- `GET /v1/crops/compare` - Compare multiple crops against each other.
- `GET /v1/crops/{crop_name}/types` - Get statistics around crop types for a given crop and state.

**6. Cross-Category Search (Tier 6)**
- `GET /v1/search` - Universal search across crops, varieties, and diseases.

### 🍅 Mandi Price APIs
- `GET /v1/mandi/raw` - Fetches exact market pricing data from Data.gov.in Agmarknet, caches it in Redis, and locally upserts tracking records in Postgres.
- `GET /v2/mandi/insights` - Runs data-analysis on Mandi prices over customizable windows (7/30/90 days), providing Min/Max/Avg, price volatility, market rankings, and time-series representations.
