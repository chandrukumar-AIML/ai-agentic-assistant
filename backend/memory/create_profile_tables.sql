-- backend/memory/create_profile_tables.sql
-- Long-term user profile storage

CREATE TABLE IF NOT EXISTS user_profiles (
    user_id      TEXT        PRIMARY KEY,
    profile_data JSONB       NOT NULL DEFAULT '{}',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- GIN index for fast JSONB field queries
CREATE INDEX IF NOT EXISTS idx_user_profiles_data
    ON user_profiles USING GIN (profile_data);

CREATE INDEX IF NOT EXISTS idx_user_profiles_updated
    ON user_profiles (updated_at DESC);

-- Auto-update timestamp
CREATE OR REPLACE FUNCTION user_profiles_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$;

DROP TRIGGER IF EXISTS user_profiles_ts ON user_profiles;
CREATE TRIGGER user_profiles_ts
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION user_profiles_updated_at();
