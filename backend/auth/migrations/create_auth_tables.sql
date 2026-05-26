-- backend/auth/migrations/create_auth_tables.sql

-- Plan tiers
CREATE TYPE plan_tier AS ENUM ('free', 'pro', 'enterprise');
CREATE TYPE user_role AS ENUM ('viewer', 'user', 'admin');

-- Workspaces
CREATE TABLE IF NOT EXISTS workspaces (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(100) NOT NULL,
    slug            VARCHAR(50)  NOT NULL UNIQUE,   -- URL-safe identifier
    plan_tier       plan_tier    NOT NULL DEFAULT 'free',
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active       BOOLEAN DEFAULT true,
    -- Namespace config (auto-derived from slug)
    chroma_collection    VARCHAR(100) GENERATED ALWAYS AS ('ws_' || slug) STORED,
    mem0_namespace       VARCHAR(100) GENERATED ALWAYS AS ('ws_' || slug) STORED,
    neo4j_label          VARCHAR(100) GENERATED ALWAYS AS ('WS_' || upper(slug)) STORED,
    -- Usage tracking
    daily_query_count    INTEGER DEFAULT 0,
    daily_reset_at       TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    total_tokens_used    BIGINT  DEFAULT 0,
    monthly_cost_usd     FLOAT   DEFAULT 0.0
);

-- Users
CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255),                   -- NULL = OAuth-only user
    full_name       VARCHAR(100),
    workspace_id    UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    role            user_role NOT NULL DEFAULT 'user',
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen_at    TIMESTAMP WITH TIME ZONE,
    -- Rate limit state
    daily_query_count  INTEGER DEFAULT 0,
    daily_reset_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Audit log
CREATE TABLE IF NOT EXISTS audit_log (
    id                  BIGSERIAL PRIMARY KEY,
    user_id             UUID REFERENCES users(id),
    workspace_id        UUID REFERENCES workspaces(id),
    session_id          VARCHAR(100),
    trace_id            VARCHAR(100),
    timestamp           TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    action              VARCHAR(50)  NOT NULL,  -- 'query', 'ingest', 'delete_memory', 'admin_*'
    tool_called         VARCHAR(100),
    worker_agents       TEXT[],
    input_tokens        INTEGER DEFAULT 0,
    output_tokens       INTEGER DEFAULT 0,
    cost_usd            FLOAT   DEFAULT 0.0,
    latency_ms          INTEGER DEFAULT 0,
    guardrail_triggered BOOLEAN DEFAULT false,
    guardrail_type      VARCHAR(50),
    pii_detected        BOOLEAN DEFAULT false,
    reflection_loops    INTEGER DEFAULT 0,
    model_used          VARCHAR(50),
    error               TEXT,
    metadata            JSONB   DEFAULT '{}'
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_users_email      ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_workspace  ON users(workspace_id);
CREATE INDEX IF NOT EXISTS idx_audit_user       ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_workspace  ON audit_log(workspace_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp  ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_action     ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_workspaces_slug  ON workspaces(slug);

-- Default workspace + admin user (for dev)
INSERT INTO workspaces (name, slug, plan_tier)
VALUES ('Default Workspace', 'default', 'enterprise')
ON CONFLICT (slug) DO NOTHING;