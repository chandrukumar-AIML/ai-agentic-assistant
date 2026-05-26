-- backend/auth/migrations/create_workspace_domains.sql
-- Per-workspace browser domain whitelist for the browser agent.
-- Allows workspace admins to allowlist additional domains beyond the
-- global ALWAYS_ALLOWED set in domain_whitelist.py.

CREATE TABLE IF NOT EXISTS workspace_domains (
    id              BIGSERIAL PRIMARY KEY,
    workspace_slug  VARCHAR(50)  NOT NULL,               -- FK to workspaces.slug
    domain          VARCHAR(255) NOT NULL,                -- e.g. "mycompany.com"
    added_by        VARCHAR(255),                         -- user email who added it
    note            VARCHAR(500),                         -- optional reason/comment
    is_active       BOOLEAN      NOT NULL DEFAULT true,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (workspace_slug, domain)
);

CREATE INDEX IF NOT EXISTS idx_workspace_domains_slug
    ON workspace_domains(workspace_slug)
    WHERE is_active = true;

-- Seed: default workspace gets no extra domains (relies on ALWAYS_ALLOWED)
-- Workspace admins can insert rows via API or directly into this table.
