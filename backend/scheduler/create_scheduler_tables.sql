-- backend/scheduler/create_scheduler_tables.sql
-- Agentic Task Scheduler (Feature 4)

DO $$ BEGIN
    CREATE TYPE task_schedule_type AS ENUM ('once', 'interval', 'cron', 'event');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE task_status_type AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled', 'paused');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS scheduled_tasks (
    id              BIGSERIAL       PRIMARY KEY,
    task_id         UUID            NOT NULL UNIQUE DEFAULT gen_random_uuid(),

    -- Owner
    user_id         TEXT            NOT NULL,
    workspace_id    TEXT            NOT NULL DEFAULT '00000000-0000-0000-0000-000000000001',

    -- Task definition
    name            TEXT            NOT NULL,
    description     TEXT            NOT NULL DEFAULT '',
    agent_node      TEXT            NOT NULL,        -- LangGraph node to invoke
    agent_payload   JSONB           NOT NULL DEFAULT '{}',

    -- Schedule
    schedule_type   TEXT            NOT NULL DEFAULT 'once'
                    CHECK (schedule_type IN ('once','interval','cron','event')),
    schedule_value  TEXT            NOT NULL,        -- ISO datetime | "5m" | cron expr | event name
    timezone        TEXT            NOT NULL DEFAULT 'UTC',

    -- Execution state
    status          TEXT            NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending','running','completed','failed','cancelled','paused')),
    run_count       INT             NOT NULL DEFAULT 0,
    max_runs        INT,                             -- NULL = unlimited
    last_run_at     TIMESTAMPTZ,
    next_run_at     TIMESTAMPTZ,
    last_error      TEXT,

    -- Notifications
    notify_email    TEXT,
    notify_slack    BOOLEAN         NOT NULL DEFAULT FALSE,

    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sched_user      ON scheduled_tasks (user_id);
CREATE INDEX IF NOT EXISTS idx_sched_workspace  ON scheduled_tasks (workspace_id);
CREATE INDEX IF NOT EXISTS idx_sched_status     ON scheduled_tasks (status);
CREATE INDEX IF NOT EXISTS idx_sched_next_run   ON scheduled_tasks (next_run_at) WHERE status = 'pending';

-- Execution run log
CREATE TABLE IF NOT EXISTS task_runs (
    id          BIGSERIAL   PRIMARY KEY,
    task_id     UUID        NOT NULL REFERENCES scheduled_tasks(task_id) ON DELETE CASCADE,
    run_id      UUID        NOT NULL DEFAULT gen_random_uuid(),
    status      TEXT        NOT NULL CHECK (status IN ('running','completed','failed')),
    started_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    output      JSONB       NOT NULL DEFAULT '{}',
    error       TEXT,
    latency_ms  FLOAT
);

CREATE INDEX IF NOT EXISTS idx_task_runs_task ON task_runs (task_id);
CREATE INDEX IF NOT EXISTS idx_task_runs_run  ON task_runs (run_id);
