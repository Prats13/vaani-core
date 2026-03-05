# 🌤 Vaani - Weather Intelligence Service

A high-performance weather backend service for "Vaani - The Farmer Buddy" designed to fetch, cache, and serve highly localized weather data based on Indian Pincodes.

## 🎯 Objective
This service efficiently resolves Indian pincodes to geographic coordinates (Latitude/Longitude) and fetches weather data gracefully. To conserve external API limits and improve latency, the service follows a strategic flow:
1. **Daily Forecast First**: Always queries the daily weather forecast.
2. **Heavy Rain Detection**: Evaluates the daily data to find days with heavy rainfall.
3. **Conditional Hourly Forecast**: Only if heavy rain is detected, it queries the computationally expensive hourly forecast for precisely those days.
4. **Resilient Caching**: Utilizes Redis for sub-millisecond response caching and PostgreSQL for persistent data coverage tracking.

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
   │      ├──▶ 3. Postgres (Check Weather Coverage Window)
   │      │
   │      ├──▶ 4. Open-Meteo DAILY API (Always fetched if refresh needed)
   │      │
   │      ├──▶ 5. Heavy Rain Detection Algorithm
   │      │      └──▶ If Yes: Open-Meteo HOURLY API
   │      │
   │      ├──▶ 6. Upsert Data into PostgreSQL
   │      │
   │      └──▶ 7. Cache final JSON in Redis ──▶ Return JSON
```

---

## 🛠 Tech Stack
- **Framework**: FastAPI (Python 3.9+)
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **ORM**: SQLAlchemy
- **HTTP Client**: HTTPX (Asynchronous)
- **External Apis**: Open-Meteo (Weather), Zippopotam (Geocoding)

---

## 📁 Project Structure
```text
Weather-service/
├── app/
│   ├── main.py              # FastAPI application & entry points
│   ├── config.py            # Pydantic Settings & Env management
│   ├── db.py                # SQLAlchemy engine & session maker
│   ├── models.py            # DB Schema Definitions
│   ├── services/
│   │   ├── geocode_service.py   # Pincode to Lat/Lon resolution
│   │   ├── weather_service.py   # Core orchestration logic
│   │   ├── openmeteo_client.py  # Async Open-Meteo interactions
│   │   └── cache_service.py     # Redis caching logic
│   └── utils/
│       ├── time_utils.py        # Timezone & UTC window calculations
│       └── rainfall_utils.py    # Heavy rain detection algorithms
├── .env                     # Environment variables
├── docker-compose.yml       # Postgres & Redis containers
└── requirements.txt         # Python dependencies
```

---

## 🚀 Setup & Installation

### 1. Prerequisites
- [Docker](https://docs.docker.com/get-docker/) & Docker Compose
- Python 3.9+

### 2. Environment Variables
Ensure a `.env` file exists in the root directory:
```env
DATABASE_URL=postgresql://maheshdasika:pass@localhost:5432/weather
REDIS_URL=redis://localhost:6379
OPEN_METEO_BASE=https://api.open-meteo.com/v1/forecast
PINCODE_API_BASE=http://api.zippopotam.us/in
FORECAST_REFRESH_TTL_HOURS=3
CACHE_TTL_SECONDS=1800
```

### 3. Start Database and Cache Native Services
```bash
docker-compose up -d
```
*Note: If you change DB credentials later, you must delete the docker volume using `docker-compose down -v` and rebuild.*

### 4. Setup Python Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5. Run the Server
```bash
uvicorn app.main:app --reload --port 8080
```

---

## 📡 API Endpoints

### 1. Health Check
Checks if FastAPI, Postgres, and Redis are talking to each other.
- **URL**: `/health`
- **Method**: `GET`
- **Response**:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "timestamp": "2026-03-01T00:00:00Z"
}
```

### 2. Get Weather by Pincode
Fetches the weather forecast for the specified highly localized area.
- **URL**: `/v1/weather/{pincode}`
- **Method**: `GET`
- **Query Parameters**:
  - `days_past` (optional, default: 7): Number of historical days to fetch.
  - `days_future` (optional, default: 16): Number of forecast days to fetch.
  - `force_refresh` (optional, default: false): Bypasses Redis to force a fresh pull.
- **Example**: `http://localhost:8080/v1/weather/560066`
- **Response**: Returns a comprehensive JSON containing `lat`, `lon`, `daily` forecasts, detected `heavy_rain_days`, and granular `hourly` forecasts for those specific rainy days.
