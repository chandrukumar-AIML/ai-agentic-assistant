-- backend/prompts/migrations/create_prompt_tables.sql

-- Prompt versions table: every prompt has a full history
CREATE TABLE IF NOT EXISTS prompt_versions (
    id              SERIAL PRIMARY KEY,
    prompt_name     VARCHAR(100) NOT NULL,
    version         VARCHAR(20)  NOT NULL,   -- e.g. "1.0.0", "1.1.0"
    content         TEXT         NOT NULL,
    description     VARCHAR(500),
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by      VARCHAR(100) DEFAULT 'system',
    is_active       BOOLEAN      DEFAULT false,
    performance_score FLOAT      DEFAULT 0.0,
    query_count     INTEGER      DEFAULT 0,
    thumbs_up       INTEGER      DEFAULT 0,
    thumbs_down     INTEGER      DEFAULT 0,
    UNIQUE (prompt_name, version)
);

-- A/B test table: tracks active experiments
CREATE TABLE IF NOT EXISTS ab_tests (
    id              SERIAL PRIMARY KEY,
    test_name       VARCHAR(100) NOT NULL UNIQUE,
    prompt_name     VARCHAR(100) NOT NULL,
    variant_a_id    INTEGER      REFERENCES prompt_versions(id),
    variant_b_id    INTEGER      REFERENCES prompt_versions(id),
    traffic_split   FLOAT        DEFAULT 0.5,   -- 0.5 = 50/50
    status          VARCHAR(20)  DEFAULT 'running',  -- running|completed|paused
    winner_id       INTEGER      REFERENCES prompt_versions(id),
    min_queries     INTEGER      DEFAULT 100,    -- queries before auto-promote
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at    TIMESTAMP WITH TIME ZONE,
    auto_promote    BOOLEAN      DEFAULT true
);

-- Query log for A/B tracking: which variant served which query
CREATE TABLE IF NOT EXISTS ab_query_log (
    id              SERIAL PRIMARY KEY,
    test_id         INTEGER      REFERENCES ab_tests(id),
    variant_id      INTEGER      REFERENCES prompt_versions(id),
    session_id      VARCHAR(100),
    user_id         VARCHAR(100),
    trace_id        VARCHAR(100),
    feedback_score  FLOAT,       -- NULL until user gives feedback
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_prompt_versions_name    ON prompt_versions(prompt_name);
CREATE INDEX IF NOT EXISTS idx_prompt_versions_active  ON prompt_versions(prompt_name, is_active);
CREATE INDEX IF NOT EXISTS idx_ab_tests_status         ON ab_tests(status);
CREATE INDEX IF NOT EXISTS idx_ab_query_log_test       ON ab_query_log(test_id);
CREATE INDEX IF NOT EXISTS idx_ab_query_log_variant    ON ab_query_log(variant_id);