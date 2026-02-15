# VAANI Design Document

## 1. System Overview

**VAANI** (Vaani) is a voice-first AI-powered decision support system designed to empower rural farmers with contextual, explainable, and actionable intelligence. Instead of delivering raw data, VAANI answers the key question farmers ask: "Mujhe ab kya karna chahiye?" (What should I do now?)

**Core Value**: Convert fragmented public data (weather, soil, market prices) into simple, explainable guidance delivered through natural voice interactions in local languages.

**Positioning**: VAANI is not just an AI tool — it is a digital farmer buddy.

## 2. Design Principles

- **Voice-First**: All interactions prioritize voice over text for low digital literacy users
- **Explainable AI**: Every recommendation includes clear reasoning farmers can understand
- **Deterministic Where Required**: Use rule-based logic before AI to ensure physical accuracy
- **Context-Aware**: Personalized advice based on user's crops, location, and farming practices
- **Low Bandwidth Friendly**: Optimized for rural connectivity constraints
- **Modular and Scalable**: Architecture supports future expansion
- **Responsible Advisory**: Always advisory, never authoritative

## 3. High-Level Architecture: Three Pillars

VAANI is built on three core pillars that work together to deliver comprehensive farmer support:

```
┌─────────────────────────────────────────────────────────────┐
│                    PILLAR 1: COMMUNICATION                  │
│  Phone (IVR) | WhatsApp Voice | WhatsApp Buttons | SMS     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              PILLAR 2: CORE DECISION ENGINE                 │
│                                                             │
│  Intent Classification → Context Manager → Data Integration │
│         ↓                                                   │
│  Deterministic Logic → AI Reasoning → Guardrails           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│            PILLAR 3: ENGAGEMENT & RETENTION                 │
│  Daily Notifications | WhatsApp CTAs | Motivation Messages │
└─────────────────────────────────────────────────────────────┘
```

## 4. Core Components

### Pillar 1: Communication Layer

**Objective**: Enable seamless, accessible, and vernacular interaction.

**Channels**:
- **Phone Calls**: IVR-based voice interaction for feature phones
- **WhatsApp Voice Notes**: Natural voice messaging for smartphone users
- **WhatsApp Interactive Buttons**: Action-oriented CTAs for quick access
- **SMS**: Fallback for notifications and alerts

**Key Features**:
- Speech-to-Text processing with agricultural vocabulary
- Text-to-Speech generation in Hindi and regional languages
- Minimal typing required
- Low bandwidth optimization
- Human-like conversational flow

**Design Decisions**:
- Prioritize voice over text to accommodate low literacy
- Support multiple channels to reach maximum farmers
- Use WhatsApp for engagement due to high rural penetration
- Implement IVR for users without smartphones

### Pillar 2: Core Decision Engine (6-Layer Architecture)

This is the brain of VAANI, structured as a 6-layer pipeline:

#### Layer 1: Intent Classification
**Purpose**: Identify farmer intent and route to appropriate decision logic.

**Supported Domains (MVP)**:
- Farming Decisions (irrigation, sowing, harvest timing)
- Market Intelligence (sell now/wait, crop selection)
- Government Schemes (eligibility, application)

**Capabilities**:
- Classifies queries into domain categories
- Extracts entities: crop type, location, timeframe
- Handles ambiguous queries with clarification
- Maintains conversation context

**Example**:
```
Input: "Aaj paani doon?"
Output: {
  domain: "farming",
  intent: "irrigation_decision",
  crop: "tomato"
}
```

#### Layer 2: Context Manager (Conversational Slot Filling)
**Purpose**: Gather complete context required for accurate decision-making.

**Approach**:
- Each intent has required context slots
- System asks one clarifying question at a time
- Uses user profile to pre-fill known information
- Validates context before proceeding

**Example for Irrigation Decision**:
Required context:
- Crop type
- Crop age
- Irrigation method
- Last irrigation date
- Location (from user profile)

**Benefits**:
- Ensures accuracy through complete information
- Builds trust through interactive engagement
- Creates natural conversation flow

#### Layer 3: Data Integration
**Purpose**: Fetch relevant data from multiple public sources.

**Data Sources**:
- **Weather & Soil**: Open-Meteo API (rain forecast, soil moisture)
- **Soil Characteristics**: SoilGrids API (soil texture, pH, nutrients)
- **Market Prices**: eNAM API and state mandi board datasets
- **Government Schemes**: Public scheme databases (state and central)

**Location Handling**:
- Convert pincode to latitude/longitude
- Use geographic coordinates for API queries
- Cache location data for performance

**Data Quality**:
- Validate data freshness and completeness
- Handle API failures with graceful fallbacks
- Maintain data quality thresholds

#### Layer 4: Deterministic Decision Logic
**Purpose**: Apply rule-based agricultural logic before AI reasoning to prevent hallucinations.

**Approach**:
- Use threshold-based rules for physical decisions
- Validate recommendations against agricultural best practices
- Ensure recommendations are physically feasible
- Provide clear, auditable decision paths

**Example: Irrigation Logic**
```
IF soil_moisture > threshold AND rain_expected:
  → Do not irrigate
  
IF soil_moisture < threshold AND no_rain_forecast:
  → Irrigate
  
IF soil_moisture moderate AND rain_uncertain:
  → Wait and monitor
```

**Benefits**:
- Prevents AI hallucinations on critical decisions
- Ensures physical accuracy
- Builds farmer trust through consistent logic

#### Layer 5: AI Reasoning & Explanation
**Purpose**: Generate clear, simple, conversational responses with reasoning.

**LLM Usage**:
- Structure advice in simple Hinglish
- Generate short responses (5-6 lines maximum)
- Provide clear reasoning
- Maintain conversational and friendly tone

**Response Structure**:
1. Clear recommendation (yes/no or specific action)
2. Two key reasons supporting the recommendation
3. Optional next step or follow-up suggestion

**Prompt Constraints**:
- Avoid technical jargon
- Use farmer-friendly language
- Keep responses concise
- Include reasoning for transparency

**Example Output**:
```
"Main suggest karunga ki aaj paani na den. Do karan hain:
1. Kal se barish ki sambhavna hai
2. Mitti mein nami kaafi hai

Agar 2 din baad barish nahi hui, to phir paani de sakte hain."
```

#### Layer 6: Guardrails & Safety
**Purpose**: Ensure responsible AI through safety filters.

**Safety Rules**:
- No guaranteed yield claims
- No exact chemical dosage recommendations
- No medical advice
- No political bias
- Always advisory, not authoritative

**Implementation**:
- Filter responses before delivery
- Add appropriate disclaimers
- Flag uncertain situations
- Maintain audit trail

### Pillar 3: Engagement & Retention Layer

**Objective**: Improve farmer retention and create daily value.

#### Daily Notifications
**Channels**: WhatsApp and SMS

**Notification Types**:
- Crop price movement alerts
- Rain warnings and weather alerts
- Seasonal reminders (sowing windows, harvest timing)
- Best practice tips
- Scheme application deadlines

**Design Approach**:
- Personalized based on user's crops and location
- Timely and actionable
- Respect user preferences
- Include relevant CTAs

#### WhatsApp Call-to-Action Buttons
**Purpose**: Enable quick access to common features.

**Button Options**:
- 📊 Check mandi prices
- 🌦 Weather forecast
- 🌱 Crop advice
- 🏛 Scheme eligibility

**Example Notification with CTA**:
```
"Kal barish ke chances zyada hain.
👉 Sinchai plan dekhne ke liye yahan click karein."

[Buttons: Weather | Crop Advice | Mandi Prices]
```

#### Motivation & Engagement Messaging
**Purpose**: Create sense of daily companionship.

**Message Types**:
- Seasonal encouragement
- Success stories
- Best practice reminders
- Timely farming tips

**Goal**: Make VAANI feel like a trusted farming buddy, not just a tool.

## 5. Decision Intelligence Flow

### Complete System Flow
```
Farmer Voice Query
        ↓
Communication Layer (Speech-to-Text)
        ↓
Intent Classification Layer
        ↓
Context Manager (Slot Filling)
        ↓
Data Integration (Weather/Soil/Market)
        ↓
Deterministic Decision Logic
        ↓
AI Reasoning & Explanation Generator
        ↓
Guardrail & Safety Filter
        ↓
Text-to-Speech Generation
        ↓
Voice Response via WhatsApp/Phone
```

### Example: Irrigation Decision Flow

**Step 1: Voice Input**
```
Farmer: "Kya main aaj tamatar ko paani doon?"
```

**Step 2: Intent Classification**
```
Domain: Farming
Intent: Irrigation Decision
Crop: Tomato
```

**Step 3: Context Gathering**
```
System: "Aapne last kab paani diya tha?"
Farmer: "3 din pehle"

Context Complete:
- Crop: Tomato
- Last irrigation: 3 days ago
- Location: [from profile]
- Crop age: [from profile]
```

**Step 4: Data Fetch**
```
- Soil moisture: 65% (from Open-Meteo)
- Rain forecast: 70% probability next 48 hours
- Temperature: 28°C
```

**Step 5: Deterministic Logic**
```
IF soil_moisture (65%) > threshold (60%) 
AND rain_probability (70%) > threshold (60%)
THEN recommendation = "Do not irrigate"
```

**Step 6: AI Explanation**
```
Generate simple Hinglish response with reasoning
```

**Step 7: Voice Output**
```
"Main suggest karunga ki aaj paani na den. Do karan hain:
1. Mitti mein pani kaafi hai (65%)
2. Kal se barish aane ki sambhavna hai

Agar 2 din baad barish nahi hui, to check kar sakte hain."
```

## 6. User Interaction & Explainability

### Response Structure Standard

Every VAANI response follows this pattern:
- **Direct Answer**: Clear yes/no or specific action
- **Key Reasoning**: 2 main supporting reasons
- **Risk Factors**: Potential issues to consider (when relevant)
- **Next Steps**: Follow-up action or monitoring suggestion

### Conversation Design Principles

- Use simple, conversational Hinglish
- Acknowledge uncertainty when present
- Encourage follow-up questions
- Maintain context across conversation
- Provide structured information with clear priorities
- Keep responses under 5-6 lines

### Example Interactions

**Fertilizer Guidance**:
```
Farmer: "Rice ke liye kaunsa khaad milega?"

System: "Aapki mitti clay type hai. Rice ke liye:
1. Urea (nitrogen ke liye)
2. DAP (phosphorus ke liye)
Best hai.

Paas ke agri store mein mil jayega. Exact quantity ke liye 
kisan mitra se baat karein."
```

**Crop Selection**:
```
Farmer: "Pichle 6 mahine ke mandi ke hisaab se kya ugaun?"

System: "Aapke area mein 3 options achhe hain:
1. Tomato - price stable, demand high
2. Onion - price badh raha hai
3. Green chilli - kam paani chahiye

Tomato sabse safe option hai. Risk kam hai."
```

## 7. Responsible AI & Limitations

### Ethical Guidelines

- **No Guarantees**: System provides guidance, not guaranteed outcomes
- **Transparency**: Always explain reasoning behind recommendations
- **User Agency**: Present options and let farmers make final decisions
- **Cultural Sensitivity**: Respect local farming practices and knowledge
- **Data Privacy**: Minimize personal data collection and storage

### System Limitations

- **Advisory Only**: Does not execute trades or guarantee results
- **Data Dependency**: Recommendation quality depends on external data availability
- **Regional Scope**: Initial focus on select crops and regions for MVP
- **Connectivity**: Requires basic internet for real-time data updates
- **Human Expertise**: Cannot replace agricultural extension officers for complex issues

### Risk Mitigation

- Provide confidence indication for all recommendations
- Include disclaimers about weather and market uncertainties
- Encourage users to validate advice with local experts
- Maintain fallback recommendations when data is unavailable
- Use deterministic logic for critical physical decisions

## 8. MVP Architecture Scope

### Phase 1 Features (Hackathon Demo)

**Crop Coverage**: 5 major crops (wheat, rice, cotton, tomato, sugarcane)

**Geographic Scope**: 2-3 states for demonstration (architecture designed for pan-India scale)

**Language Support**: Hindi with extensibility framework for regional languages

For the hackathon demo, Hindi is used as a common language, with architecture designed to support rapid addition of regional languages in future phases.

**Core Functionality**:
- Weather-based irrigation and sowing guidance
- Fertilizer selection guidance (general, not exact dosage)
- Crop selection based on 6-month mandi trends
- Basic government scheme awareness
- Voice interaction through WhatsApp and phone
- Daily notifications and engagement messaging
- WhatsApp interactive buttons

**Communication Channels**:
- WhatsApp voice notes
- WhatsApp interactive buttons
- Phone IVR (basic implementation)
- SMS notifications

### Success Metrics for Demo

- End-to-end voice interaction demonstration across all three pillars
- Clear reasoning and explainability for all recommendations
- Handling of 5+ realistic farmer scenarios
- Satisfactory user feedback during live demo
- Successful processing of voice queries in Hindi
- Demonstration of WhatsApp button interactions
- Examples of daily notifications and engagement

### Implementation Approach

**Core Technology**:
- Speech-to-Text and Text-to-Speech services (Sarvam AI / Gemini)
- WhatsApp Business API for messaging and buttons
- Telephony API for IVR implementation
- Web services for API handling and data processing
- Database for user profiles and conversation state
- Integration with public data sources (Open-Meteo, SoilGrids, eNAM)

**Key Design Choices**:
- Offline-first architecture with data caching for rural connectivity
- Lightweight components suitable for basic infrastructure
- Modular design allowing independent deployment of pillars
- Standards-based approach for broad compatibility

VAANI is designed to tolerate intermittent connectivity by caching recent data, while requiring basic internet access for live weather and market updates.

## 9. Scalability & Future Scope

### Phase 2 Enhancements
- Multi-language expansion to regional languages (Bengali, Tamil, Kannada, Telugu)
- Crop disease detection using image analysis
- Insurance advisory and claim support
- Credit awareness and financial literacy modules
- IoT sensor integration for real-time field data
- Community features for farmer knowledge sharing

### Long-Term Vision

Each farmer uses VAANI daily to:
- Plan irrigation schedules
- Time market selling for better prices
- Choose crops based on trends
- Access government schemes
- Reduce farming risks

VAANI becomes a trusted digital companion that supports:
- Resource-efficient agriculture
- Improved price realization
- Sustainable rural ecosystems
- Reduced guesswork in farming decisions

### Impact Vision

VAANI aims to:
- Reduce guesswork in farming decisions through data-driven guidance
- Improve price realization for farmers through market intelligence
- Increase awareness and access to government schemes
- Support resource-efficient and sustainable agriculture
- Promote thriving rural ecosystems

This design provides a comprehensive foundation for building VAANI as a practical, user-friendly agricultural decision support system that truly serves the needs of rural farmers in India.
