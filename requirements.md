# VAANI Requirements Document

## Project Overview

**Project Name**: VAANI (Vaani)

**Vision**: A voice-first AI-powered decision support system that empowers rural farmers with contextual, explainable, and actionable intelligence delivered through natural voice interactions.

**Core Value Proposition**: Instead of providing raw data or generic advisories, VAANI focuses on decision intelligence — answering the question rural users actually ask: "Mujhe ab kya karna chahiye?" (What should I do now?)

**Positioning**: VAANI is not just an AI tool — it is a digital farmer buddy.

## Problem Statement

Rural farmers face multiple structural challenges:
- Fragmented access to agricultural and market information
- Difficulty interpreting weather and mandi data
- Over-reliance on intermediaries for decisions
- Low digital literacy limiting technology adoption
- Poor connectivity constraining real-time access
- Market price volatility affecting income
- Limited awareness of government schemes and benefits

Existing systems provide information, but not contextual decision support. VAANI bridges this gap by converting data into actionable guidance.

## Target Users

### Primary Users
- **Small-scale farmers** (1-5 acres) growing staple crops
- **Rural households** making agricultural livelihood decisions
- **Agricultural workers** needing timely guidance

### User Characteristics
- Limited digital literacy
- Low-bandwidth connectivity
- Prefer voice communication over text
- Speak local/regional languages
- Need simple, actionable guidance with clear reasoning

## Functional Requirements

### 1. Communication Layer (Pillar 1)

#### 1.1 Voice Interaction System
**User Story**: As a farmer, I want to speak my questions in my local language through multiple channels, so I can get help without typing or reading.

**Acceptance Criteria**:
- System accepts voice input through phone calls (IVR-based)
- System supports WhatsApp voice notes
- System processes Hindi and major regional languages
- System handles background noise and varying audio quality
- System provides voice responses in user's preferred language
- System maintains conversational flow for follow-up questions

#### 1.2 WhatsApp Interactive Interface
**User Story**: As a farmer, I want to interact with VAANI through WhatsApp buttons, so I can quickly access common features.

**Acceptance Criteria**:
- System provides action-oriented call-to-action buttons
- System supports quick access to: mandi prices, weather forecast, crop advice, scheme eligibility
- System enables minimal typing interaction
- System works on low bandwidth connections
- System provides human-like conversational flow

### 2. Core Decision Engine (Pillar 2)

#### 2.1 Intent Classification
**User Story**: As a system, I need to identify farmer intent and domain, so I can route queries to appropriate decision logic.

**Acceptance Criteria**:
- System classifies queries into domains: farming decisions, market intelligence, government schemes
- System extracts key entities: crop type, location, timeframe
- System handles ambiguous queries with clarifying questions
- System maintains context across conversation turns

#### 2.2 Context Management (Conversational Slot Filling)
**User Story**: As a system, I need to gather complete context for each decision, so I can provide accurate recommendations.

**Acceptance Criteria**:
- System identifies required context for each intent type
- System asks one clarifying question at a time when information is missing
- System maintains conversation state across multiple turns
- System uses user profile data to pre-fill known information
- System validates gathered context before proceeding

#### 2.3 Data Integration
**User Story**: As a system, I need to access reliable weather, soil, and market data, so I can provide data-driven recommendations.

**Acceptance Criteria**:
- System integrates with Open-Meteo API for weather and soil moisture
- System integrates with SoilGrids API for soil characteristics
- System integrates with eNAM and state mandi board APIs for market prices
- System converts pincode to latitude/longitude for location-based data
- System handles data unavailability gracefully with fallback options
- System validates data quality and freshness

#### 2.4 Deterministic Decision Logic
**User Story**: As a system, I need to apply rule-based agricultural logic before AI reasoning, so I can prevent hallucinations and ensure physical accuracy.

**Acceptance Criteria**:
- System applies deterministic rules for irrigation decisions based on soil moisture and rain forecast
- System uses threshold-based logic for fertilizer recommendations
- System validates recommendations against agricultural best practices
- System ensures recommendations are physically feasible
- System provides clear decision paths that can be audited

#### 2.5 AI Reasoning and Explanation
**User Story**: As a farmer, I want to receive clear, simple explanations for recommendations, so I can understand and trust the advice.

**Acceptance Criteria**:
- System generates responses in simple Hinglish (Hindi-English mix)
- System keeps answers under 5-6 lines
- System avoids technical jargon
- System provides: (1) clear recommendation, (2) 2 key reasons, (3) optional next step
- System maintains conversational and friendly tone
- System structures advice for easy comprehension

#### 2.6 Guardrails and Safety
**User Story**: As a responsible AI system, I must ensure all advice is safe and appropriate, so farmers are not misled or harmed.

**Acceptance Criteria**:
- System never makes guaranteed yield claims
- System avoids exact chemical dosage recommendations
- System does not provide medical advice
- System maintains political neutrality
- System clearly indicates advisory nature (not authoritative)
- System includes appropriate disclaimers for uncertain situations

### 3. Engagement and Retention Layer (Pillar 3)

#### 3.1 Daily Notifications
**User Story**: As a farmer, I want to receive timely alerts about important agricultural events, so I can take proactive actions.

**Acceptance Criteria**:
- System sends daily notifications via WhatsApp and SMS
- System provides crop price movement alerts
- System sends rain warnings and weather alerts
- System delivers seasonal reminders (sowing windows, harvest timing)
- System personalizes notifications based on user's crops and location
- System respects user notification preferences

#### 3.2 WhatsApp Call-to-Action Buttons
**User Story**: As a farmer, I want quick access to common features through buttons, so I can easily navigate the system.

**Acceptance Criteria**:
- System provides interactive buttons for: Check mandi prices, Weather forecast, Crop advice, Scheme eligibility
- System includes contextual CTAs in notifications
- System enables one-tap access to relevant features
- System maintains button functionality on low-end devices

#### 3.3 Motivation and Engagement Messaging
**User Story**: As a farmer, I want to feel supported and encouraged in my farming journey, so I stay engaged with the system.

**Acceptance Criteria**:
- System sends seasonal encouragement messages
- System provides best practice reminders
- System delivers timely farming tips
- System creates a sense of daily companionship
- System maintains positive and supportive tone

### 4. Core Use Cases

#### 4.1 Irrigation Decision Support
**User Story**: As a farmer, I want to know when to irrigate my crops based on current conditions, so I can optimize water usage and crop health.

**Acceptance Criteria**:
- System gathers crop type, crop age, irrigation method, last irrigation date
- System fetches soil moisture and rain forecast data
- System applies deterministic irrigation logic
- System provides clear yes/no recommendation with reasoning
- System considers water availability and crop stage

#### 4.2 Fertilizer Guidance
**User Story**: As a farmer, I want guidance on fertilizer selection for my crops, so I can improve soil health and yield.

**Acceptance Criteria**:
- System identifies soil type from location data
- System considers crop type and growth stage
- System provides general fertilizer category guidance (not exact dosage)
- System suggests nearby agricultural stores
- System includes safety disclaimers

#### 4.3 Crop Selection Based on Market Trends
**User Story**: As a farmer, I want to choose crops based on recent market trends, so I can maximize my income potential.

**Acceptance Criteria**:
- System analyzes 6-month price trends from mandi data
- System filters crop options by climate, water availability, and soil type
- System suggests 2-3 viable crop options
- System mentions associated risks and considerations
- System provides reasoning for each suggestion

#### 4.4 Government Scheme Awareness
**User Story**: As a farmer, I want to know which government schemes I'm eligible for, so I can access available benefits.

**Acceptance Criteria**:
- System maintains database of central and state-level schemes
- System checks eligibility based on user profile
- System provides scheme details in simple language
- System explains application process
- System provides contact information for scheme offices

## Non-Functional Requirements

### 5. Performance Requirements

#### 5.1 Response Time
- Voice recognition processing within 2 seconds
- Decision generation within 3 seconds
- End-to-end response within 5 seconds total
- Data retrieval within 3 seconds for fresh data

#### 5.2 Scalability
- Support 1,000 concurrent voice interactions initially
- Architecture allows scaling to 10,000+ users
- Handle 100,000+ queries per day
- Maintain performance during peak hours (6 AM - 8 PM)

### 6. Usability Requirements

#### 6.1 Voice Interface Usability
- Voice recognition accuracy > 85% for supported languages
- Response clarity rated > 4/5 by users
- Task completion rate > 80% for primary use cases
- Minimal user frustration with clarifying questions

#### 6.2 Accessibility
- Works on basic feature phones via IVR
- Functions with 2G connectivity
- Supports users with limited digital literacy
- Provides audio-only interaction option

### 7. Technical Requirements

#### 7.1 Platform Compatibility
- Phone-based access via IVR system
- WhatsApp integration for voice notes and buttons
- SMS fallback for notifications
- Web-based admin interface for monitoring

#### 7.2 Data Requirements
- Real-time weather data with hourly updates
- Daily mandi price updates
- Soil data from geographic databases
- Government scheme database with regular updates
- User interaction logs for system improvement

## MVP Scope (Hackathon Focus)

### Phase 1 Features
1. **Limited Crop Support**: Focus on 5 major crops (wheat, rice, cotton, tomato, sugarcane)
2. **Regional Focus**: Target 2-3 states initially (demonstration purposes)
3. **Language Support**: Hindi with extensibility framework for regional languages
4. **Core Use Cases**: Irrigation decisions, fertilizer guidance, crop selection, basic scheme awareness
5. **Communication Channels**: WhatsApp voice notes and interactive buttons, phone IVR
6. **Engagement**: Daily notifications and motivational messaging

### Success Metrics for MVP (Demo Outcomes)

- Demonstrates end-to-end voice interaction across all three pillars
- Shows clear reasoning and explainability for all recommendations
- Handles at least 5 realistic farmer scenarios successfully
- Achieves satisfactory user feedback during live demo
- Successfully processes voice queries in Hindi
- Demonstrates WhatsApp button interactions
- Shows daily notification examples

## Future Expansion Opportunities

### Phase 2 Enhancements
- Multi-language expansion to regional languages
- Crop disease detection using image analysis
- Insurance advisory and claim support
- Credit awareness and financial literacy
- IoT sensor integration for real-time field data
- Community features for farmer knowledge sharing

### Long-term Vision
- Each farmer uses VAANI daily to plan irrigation, time market selling, choose crops, access schemes, and reduce risk
- VAANI becomes a trusted digital companion for rural agricultural decisions
- Integration with agricultural supply chain platforms
- Expansion to other rural livelihood decisions beyond agriculture

## Constraints and Assumptions

### Technical Constraints
- Limited internet bandwidth in rural areas
- Varying smartphone penetration
- Dependency on external data APIs
- Need for multilingual support

### Business Constraints
- Public data availability and reliability
- Need to remain neutral and non-commercial
- Cost sensitivity of rural users
- Compliance with responsible AI and advisory guidelines

### Assumptions
- Users have access to basic phones or smartphones
- Internet connectivity available intermittently
- Users willing to adopt voice-based technology
- Public data APIs remain accessible and reliable

## Why AI is Required

VAANI cannot be built using static rules alone because farming and market decisions depend on uncertain, interacting variables such as weather forecasts, price volatility, crop stage, soil conditions, and user intent expressed in natural language. AI enables:
- Contextual reasoning across multiple data sources
- Natural language understanding for conversational interaction
- Probabilistic decision-making under uncertainty
- Explainable synthesis of complex agricultural knowledge
- Personalization based on user context and history

## Non-Goals (Out of Scope for MVP)

- Does not execute trades or sell produce
- Does not guarantee yield or price outcomes
- Does not replace human agricultural experts
- Does not provide exact chemical dosage or medical advice
- Does not handle financial transactions
- Does not provide legal advice on land or contracts

## Design Principles

- **Voice-first**: All interactions prioritize voice over text
- **Explainable AI**: Every recommendation includes clear reasoning
- **Deterministic where required**: Use rule-based logic for physical accuracy
- **Context-aware**: Personalized advice based on user situation
- **Low bandwidth friendly**: Optimized for rural connectivity
- **Modular and scalable**: Architecture supports future expansion
- **Responsible advisory**: Always advisory, never authoritative
