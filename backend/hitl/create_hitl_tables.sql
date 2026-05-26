-- backend/hitl/create_hitl_tables.sql
-- Human-in-the-Loop approval queue

CREATE TABLE IF NOT EXISTS hitl_approvals (
    id              BIGSERIAL PRIMARY KEY,
    approval_id     UUID        NOT NULL UNIQUE DEFAULT gen_random_uuid(),

    -- Who requested it
    user_id         TEXT        NOT NULL,
    session_id      TEXT        NOT NULL,
    workspace_id    TEXT        NOT NULL DEFAULT '00000000-0000-0000-0000-000000000001',

    -- What needs approval
    action_type     TEXT        NOT NULL,   -- e.g. "email_send","payment","calendar_book"
    action_payload  JSONB       NOT NULL DEFAULT '{}',
    context_summary TEXT        NOT NULL DEFAULT '',

    -- Status
    status          TEXT        NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending','approved','rejected','expired','escalated')),

    -- Decision
    reviewer_id     TEXT,
    reviewer_note   TEXT,
    decided_at      TIMESTAMPTZ,

    -- Timing
    expires_at      TIMESTAMPTZ NOT NULL,   -- 30 minutes from creation
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- LangGraph resume info
    thread_id       TEXT,       -- LangGraph checkpoint thread id
    checkpoint_id   TEXT        -- to resume graph execution
);

CREATE INDEX IF NOT EXISTS idx_hitl_status     ON hitl_approvals (status);
CREATE INDEX IF NOT EXISTS idx_hitl_user       ON hitl_approvals (user_id);
CREATE INDEX IF NOT EXISTS idx_hitl_session    ON hitl_approvals (session_id);
CREATE INDEX IF NOT EXISTS idx_hitl_expires    ON hitl_approvals (expires_at) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_hitl_approval   ON hitl_approvals (approval_id);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION hitl_update_timestamp()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS hitl_approvals_updated ON hitl_approvals;
CREATE TRIGGER hitl_approvals_updated
    BEFORE UPDATE ON hitl_approvals
    FOR EACH ROW EXECUTE FUNCTION hitl_update_timestamp();

-- Notification log for delivery tracking
CREATE TABLE IF NOT EXISTS hitl_notifications (
    id              BIGSERIAL   PRIMARY KEY,
    approval_id     UUID        NOT NULL REFERENCES hitl_approvals(approval_id) ON DELETE CASCADE,
    channel         TEXT        NOT NULL,   -- email | slack | in_app | webhook
    recipient       TEXT        NOT NULL,
    status          TEXT        NOT NULL DEFAULT 'sent'
                    CHECK (status IN ('sent','failed','delivered')),
    sent_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata        JSONB       NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_hitl_notif_approval ON hitl_notifications (approval_id);
