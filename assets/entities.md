# VAANI — Entity & Attribute Definitions

> This document defines all data entities for VAANI.
> Format: each entity lists its attributes with `name | type | description`.
> This is the basis for the ER diagram, Pydantic models, DB schema, and static JSON files.

---

## Entity Classification: Primary vs Derived

**Definition:**
- **Primary Entity** — exists independently in the real world or as a real event. VAANI *observes* or *records* it. It has a lifecycle of its own.
- **Derived Entity** — created, computed, assembled, or inferred *by VAANI* as a result of processing, combining, or reacting to primary entities. It would not exist without VAANI's logic.

---

### Primary Entities (17)
> These form the **nodes** of the knowledge graph. They are the raw material VAANI works with.

| # | Entity | Source | Why it's Primary |
|---|---|---|---|
| 1 | **Farmer** | User onboarding | A real person — exists before VAANI knows about them |
| 2 | **Crop** | Agricultural reference | A biological crop type — exists in the real world |
| 3 | **CropVariety** | Agricultural reference | A real sub-type of a crop (Basmati, IR36) — exists independently |
| 4 | **State** | Geographic reference | A real administrative unit — exists independently |
| 5 | **Location** (`pincode_location`) | Pincode lookup | A real geographic point — VAANI resolves it, doesn't create it. DB table: `pincode_location`, PK = `pincode` (str) |
| 6 | **AgroClimaticZone** | Geographic reference | A real agro-geographic zone defined by soil/rainfall patterns |
| 7 | **Mandi** | Market reference | A real physical wholesale market — exists independently |
| 8 | **GovernmentScheme** | Government source | A real government program — published externally |
| 9 | **Fertilizer** | Agricultural reference | A real agricultural product — exists independently |
| 10 | **WeatherDaily** | IMD / Open-Meteo API | Real measured atmospheric data — VAANI fetches, doesn't generate |
| 11 | **WeatherHourly** | IMD / Open-Meteo API | Real hourly measurement — same reasoning as WeatherDaily |
| 12 | **SoilData** | SoilGrids API | Real measured soil characteristics — external source |
| 13 | **DisasterAlert** | NDMA / IMD | A real official government alert — issued externally |
| 14 | **PestAlert** | ICAR / State Agri Dept | A real crop threat advisory — issued by external authority |
| 15 | **ConversationSession** | Farmer interaction | A real event — the farmer actually called/messaged |
| 16 | **ConversationTurn** | LiveKit (real-time) | A real exchange — managed by LiveKit, logged by VAANI |
| 17 | **FarmerFeedback** | Farmer input | Real feedback — the farmer expressed it, VAANI records it |

---

### Derived Entities (14)
> These form the **edges and computed nodes** of the knowledge graph. VAANI creates them by processing primary entities.

| # | Entity | Derived From | How VAANI derives it |
|---|---|---|---|
| 1 | **FarmerCrop** | Farmer + Crop + CropVariety | Farmer registers an active crop — VAANI creates the junction with farm context |
| 2 | **FarmerSchemeEligibility** | Farmer + GovernmentScheme | VAANI evaluates scheme eligibility rules against farmer's profile |
| 3 | **FarmerNotifPreference** | Farmer | Created during onboarding as a settings record — 1:1 with Farmer |
| 4 | **VarietyState** | CropVariety + State | VAANI resolves which varieties grow where — junction assembled from reference data |
| 5 | **CropGrowthStage** | Crop | Crop's lifecycle broken into stages — derived from agricultural knowledge about the crop |
| 6 | **CropCalendarWindow** | Crop + AgroClimaticZone | Sowing/harvest calendar computed from crop science + zone's seasonal pattern |
| 7 | **CropAdvisoryRule** | System logic | Rules authored by agri experts, stored as data — exist only inside VAANI |
| 8 | **MandiPrice** | Mandi + Crop + eNAM API | VAANI queries eNAM and stores the result — a time-series snapshot derived from querying real markets |
| 9 | **MarketTrend** | MandiPrice (aggregation) | VAANI computes rolling averages and direction from historical MandiPrice records |
| 10 | **MarketPriceAlert** | MandiPrice + FarmerCrop + CropAdvisoryRule | VAANI detects a threshold breach by comparing real-time price against farmer's crop context |
| 11 | **Notification** | Farmer + trigger event | VAANI generates and dispatches — does not exist until the system decides to send it |
| 12 | **WeatherCoverage** | Location + weather station metadata | VAANI maps pincodes to available data sources — system-computed availability metadata |
| 13 | **QueryContext** | Farmer + WeatherDaily + SoilData + MandiPrice + Crop | VAANI assembles the full context snapshot to send to the LLM — exists only in the AI pipeline |
| 14 | **QueryResult** | QueryContext + LLM | LLM output parsed and stored by VAANI — created purely through AI inference |

---

### Knowledge Graph Implications

```
PRIMARY ENTITIES (real-world nodes)
        ↓  observed / recorded by VAANI
DERIVED ENTITIES (computed edges & nodes)
        ↓  processed by AI pipeline
QUERY CONTEXT → QUERY RESULT → NOTIFICATION → FARMER
```

**Key insight:** The 7 static reference primaries (Crop, CropVariety, State, AgroClimaticZone, Mandi, GovernmentScheme, Fertilizer) form the **knowledge base**. The 4 live-data primaries (WeatherDaily, WeatherHourly, SoilData, DisasterAlert/PestAlert) form the **real-time signal layer**. Derived entities are where VAANI's intelligence lives.

---

## Batch 1 of ? (Entities 1–10)

---

### 1. Farmer - I/O
> The primary user of the system. Profile is built incrementally through conversation.

| Attribute | Type | Description |
|---|---|---|
| farmer_id | UUID | Primary key |
| phone_number | str | Primary SIM number — for SMS fallback and identity |
| whatsapp_number | str | WhatsApp number — system entry point; can be same or different from phone_number |
| name | str | Farmer's full name |
| age | int | Age in years |
| gender | enum(Male, Female, Other) | Gender |
| pincode | str | Home/farm pincode — used to derive location |
| district | str | District name |
| state | str | State name |
| land_area_acres | float | Total land holding in acres (canonical unit; input accepted in bigha/guntha/cents and converted) |
| irrigation_source | enum(Canal, Borewell, Rainfed, Drip, Sprinkler) | Primary irrigation source |
| language_preference | enum(Hindi, Kannada, Telugu, Bengali) | Preferred language for voice interactions |
| experience_years | int | Years of farming experience — used to calibrate advice complexity |
| is_profile_complete | bool | Whether onboarding slot-filling is complete |
| created_at | datetime | Profile creation timestamp |
| updated_at | datetime | Last profile update timestamp |
---

### 2. Crop
> Reference data for a crop type — its characteristics, requirements, and suitability.
> This is **static/reference data** (not per-farmer).

| Attribute | Type | Description |
|---|---|---|
| crop_id | UUID | Primary key |
| crop_name | str | Standard English name (e.g. "Paddy") |
| local_names | dict(str→str) | Local names keyed by language code (e.g. `{"hi": "धान", "kn": "ಭತ್ತ"}`) |
| crop_type | enum(Cereal, Pulse, Oilseed, Vegetable, Cash Crop, Fiber, Spice) | Crop category |
| season | enum(Kharif, Rabi, Zaid, Year-round) | Primary growing season |
| growth_duration_days | int | Typical days from sowing to harvest |
| min_water_requirement_mm | float | Minimum water requirement across full season |
| max_water_requirement_mm | float | Maximum water requirement across full season |
| suitable_soil_types | list(str) | Soil types this crop grows well in |
| suitable_states | list(str) | Indian states where this crop is grown |
| msp_eligible | bool | Whether the crop has a government Minimum Support Price |

---

### 3. FarmerCrop - I/O
> Represents a specific crop that a farmer is actively growing. Links Farmer ↔ Crop with farm-level context.

| Attribute | Type | Description |
|---|---|---|
| farmer_crop_id | UUID | Primary key |
| farmer_id | UUID | FK → Farmer |
| crop_id | UUID | FK → Crop |
| variety_id | UUID | FK → CropVariety (null = unknown variety) — added from colleague's schema |
| sowing_date | date | Date the crop was sown |
| expected_harvest_date | date | Expected harvest date |
| area_acres | float | Area under this crop in acres (consistent with Farmer.land_area_acres) |
| irrigation_method | enum(Flood, Drip, Sprinkler, Furrow, Manual) | Irrigation method used for this crop |
| last_irrigation_date | date | Date of last irrigation — key input for irrigation decisions |
| current_growth_stage | str | E.g. "Vegetative", "Flowering", "Grain filling" |
| is_active | bool | Whether this crop is currently being grown (not yet harvested) |
| created_at | datetime | Record creation timestamp |

---

### 4. Location
> Canonical location record derived from a pincode.
> **DB table name: `pincode_location`** — aligned with colleague's tested schema.
> `pincode` is the **natural primary key** (str) used by all weather tables as FK. All other non-weather entities reference this table via `pincode` as well for consistency.

| Attribute | Type | Description |
|---|---|---|
| pincode | str | **Primary key** — 6-digit Indian pincode (natural key, per colleague's schema) |
| taluk | str | Sub-district level |
| district | str | District name |
| state | str | State name |
| latitude | float | Latitude — used for API calls (Open-Meteo, SoilGrids) |
| longitude | float | Longitude — used for API calls |
| agro_zone_id | UUID | FK → AgroClimaticZone |

- agro_zone_id - info required
---

### 5. AgroClimaticZone
> Geographic zone with shared soil, rainfall, and temperature patterns.
> **Static reference data** used to contextualize crop advice.

| Attribute              | Type | Description |
|------------------------|---|---|
| agro_zone_id           | UUID | Primary key |
| agro_zone_name         | str | Human-readable name (e.g. "Northern Dry Zone") |
| agro_zone_code         | str | Short code (e.g. "KA-NDZ") |
| state                  | str | State this zone belongs to |
| avg_annual_rainfall_mm | float | Average annual rainfall in mm |
| primary_soil_type      | str | Dominant soil type in this zone |
| elevation_range_m      | str | Elevation range in metres (e.g. "300-900") |
| description            | str | Plain-language description for context window injection |

---

### 6. WeatherDaily
> Daily aggregated weather data per pincode — used for planning decisions (irrigation, sowing).
> **DB table name: `weather.weather_daily`** — directly from colleague's tested schema.
> FK is `pincode` (str), not a UUID, matching `pincode_location.pincode`.

| Attribute | Type | Description |
|---|---|---|
| weather_daily_id | UUID | Primary key |
| pincode | str | FK → pincode_location (colleague's tested FK: `weather_daily_pincode_fkey`) |
| date | date | The calendar date this record covers |
| temp_max_celsius | float | Maximum temperature of the day |
| temp_min_celsius | float | Minimum temperature of the day |
| humidity_percent | float | Average relative humidity |
| rainfall_mm | float | Total rainfall for the day |
| soil_moisture_percent | float | Topsoil moisture percentage (0–100) |
| rain_probability_24h | float | Probability of rain in next 24 hours (0.0–1.0) |
| rain_probability_48h | float | Probability of rain in next 48 hours (0.0–1.0) |
| evapotranspiration_mm | float | Daily crop water demand indicator |
| data_source | str | Source API (e.g. "open-meteo", "imd") |
| fetched_at | datetime | When this record was fetched |

---

### 7. SoilData
> Soil characteristics for a location fetched from SoilGrids API.
> **Semi-static** — changes slowly, cached with a long TTL.

| Attribute | Type | Description |
|---|---|---|
| soil_id | UUID | Primary key |
| location_id | UUID | FK → Location |
| soil_type | enum(Clay, Sandy, Loamy, Silt, Clay-Loam, Sandy-Loam) | Dominant soil texture |
| ph_level | float | Soil pH (typically 4.0–9.0) |
| nitrogen_level | enum(Low, Medium, High) | Available nitrogen level |
| phosphorus_level | enum(Low, Medium, High) | Available phosphorus level |
| potassium_level | enum(Low, Medium, High) | Available potassium level |
| organic_matter_percent | float | Organic matter content percentage |
| water_holding_capacity | enum(Low, Medium, High) | How well the soil retains water |
| data_source | str | Source API (e.g. "soilgrids") |
| fetched_at | datetime | When this record was fetched |

- Farmers carry soil data with them in terms of soil report. What Soil Report constitues of ? - Copy of a Soil Reports  
---

### 8. Mandi
> A physical agricultural wholesale market where farmers sell produce.
> **Static reference data** — updated periodically.

| Attribute | Type | Description |
|---|---|---|
| mandi_id | UUID | Primary key |
| mandi_name | str | Official name of the mandi |
| district | str | District where the mandi is located |
| state | str | State |
| location_id | UUID | FK → Location (for distance calculation) |
| is_enam_registered | bool | Whether connected to the eNAM digital platform |
| contact_number | str | Contact number of mandi office |
| operating_days | str | E.g. "Mon-Sat" |

---

### 9. MandiPrice
> Daily price records for a crop at a specific mandi. Fetched from eNAM API.
> **Transient** — cached with daily TTL; historical records kept for trend analysis.

| Attribute | Type | Description |
|---|---|---|
| price_id | UUID | Primary key |
| mandi_id | UUID | FK → Mandi |
| crop_id | UUID | FK → Crop |
| min_price_per_quintal | float | Minimum price recorded that day |
| max_price_per_quintal | float | Maximum price recorded that day |
| modal_price_per_quintal | float | Most common/modal price — used as the reference price |
| trade_volume_quintals | float | Total trade volume in quintals |
| recorded_date | date | Date of this price record |
| data_source | str | Source (e.g. "enam", "state-mandi-board") |

---

### 10. GovernmentScheme
> Central or state government agricultural scheme with eligibility and application details.
> **Static reference data** — updated periodically.

| Attribute | Type | Description |
|---|---|---|
| scheme_id | UUID | Primary key |
| scheme_name | str | Full official name of the scheme |
| scheme_code | str | Short identifier (e.g. "PM-KISAN") |
| level | enum(Central, State) | Whether central or state scheme |
| state | str | State name (null for central schemes) |
| description | str | Plain-language description (used in LLM context) |
| eligibility_criteria | JSON | Structured eligibility rules (land size, crop type, income, etc.) |
| benefits | str | What the farmer gets (amount, subsidy, service) |
| application_process | str | Step-by-step how to apply |
| application_deadline | date | Deadline (null if rolling) |
| contact_info | str | Office/helpline contact |
| is_active | bool | Whether the scheme is currently open |

---

## Batch 2 of ? (Entities 11–20)

---

### 11. ConversationSession - Backend config (Not required)
> Tracks a single ongoing conversation. Holds the context-gathering state machine — what information has been collected and what is still needed.

| Attribute | Type | Description |
|---|---|---|
| session_id | UUID | Primary key |
| farmer_id | UUID | FK → Farmer |
| channel | enum(WhatsApp, IVR, SMS) | Channel through which the conversation is happening |
| intent_domain | enum(Farming, Market, GovernmentScheme, General) | Classified domain of the conversation |
| intent_type | str | Specific intent (e.g. "irrigation_decision", "crop_selection", "scheme_eligibility") |
| context_fields_needed | list(str) | Which context fields are required to resolve this intent |
| context_gathered | JSON | Map of field name → collected value so far |
| status | enum(Collecting, Processing, Responding, Completed, Abandoned) | Current state in the pipeline |
| started_at | datetime | When the session began |
| ended_at | datetime | When the session ended (null if still active) |


### 12. ConversationTurn - Backend config (Not required)
> A single message exchange within a session — stored for audit and analytics.
> **Note**: Real-time turn management (STT, TTS, audio streaming) is handled by the LiveKit Python SDK internally. This entity is the persistent log of each turn after the fact.

| Attribute | Type | Description |
|---|---|---|
| turn_id | UUID | Primary key |
| session_id | UUID | FK → ConversationSession |
| turn_number | int | Sequential order within the session (1, 2, 3…) |
| speaker | enum(Farmer, System) | Who sent this message |
| transcribed_text | str | STT output from farmer's voice (populated by LiveKit pipeline) |
| response_text | str | System's text response (null for farmer turns) |
| stt_latency_ms | int | Time taken for speech-to-text (reported by LiveKit) |
| tts_latency_ms | int | Time taken for text-to-speech (reported by LiveKit) |
| created_at | datetime | Timestamp of this turn |

### 13. QueryContext - Backend config (Not required)
> The fully assembled context package sent to the LLM reasoning engine. Snapshot of all data at decision time.

| Attribute | Type | Description |
|---|---|---|
| query_context_id | UUID | Primary key |
| session_id | UUID | FK → ConversationSession |
| farmer_id | UUID | FK → Farmer |
| intent_type | str | Intent being resolved (matches session intent_type) |
| farmer_context | JSON | Snapshot of farmer profile and active crop details |
| crop_context | JSON | Crop knowledge base data relevant to this query |
| weather_context | JSON | Weather snapshot fetched at time of request |
| soil_context | JSON | Soil data snapshot for farmer's location |
| market_context | JSON | Mandi price snapshot (included for market/crop queries) |
| scheme_context | JSON | Relevant scheme data (included for scheme queries) |
| deterministic_output | JSON | Result from the rule-based logic layer (pre-LLM decision) |
| created_at | datetime | When the request was assembled |

---

### 14. QueryResult - Backend config (Not required)
> The LLM's parsed and validated response with full metadata for auditing and feedback.

| Attribute | Type | Description |
|---|---|---|
| query_result_id | UUID | Primary key |
| query_context_id | UUID | FK → QueryContext |
| recommendation | str | The direct answer (e.g. "Do not irrigate today") |
| reasoning | list(str) | 2–3 key reasons supporting the recommendation |
| risk_factors | list(str) | Optional warnings or caveats |
| next_steps | str | Optional follow-up action or monitoring suggestion |
| raw_llm_output | str | Full unprocessed LLM response before parsing |
| confidence_score | float | Confidence level 0.0–1.0 |
| guardrail_flags | list(str) | Safety issues flagged (empty list if clean) |
| llm_model | str | Model used (e.g. "claude-sonnet-4-6") |
| llm_latency_ms | int | Time taken for LLM inference |
| total_latency_ms | int | End-to-end latency from voice in to voice out |
| created_at | datetime | Response generation timestamp |

---

### 15. Notification
> An outbound message sent proactively to a farmer — price alerts, weather warnings, reminders, motivation.

| Attribute | Type | Description |
|---|---|---|
| notification_id | UUID | Primary key |
| farmer_id | UUID | FK → Farmer |
| notification_type | enum(PriceAlert, WeatherAlert, SeasonalReminder, BestPracticeTip, SchemeDeadline, Motivation) | Category of notification |
| channel | enum(WhatsApp, SMS) | Delivery channel |
| message_text | str | Text content of the notification |
| cta_buttons | JSON | WhatsApp interactive button config (optional) |
| scheduled_at | datetime | When this notification was scheduled to send |
| sent_at | datetime | Actual send time (null if not yet sent) |
| delivery_status | enum(Pending, Sent, Delivered, Failed) | Delivery state |
| created_at | datetime | Record creation timestamp |

---

Notes:
* voice_s3_key is not required

### 16. FarmerFeedback - I/O
> Post-interaction feedback collected from the farmer to evaluate advisory quality.

| Attribute | Type | Description |
|---|---|---|
| feedback_id | UUID | Primary key |
| farmer_id | UUID | FK → Farmer |
| session_id | UUID | FK → ConversationSession |
| query_result_id | UUID | FK → QueryResult |
| rating | int | Rating 1–5 (collected via WhatsApp reply or button) |
| was_advice_followed | bool | Whether the farmer acted on the advice (null = not responded) |
| feedback_text | str | Optional voice transcription or typed feedback |
| created_at | datetime | Feedback submission timestamp |

---

### 17. Fertilizer
> Reference data for fertilizer types used in fertilizer guidance advisory.
> **Static knowledge data** — used in LLM context, no exact dosage stored.

| Attribute | Type | Description |
|---|---|---|
| fertilizer_id | UUID | Primary key |
| fertilizer_name | str | Common name (e.g. "Urea", "DAP", "MOP") |
| fertilizer_code | str | Short identifier (e.g. "UREA", "DAP") |
| nutrient_type | enum(Nitrogen, Phosphorus, Potassium, NPK, Micronutrient, Organic) | Primary nutrient category |
| nutrient_composition | str | Composition ratio (e.g. "46-0-0" for Urea) |
| suitable_crop_ids | list(UUID) | FK → Crop list |
| suitable_soil_types | list(str) | Soil types this fertilizer works well for |
| recommended_timing | str | When to apply relative to crop growth (e.g. "Before sowing", "At vegetative stage") |
| availability | enum(Widely Available, Moderately Available, Limited) | How easy to find in rural markets |
| approx_price_per_50kg | float | Approximate market price per 50kg bag in INR |
| safety_note | str | Brief safety note (no exact dosage — always advisory) |

---

### 18. CropGrowthStage
> Defines the sequential growth stages of a crop with water requirements and key activities per stage.
> **Static reference data** — linked to Crop, used to drive irrigation and fertilizer advice.

| Attribute | Type | Description |
|---|---|---|
| stage_id | UUID | Primary key |
| crop_id | UUID | FK → Crop |
| stage_name | str | Stage name (e.g. "Germination", "Vegetative", "Flowering", "Grain Filling", "Maturity") |
| stage_order | int | Sequential order (1 = first stage after sowing) |
| days_from_sowing_start | int | Day number when this stage begins |
| days_from_sowing_end | int | Day number when this stage ends |
| water_requirement_mm_per_day | float | Daily water requirement at this stage |
| irrigation_interval_days | int | Recommended days between irrigations at this stage |
| key_activities | list(str) | Important farming tasks at this stage (e.g. "Apply first top dressing") |
| pest_risk_level | enum(Low, Medium, High) | General pest risk at this stage |

---

### 19. PestAlert
> A pest or disease warning for a crop in a geographic zone, triggered by weather conditions.

| Attribute | Type | Description |
|---|---|---|
| alert_id | UUID | Primary key |
| crop_id | UUID | FK → Crop |
| agro_zone_id | UUID | FK → AgroClimaticZone (zone-level scope, not single pincode) |
| pest_name | str | Name of the pest or disease (e.g. "Brown Planthopper", "Blast") |
| pest_type | enum(Insect, Fungal, Bacterial, Viral, Weed) | Category of threat |
| alert_level | enum(Watch, Warning, Emergency) | Severity level |
| description | str | Plain-language description of the threat |
| favorable_weather_conditions | str | Weather pattern that triggers this alert (used for rule-based matching) |
| recommended_action | str | Advisory action for farmer (no chemical dosage) |
| valid_from | date | Start of the alert window |
| valid_until | date | End of the alert window |
| data_source | str | Source of the alert (e.g. "ICAR", "state-agri-dept") |
| created_at | datetime | Record creation timestamp |

---

### 20. MarketTrend
> Aggregated price trend analysis for a crop at state level over a rolling period.
> Derived from MandiPrice records — used for crop selection advice.

| Attribute | Type | Description |
|---|---|---|
| trend_id | UUID | Primary key |
| crop_id | UUID | FK → Crop |
| state | str | State-level aggregation (trends vary significantly by state) |
| period_months | int | Rolling period in months (e.g. 6) |
| avg_price_per_quintal | float | Average modal price across mandis in the period |
| min_price_per_quintal | float | Lowest recorded price in the period |
| max_price_per_quintal | float | Highest recorded price in the period |
| price_trend_direction | enum(Rising, Falling, Stable, Volatile) | Overall price movement direction |
| price_change_percent | float | Price change vs same period last year (positive = increase) |
| demand_level | enum(Low, Medium, High) | Inferred demand based on trade volumes |
| computed_at | datetime | When this trend was last computed |

---

## Batch 3 of 3 (Entities 21–25) — Final Batch

---

### 21. DisasterAlert
> A natural disaster or extreme weather risk alert affecting farming communities.
> Covers villages on state borders, coastal areas, and Union Territories that face cyclones, floods, droughts, and other hazards.
> **Broader scope than PestAlert** — applies at district or state level, sourced from NDMA / IMD / state disaster management authorities.

| Attribute | Type | Description |
|---|---|---|
| disaster_alert_id | UUID | Primary key |
| disaster_type | enum(Flood, Cyclone, Drought, Hailstorm, ColdWave, HeatWave, Earthquake, Landslide, Tsunami, LocustSwarm) | Type of disaster or extreme event |
| geographic_scope | enum(District, State, UnionTerritory, CoastalStrip, BorderRegion) | Granularity of the affected area |
| affected_state | str | State name (or UT name) |
| affected_district | str | District name (null if state-wide) |
| alert_level | enum(Advisory, Watch, Warning, Emergency) | Severity — Emergency triggers immediate push notification |
| description | str | Plain-language description of the threat |
| farming_impact | str | Specific impact on crops, livestock, or farming operations |
| recommended_action | str | What the farmer should do (e.g. "Harvest immediately", "Move livestock to higher ground") |
| valid_from | datetime | Start of the alert window |
| valid_until | datetime | End of the alert window |
| data_source | str | Issuing authority (e.g. "NDMA", "IMD", "State SDMA") |
| source_url | str | Link to official alert (for traceability) |
| issued_at | datetime | When the alert was officially issued |
| created_at | datetime | When the record was ingested into VAANI |

---

### 22. FarmerSchemeEligibility
> Junction entity tracking a farmer's eligibility status for a specific government scheme.
> Built during the "Government Scheme Awareness" advisory flow.

| Attribute | Type | Description |
|---|---|---|
| eligibility_id | UUID | Primary key |
| farmer_id | UUID | FK → Farmer |
| scheme_id | UUID | FK → GovernmentScheme |
| is_eligible | bool | Whether the farmer meets the eligibility criteria |
| eligibility_reasons | list(str) | Key reasons why eligible or ineligible |
| application_status | enum(NotApplied, Applied, UnderReview, Approved, Rejected) | Current application status |
| checked_at | date | When eligibility was last evaluated |
| applied_at | date | When the farmer applied (null if not applied) |
| notes | str | Any additional context or follow-up notes |
| created_at | datetime | Record creation timestamp |

---

### 23. CropAdvisoryRule
> A single deterministic rule in the decision engine — applied BEFORE the LLM to ensure physical accuracy.
> Rules are evaluated in priority order; the first matching rule wins.

| Attribute | Type | Description |
|---|---|---|
| rule_id | UUID | Primary key |
| rule_name | str | Human-readable name (e.g. "Skip Irrigation — High Moisture + Rain Expected") |
| intent_type | str | Which advisory flow this rule applies to (e.g. "irrigation_decision") |
| crop_id | UUID | FK → Crop (null = applies to all crops) |
| conditions | JSON | Structured condition tree (field, operator, value — supports AND/OR logic) |
| recommendation_code | str | Machine-readable outcome (e.g. "DO_NOT_IRRIGATE", "IRRIGATE_NOW", "WAIT_AND_MONITOR") |
| recommendation_text | str | Human-readable recommendation passed to LLM as deterministic anchor |
| priority | int | Evaluation order — lower number = higher priority |
| is_active | bool | Whether this rule is currently in use |
| created_at | datetime | Rule creation timestamp |

---

### 24. FarmerNotificationPreference
> Per-farmer settings controlling which notifications they receive and when.
> One-to-one with Farmer — created with defaults during onboarding.

| Attribute | Type | Description |
|---|---|---|
| preference_id | UUID | Primary key |
| farmer_id | UUID | FK → Farmer (unique) |
| receive_price_alerts | bool | Opt-in for mandi price movement alerts |
| receive_weather_alerts | bool | Opt-in for rain and weather warnings |
| receive_disaster_alerts | bool | Opt-in for disaster/emergency alerts (defaults to true — safety critical) |
| receive_pest_alerts | bool | Opt-in for pest and disease warnings |
| receive_seasonal_reminders | bool | Opt-in for sowing/harvest window reminders |
| receive_scheme_deadlines | bool | Opt-in for government scheme deadline reminders |
| receive_motivation_messages | bool | Opt-in for daily encouragement and best practice tips |
| preferred_send_time | str | Preferred time of day for non-urgent notifications (e.g. "07:00") |
| notification_language | enum(Hindi, Kannada, Telugu, Bengali) | Language for notifications (defaults to Farmer.language_preference) |
| updated_at | datetime | Last updated timestamp |

---

### 25. MarketPriceAlert
> A triggered alert when a crop's mandi price crosses a significant threshold for a farmer.
> Distinct from Notification — this is the event record that *generates* a price-related Notification.

| Attribute | Type | Description |
|---|---|---|
| price_alert_id | UUID | Primary key |
| farmer_crop_id | UUID | FK → FarmerCrop (which farmer's which crop) |
| mandi_id | UUID | FK → Mandi (which mandi triggered this) |
| trigger_type | enum(PriceHigh, PriceLow, PriceSpike, PriceDrop, NearMSP, AboveMSP) | What condition was triggered |
| triggered_price | float | The price that triggered the alert (per quintal) |
| reference_price | float | The baseline or threshold price being compared against |
| price_change_percent | float | Percentage change that triggered the alert |
| alert_message | str | Auto-generated message (e.g. "Tomato price at Hubli mandi rose 22% today") |
| notification_id | UUID | FK → Notification (the notification dispatched for this alert) |
| triggered_at | datetime | When the threshold was breached |
| created_at | datetime | Record creation timestamp |

---

## Entity Summary

| # | Entity | Nature | Purpose |
|---|---|---|---|
| 1 | Farmer | DB | Primary user — profile and identity |
| 2 | Crop | Static JSON | Crop reference data |
| 3 | FarmerCrop | DB | Active crop per farmer |
| 4 | Location | DB | Pincode → lat/lng anchor |
| 5 | AgroClimaticZone | Static JSON | Regional agricultural context |
| 6 | WeatherData | Redis (transient) | Real-time weather + forecast |
| 7 | SoilData | Redis (semi-static) | Soil characteristics per location |
| 8 | Mandi | Static JSON | Market location reference |
| 9 | MandiPrice | DB (daily) | Daily crop prices at mandis |
| 10 | GovernmentScheme | Static JSON | Scheme details and eligibility rules |
| 11 | ConversationSession | DB | Context-gathering state machine |
| 12 | ConversationTurn | DB (audit log) | Per-turn log (LiveKit manages real-time) |
| 13 | QueryContext | DB | Assembled LLM context snapshot |
| 14 | QueryResult | DB | LLM output + audit metadata |
| 15 | Notification | DB | Outbound proactive messages |
| 16 | FarmerFeedback | DB | Post-interaction ratings |
| 17 | Fertilizer | Static JSON | Fertilizer reference data |
| 18 | CropGrowthStage | Static JSON | Per-crop growth stage definitions |
| 19 | PestAlert | DB | Zone-level pest/disease warnings |
| 20 | MarketTrend | DB (derived) | 6-month price trend aggregations |
| 21 | DisasterAlert | DB | Natural disaster alerts (NDMA/IMD) |
| 22 | FarmerSchemeEligibility | DB | Farmer ↔ Scheme eligibility junction |
| 23 | CropAdvisoryRule | DB | Deterministic rules for decision engine |
| 24 | FarmerNotificationPreference | DB | Per-farmer notification settings |
| 25 | MarketPriceAlert | DB | Price threshold breach events |
| 26 | State | Static JSON | Normalised state reference table |
| 27 | CropVariety | Static JSON | Variety-level crop data (e.g. Basmati, IR36) |
| 28 | VarietyState | Static JSON | Junction: which varieties grow in which states |
| 29 | CropCalendarWindow | Static JSON | Seasonal sowing/harvest calendar per crop per zone |
| 30 | WeatherHourly | DB (transient) | Hourly weather readings for real-time alerts |
| 31 | WeatherCoverage | DB | Pincode-level weather data availability tracking |

---

## Batch 4 (Entities 26–31) — Integrated from Colleague's Schema (`VAANI Schema.erd`)

> Source: `crop.*` and `weather.*` PostgreSQL schemas.
> These entities add precision that our original design lacked — variety-level crop data, regional calendar windows, and split weather granularity.

---

### 26. State
> Normalised reference table for Indian states and union territories.
> Replaces raw `state: str` fields scattered across Farmer, Mandi, MandiPrice, GovernmentScheme, etc.
> **Static reference data** — rarely changes.

| Attribute | Type | Description |
|---|---|---|
| state_id | UUID | Primary key |
| state_name | str | Full name (e.g. "Karnataka") |
| state_code | str | 2-letter code (e.g. "KA") |
| region | enum(North, South, East, West, Central, Northeast) | Broad geographic region |
| primary_language | str | Dominant spoken language (e.g. "Kannada") |
| is_union_territory | bool | True for UTs (e.g. Puducherry, Lakshadweep) |

---

### 27. CropVariety
> A specific variety within a crop — carries its own water, growth, and yield profile.
> Critical for precision advice: Basmati and IR36 are both Paddy but behave very differently.
> From colleague's `crop.crop_varieties` table. **Static reference data**.

| Attribute | Type | Description |
|---|---|---|
| variety_id | UUID | Primary key |
| crop_id | UUID | FK → Crop |
| variety_name | str | Variety name (e.g. "Sona Masoori", "Basmati", "IR36") |
| local_names | dict(str→str) | Local names by language code |
| growth_duration_days | int | Variety-specific duration (overrides Crop default) |
| water_requirement_mm | float | Season-total water requirement for this variety |
| drought_tolerance | enum(Low, Medium, High) | How well this variety handles water stress |
| typical_yield_quintals_per_acre | float | Expected yield under normal conditions |
| is_msp_variety | bool | Whether this variety qualifies for MSP pricing |
| notes | str | Any special cultivation notes |

---

### 28. VarietyState
> Junction table: which crop varieties are grown in which states.
> From colleague's `crop.variety_states` table. Enables region-specific advice.
> **Static reference data**.

| Attribute | Type | Description |
|---|---|---|
| variety_state_id | UUID | Primary key |
| variety_id | UUID | FK → CropVariety |
| state_id | UUID | FK → State |
| is_widely_grown | bool | Whether this variety is dominant in the state |
| notes | str | Regional notes (e.g. "Preferred in coastal districts") |

---

### 29. CropCalendarWindow
> Defines the seasonal sowing and harvest calendar for a crop in a specific agro-climatic zone.
> From colleague's `crop.crop_calendar_windows` table.
> Distinct from `CropGrowthStage` — this is macro-level calendar (when to start), not within-season milestones.
> **Static reference data**.

| Attribute | Type | Description |
|---|---|---|
| window_id | UUID | Primary key |
| crop_id | UUID | FK → Crop |
| agro_zone_id | UUID | FK → AgroClimaticZone (zone-specific windows) |
| season | enum(Kharif, Rabi, Zaid) | Cropping season |
| sowing_start_month | int | Earliest recommended sowing month (1=Jan, 6=Jun) |
| sowing_end_month | int | Latest recommended sowing month |
| harvest_start_month | int | Earliest expected harvest month |
| harvest_end_month | int | Latest expected harvest month |
| notes | str | Advisory notes (e.g. "Delay if monsoon onset is late") |

---

### 30. WeatherHourly
> High-frequency hourly weather readings for real-time alerts and intra-day decisions.
> **DB table name: `weather.weather_hourly`** — directly from colleague's tested schema.
> FK is `pincode` (str), matching `pincode_location.pincode` (colleague's FK: `weather_hourly_pincode_fkey`).
> **Transient** — short TTL in Redis; not persisted long-term.

| Attribute | Type | Description |
|---|---|---|
| weather_hourly_id | UUID | Primary key |
| pincode | str | FK → pincode_location (colleague's tested FK: `weather_hourly_pincode_fkey`) |
| recorded_at | datetime | Exact hourly timestamp |
| temperature_celsius | float | Temperature at this hour |
| humidity_percent | float | Relative humidity |
| rainfall_mm | float | Rainfall in this hour |
| wind_speed_kmh | float | Wind speed |
| wind_direction | str | Wind direction (e.g. "NE") |
| soil_moisture_percent | float | Topsoil moisture at this hour |
| data_source | str | Source API |
| fetched_at | datetime | When this record was fetched |

---

### 31. WeatherCoverage
> Tracks which pincodes have actual weather data available and from which source.
> **DB table name: `weather.weather_coverage`** — directly from colleague's tested schema.
> FK is `pincode` (str), matching `pincode_location.pincode` (colleague's FK: `weather_coverage_pincode_fkey`).
> Used to gracefully fall back to nearest station when a pincode has no direct coverage.

| Attribute | Type | Description |
|---|---|---|
| coverage_id | UUID | Primary key |
| pincode | str | FK → pincode_location (colleague's tested FK: `weather_coverage_pincode_fkey`) |
| has_daily_data | bool | Whether daily weather data is available for this pincode |
| has_hourly_data | bool | Whether hourly data is available |
| nearest_station_name | str | Name of the nearest IMD/weather station |
| nearest_station_distance_km | float | Distance to nearest station in km |
| data_source | str | Primary data source (e.g. "IMD", "open-meteo") |
| last_verified_at | datetime | When coverage was last confirmed |