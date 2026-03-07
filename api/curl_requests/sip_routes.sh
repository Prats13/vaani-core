#!/bin/bash
# Vaani SIP Routes - cURL Requests
# Base URL: http://localhost:8000

BASE_URL="http://localhost:8010/api/v1"
API_KEY="your-api-key-here"

# ------------------------------------------------------------
# GET /sip/health
# ------------------------------------------------------------
curl -X GET "{{BASE_URL}}/sip/health" \
  -H "Content-Type: application/json"


# ------------------------------------------------------------
# POST /sip/call/outbound  (minimal — no agent_params)
# ------------------------------------------------------------
curl -X POST "{{BASE_URL}}/sip/call/outbound" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: {{API_KEY}}" \
  -d '{
    "agent_config": {
      "agent_type": "farmer_advisory",
      "stt_config": "sarvam-saarika-2.5",
      "llm_config": "gemini-2.5-flash",
      "tts_config": "sarvam-bulbul"
    },
    "call_config": {
      "call_from": "+918035001234",
      "call_to": "+919876543210"
    }
  }'


# ------------------------------------------------------------
# POST /sip/call/outbound  (with full agent_params)
# ------------------------------------------------------------
curl -X POST "{{BASE_URL}}/sip/call/outbound" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: " \
  -d '{
    "agent_config": {
      "agent_type": "farmer_advisory",
      "stt_config": "sarvam-saarika-2.5",
      "llm_config": "gemini-2.5-flash",
      "tts_config": "sarvam-bulbul"
    },
    "call_config": {
      "call_direction": "outbound",
      "call_type": "pstn",
      "call_provider": "exotel",
      "call_from": "+918035001234",
      "call_to": "+919876543210"
    },
    "agent_params": {
      "farmer_name": "Raju",
      "farmer_phone": "+919876543210",
      "query_context": "Cotton crop pest advisory"
    }
  }'


# ------------------------------------------------------------
# POST /sip/call/outbound  (onboarding agent)
# ------------------------------------------------------------
curl -X POST "{{BASE_URL}}/sip/call/outbound" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: {{API_KEY}}" \
  -d '{
    "agent_config": {
      "agent_type": "farmer_onboarding",
      "stt_config": "sarvam-saarika-2.5",
      "llm_config": "gemini-2.5-flash",
      "tts_config": "sarvam-bulbul"
    },
    "call_config": {
      "call_direction": "outbound",
      "call_type": "pstn",
      "call_provider": "exotel",
      "call_from": "+918035001234",
      "call_to": "+919876543210"
    },
    "agent_params": {
      "farmer_name": "Meena",
      "farmer_phone": "+919876543210"
    }
  }'