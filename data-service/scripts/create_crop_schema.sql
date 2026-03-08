CREATE SCHEMA IF NOT EXISTS crop;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 1) crop.crops
CREATE TABLE IF NOT EXISTS crop.crops (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    crop_name TEXT NOT NULL,
    crop_name_key TEXT NOT NULL UNIQUE,
    has_calendar BOOLEAN NOT NULL DEFAULT false,
    varieties_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_crops_crop_name_key ON crop.crops(crop_name_key);

-- 2) crop.crop_calendar_windows
CREATE TABLE IF NOT EXISTS crop.crop_calendar_windows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    crop_id UUID NOT NULL REFERENCES crop.crops(id) ON DELETE CASCADE,
    region TEXT,
    season TEXT,
    window_label_raw TEXT,
    source_document TEXT,
    sowing_months TEXT[] NOT NULL DEFAULT '{}',
    growth_months TEXT[] NOT NULL DEFAULT '{}',
    harvest_months TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_crop_calendar_windows_crop_id ON crop.crop_calendar_windows(crop_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_crop_calendar_windows ON crop.crop_calendar_windows(
    crop_id,
    COALESCE(region, ''),
    COALESCE(season, ''),
    COALESCE(window_label_raw, ''),
    sowing_months,
    growth_months,
    harvest_months
);

-- 3) crop.crop_varieties
CREATE TABLE IF NOT EXISTS crop.crop_varieties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    crop_id UUID NOT NULL REFERENCES crop.crops(id) ON DELETE CASCADE,
    variety_type TEXT NOT NULL,
    name TEXT NOT NULL,
    source TEXT,
    year INT,
    yield_min_q_per_ha NUMERIC,
    yield_max_q_per_ha NUMERIC,
    seed_rate_min_g_per_ha NUMERIC,
    seed_rate_max_g_per_ha NUMERIC,
    sowing_time_raw TEXT,
    sowing_time_tags TEXT[] NOT NULL DEFAULT '{}',
    states_raw TEXT,
    resistance_or_tolerance_lines TEXT[] NOT NULL DEFAULT '{}',
    other_lines TEXT[] NOT NULL DEFAULT '{}',
    raw_text TEXT,
    page INT,
    extras JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_crop_varieties_crop_id ON crop.crop_varieties(crop_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_crop_varieties ON crop.crop_varieties(
    crop_id,
    variety_type,
    name,
    COALESCE(source, ''),
    COALESCE(year, 0)
);

-- 4) crop.states
CREATE TABLE IF NOT EXISTS crop.states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    state_name TEXT NOT NULL UNIQUE,
    state_code TEXT,
    aliases TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Pre-seed main Indian states & UTs + requested aliases
INSERT INTO crop.states (state_name, aliases) VALUES
    ('Andaman and Nicobar Islands', '{}'),
    ('Andhra Pradesh', '{"AP", "A.P."}'),
    ('Arunachal Pradesh', '{}'),
    ('Assam', '{}'),
    ('Bihar', '{}'),
    ('Chandigarh', '{}'),
    ('Chhattisgarh', '{"Chattisgarh", "Chhatisgarh"}'),
    ('Dadra and Nagar Haveli and Daman and Diu', '{"Daman & Diu", "Dadra & Nagar Haveli"}'),
    ('Delhi', '{"New Delhi", "NCT of Delhi"}'),
    ('Goa', '{}'),
    ('Gujarat', '{}'),
    ('Haryana', '{}'),
    ('Himachal Pradesh', '{"HP", "H.P."}'),
    ('Jammu and Kashmir', '{"J&K", "J K", "JK", "Jammu & Kashmir"}'),
    ('Jharkhand', '{}'),
    ('Karnataka', '{}'),
    ('Kerala', '{}'),
    ('Ladakh', '{}'),
    ('Lakshadweep', '{}'),
    ('Madhya Pradesh', '{"MP", "M.P."}'),
    ('Maharashtra', '{"Maharastra"}'),
    ('Manipur', '{}'),
    ('Meghalaya', '{}'),
    ('Mizoram', '{}'),
    ('Nagaland', '{}'),
    ('Odisha', '{"Orissa"}'),
    ('Puducherry', '{"Pondicherry"}'),
    ('Punjab', '{}'),
    ('Rajasthan', '{"Raj", "Raj."}'),
    ('Sikkim', '{}'),
    ('Tamil Nadu', '{"TN", "T.N."}'),
    ('Telangana', '{"TS", "T.S."}'),
    ('Tripura', '{}'),
    ('Uttar Pradesh', '{"UP", "U.P."}'),
    ('Uttarakhand', '{"Uttaranchal"}'),
    ('West Bengal', '{"WB", "W.B."}')
ON CONFLICT (state_name) DO NOTHING;

-- 5) crop.variety_states
CREATE TABLE IF NOT EXISTS crop.variety_states (
    variety_id UUID NOT NULL REFERENCES crop.crop_varieties(id) ON DELETE CASCADE,
    state_id UUID NOT NULL REFERENCES crop.states(id) ON DELETE CASCADE,
    source TEXT NOT NULL DEFAULT 'parsed',
    PRIMARY KEY (variety_id, state_id)
);

CREATE INDEX IF NOT EXISTS idx_variety_states_variety_id ON crop.variety_states(variety_id);
CREATE INDEX IF NOT EXISTS idx_variety_states_state_id ON crop.variety_states(state_id);
