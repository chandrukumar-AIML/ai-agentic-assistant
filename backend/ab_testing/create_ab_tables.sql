-- backend/ab_testing/create_ab_tables.sql
-- Model-level A/B experiment tracking (Feature 12)

CREATE TABLE IF NOT EXISTS model_experiments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    description     TEXT DEFAULT '',
    model_a         TEXT NOT NULL,          -- e.g. "gpt-4o"
    model_b         TEXT NOT NULL,          -- e.g. "gpt-4o-mini" or "llama3"
    system_prompt   TEXT DEFAULT '',
    status          TEXT NOT NULL DEFAULT 'running'
                        CHECK (status IN ('running', 'paused', 'completed')),
    traffic_split   NUMERIC(4,3) NOT NULL DEFAULT 0.5,  -- fraction sent to model A
    min_turns       INT NOT NULL DEFAULT 50,
    auto_promote    BOOLEAN NOT NULL DEFAULT TRUE,
    winner_model    TEXT,
    significance_p  NUMERIC(10,6),          -- p-value when completed
    effect_size     NUMERIC(10,6),          -- Cohen's d
    promoted_at     TIMESTAMPTZ,
    created_by      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS model_experiment_turns (
    id              BIGSERIAL PRIMARY KEY,
    experiment_id   UUID NOT NULL REFERENCES model_experiments(id) ON DELETE CASCADE,
    variant         CHAR(1) NOT NULL CHECK (variant IN ('A', 'B')),
    model           TEXT NOT NULL,
    query           TEXT NOT NULL,
    response        TEXT NOT NULL,
    latency_ms      INT NOT NULL DEFAULT 0,
    prompt_tokens   INT NOT NULL DEFAULT 0,
    completion_tokens INT NOT NULL DEFAULT 0,
    cost_usd        NUMERIC(12,6) NOT NULL DEFAULT 0,
    quality_score   NUMERIC(5,4),           -- NULL until feedback given
    thumbs_up       BOOLEAN,                -- quick human signal
    session_id      TEXT DEFAULT '',
    user_id         TEXT DEFAULT '',
    trace_id        TEXT DEFAULT '',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Fast lookup for significance computation (variant filter + quality_score IS NOT NULL filter)
CREATE INDEX IF NOT EXISTS idx_met_experiment_variant
    ON model_experiment_turns (experiment_id, variant);

-- Partial index: only rated turns (used by compute_significance and auto-promote check)
CREATE INDEX IF NOT EXISTS idx_met_rated_turns
    ON model_experiment_turns (experiment_id, variant, quality_score)
    WHERE quality_score IS NOT NULL;

-- Fast count for auto-promote threshold check
CREATE INDEX IF NOT EXISTS idx_met_experiment_created
    ON model_experiment_turns (experiment_id, created_at DESC);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_me_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$;

DROP TRIGGER IF EXISTS trg_me_updated_at ON model_experiments;
CREATE TRIGGER trg_me_updated_at
    BEFORE UPDATE ON model_experiments
    FOR EACH ROW EXECUTE FUNCTION update_me_updated_at();
