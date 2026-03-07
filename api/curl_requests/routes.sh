#!/bin/bash
# Vaani API Routes - cURL Requests
# Base URL: http://localhost:8000

BASE_URL="http://localhost:8010/api/v1"
API_KEY="vaani_ai_for_bharat_2026"

# ------------------------------------------------------------
# GET /whatsapp/health
# ------------------------------------------------------------
curl -X GET "$BASE_URL/whatsapp/health" \
  -H "Content-Type: application/json"


# ------------------------------------------------------------
# POST /whatsapp/start_session  (minimal — no config override)
# ------------------------------------------------------------
curl -X POST "$BASE_URL/whatsapp/start_session" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "user_id": "farmer_123"
  }'


# ------------------------------------------------------------
# POST /whatsapp/start_session  (with full config override)
# ------------------------------------------------------------
curl -X POST "$BASE_URL/whatsapp/start_session" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "user_id": "farmer_123",
    "config": {
      "agent_type": "farmer_advisory",
      "llm_config": "gemini-2.5-flash",
      "stt_config": "sarvam-saarika-2.5",
      "tts_config": "sarvam-bulbul"
    }
  }'